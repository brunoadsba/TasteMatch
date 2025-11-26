"""
Endpoints da API para sistema de recomendações personalizadas.
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
from datetime import datetime
from pydantic import BaseModel
import json
import time

from app.database.base import get_db
from app.api.deps import get_current_user
from app.database.models import User
from app.database.crud import (
    get_restaurants,
    get_user_orders,
    get_restaurant,
    get_recommendation,
    create_recommendation,
    get_user_preferences
)
from app.models.recommendation import RecommendationResponse
from app.models.restaurant import RestaurantResponse
from app.core.recommender import (
    generate_recommendations as generate_recs,
    extract_user_patterns,
    select_chef_recommendation
)
from app.core.llm_service import (
    generate_insight,
    generate_chef_explanation
)
from app.core.logging_config import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/api/recommendations", tags=["recomendações"])


class RecommendationsListResponse(BaseModel):
    """Resposta para listagem de recomendações."""
    recommendations: List[RecommendationResponse]
    count: int
    generated_at: datetime


class ChefRecommendationResponse(BaseModel):
    """Resposta para recomendação única do Chef."""
    restaurant: RestaurantResponse
    similarity_score: float
    explanation: str  # Explicação gerada por LLM
    reasoning: List[str]  # Lista de razões (ex: "Você costuma pedir comida vegetariana")
    confidence: float  # Confiança da recomendação (0.0 a 1.0)
    generated_at: datetime


@router.get("", response_model=RecommendationsListResponse)
def get_recommendations(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    limit: int = Query(10, ge=1, le=50, description="Número de recomendações a retornar"),
    refresh: bool = Query(False, description="Recalcular recomendações (ignorar cache)")
):
    """
    Obtém recomendações personalizadas para o usuário autenticado.
    
    Args:
        current_user: Usuário autenticado (via JWT)
        db: Sessão do banco de dados
        limit: Número de recomendações (1-50, padrão: 10)
        refresh: Se True, recalcula recomendações ignorando cache
        
    Returns:
        RecommendationsListResponse: Lista de recomendações com insights
    """
    try:
        start_time = time.time()
        
        logger.info(
            "Gerando recomendações",
            extra={"user_id": current_user.id, "limit": limit, "refresh": refresh}
        )
        
        # 1. Gerar recomendações usando a lógica de recomendação
        recs_list = generate_recs(
            user_id=current_user.id,
            db=db,
            limit=limit,
            exclude_recent=True,
            min_rating=3.0,
            refresh=refresh
        )
        
        if not recs_list:
            # Se não houver recomendações, retornar lista vazia
            return RecommendationsListResponse(
                recommendations=[],
                count=0,
                generated_at=datetime.utcnow()
            )
        
        # 2. Preparar contexto do usuário para geração de insights
        user_orders = get_user_orders(db, user_id=current_user.id, limit=100)
        all_restaurants = get_restaurants(db, limit=10000)
        
        # Extrair padrões do usuário
        user_patterns = extract_user_patterns(current_user.id, user_orders, all_restaurants)
        
        user_context = {
            "name": current_user.name,
            "total_orders": len(user_orders),
            "favorite_cuisines": user_patterns.get("favorite_cuisines", [])
        }
        
        # 3. Para cada recomendação, gerar insight e formatar resposta
        # Remover duplicatas baseado no ID do restaurante (garantir unicidade)
        seen_restaurant_ids = set()
        unique_recs_list = []
        for rec in recs_list:
            restaurant_id = rec["restaurant"].id
            if restaurant_id not in seen_restaurant_ids:
                unique_recs_list.append(rec)
                seen_restaurant_ids.add(restaurant_id)
        
        recommendations_response = []
        generated_at = datetime.utcnow()
        
        for rec in unique_recs_list:
            restaurant = rec["restaurant"]
            similarity_score = rec["similarity_score"]
            
            # Gerar insight para esta recomendação
            insight = None
            try:
                insight = generate_insight(
                    user_id=current_user.id,
                    restaurant=restaurant,
                    similarity_score=similarity_score,
                    user_context=user_context,
                    user_patterns=user_patterns,
                    db=db,
                    use_cache=True,
                    ttl_days=7
                )
            except Exception as e:
                # Se falhar ao gerar insight, continuar sem ele
                # Um insight genérico será usado como fallback
                if db:
                    # Tentar buscar do cache primeiro
                    try:
                        cached_rec = get_recommendation(
                            db,
                            user_id=current_user.id,
                            restaurant_id=restaurant.id
                        )
                        if cached_rec and cached_rec.insight_text:
                            insight = cached_rec.insight_text
                    except:
                        pass
                
                if not insight:
                    # Fallback: insight genérico
                    from app.core.llm_service import format_cuisine_type
                    cuisine_type_formatted = format_cuisine_type(restaurant.cuisine_type)
                    insight = (
                        f"Recomendamos {restaurant.name}, um restaurante de {cuisine_type_formatted} "
                        f"com avaliação de {restaurant.rating}/5.0, baseado nas suas preferências."
                    )
            
            # Salvar/Atualizar recomendação no banco (para cache de insights)
            try:
                create_recommendation(
                    db=db,
                    user_id=current_user.id,
                    restaurant_id=restaurant.id,
                    similarity_score=similarity_score,
                    insight_text=insight
                )
            except Exception:
                # Se erro ao salvar, continuar (não crítico)
                pass
            
            # Verificar se já não foi adicionado (evitar duplicatas durante o loop)
            if any(r.restaurant.id == restaurant.id for r in recommendations_response):
                continue  # Pular se já existe
            
            # Formatar resposta - garantir que similarity_score está entre 0.0 e 1.0
            # (corrigir imprecisão de ponto flutuante que pode resultar em valores como 1.0000000000000002)
            similarity_score_clamped = max(0.0, min(1.0, float(similarity_score)))
            
            recommendations_response.append(RecommendationResponse(
                restaurant=RestaurantResponse.model_validate(restaurant),
                similarity_score=similarity_score_clamped,
                insight=insight,
                generated_at=generated_at
            ))
        
        # DEDUPLICAÇÃO FINAL: Remover duplicatas baseado no ID do restaurante
        # (garantia final antes de retornar a resposta)
        final_unique_recommendations = []
        final_seen_ids = set()
        final_seen_names = set()  # Também deduplicar por nome (evitar restaurantes com mesmo nome)
        
        for rec in recommendations_response:
            restaurant_id = rec.restaurant.id
            restaurant_name = rec.restaurant.name.strip().lower()  # Normalizar nome
            
            # Verificar duplicatas por ID E por nome (caso haja IDs diferentes com mesmo nome)
            if restaurant_id not in final_seen_ids and restaurant_name not in final_seen_names:
                final_unique_recommendations.append(rec)
                final_seen_ids.add(restaurant_id)
                final_seen_names.add(restaurant_name)
        
        duration_ms = (time.time() - start_time) * 1000
        
        logger.info(
            "Recomendações geradas com sucesso",
            extra={
                "user_id": current_user.id,
                "count": len(final_unique_recommendations),
                "count_before_dedup": len(recommendations_response),
                "duration_ms": round(duration_ms, 2)
            }
        )
        
        return RecommendationsListResponse(
            recommendations=final_unique_recommendations,
            count=len(final_unique_recommendations),
            generated_at=generated_at
        )
        
    except Exception as e:
        logger.error(
            "Erro ao gerar recomendações",
            extra={"user_id": current_user.id, "error_type": type(e).__name__, "error": str(e)},
            exc_info=True
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro ao gerar recomendações: {str(e)}"
        )


@router.get("/{restaurant_id}/insight", response_model=Dict[str, Any])
def get_restaurant_insight(
    restaurant_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Gera insight específico para um restaurante recomendado.
    
    Args:
        restaurant_id: ID do restaurante
        current_user: Usuário autenticado (via JWT)
        db: Sessão do banco de dados
        
    Returns:
        dict: Insight gerado para o restaurante
        
    Raises:
        HTTPException: Se restaurante não for encontrado
    """
    # Verificar se restaurante existe
    restaurant = get_restaurant(db, restaurant_id)
    if not restaurant:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Restaurante não encontrado"
        )
    
    # Obter contexto do usuário
    user_orders = get_user_orders(db, user_id=current_user.id, limit=100)
    all_restaurants = get_restaurants(db, limit=10000)
    
    # Extrair padrões do usuário
    user_patterns = extract_user_patterns(current_user.id, user_orders, all_restaurants)
    
    user_context = {
        "name": current_user.name,
        "total_orders": len(user_orders),
        "favorite_cuisines": user_patterns.get("favorite_cuisines", [])
    }
    
    # Buscar recomendação existente para obter similarity_score
    existing_rec = get_recommendation(
        db,
        user_id=current_user.id,
        restaurant_id=restaurant_id
    )
    
    similarity_score = 0.5  # Padrão se não houver recomendação
    if existing_rec:
        similarity_score = float(existing_rec.similarity_score)
    else:
        # Calcular similaridade rapidamente se não existir
        # (simplificado: usar rating normalizado como aproximação)
        similarity_score = float(restaurant.rating) / 5.0 if restaurant.rating else 0.5
    
    # Gerar insight
    try:
        insight = generate_insight(
            user_id=current_user.id,
            restaurant=restaurant,
            similarity_score=similarity_score,
            user_context=user_context,
            user_patterns=user_patterns,
            db=db,
            use_cache=False,  # Sempre gerar novo para este endpoint
            ttl_days=7
        )
    except Exception as e:
        # Fallback: insight genérico
        from app.core.llm_service import format_cuisine_type
        cuisine_type_formatted = format_cuisine_type(restaurant.cuisine_type)
        insight = (
            f"Recomendamos {restaurant.name}, um restaurante de {cuisine_type_formatted} "
            f"com avaliação de {restaurant.rating}/5.0, baseado nas suas preferências."
        )
    
        return {
            "restaurant_id": restaurant_id,
            "insight": insight,
            "generated_at": datetime.utcnow()
        }


@router.get("/chef-choice", response_model=ChefRecommendationResponse)
def get_chef_recommendation(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    refresh: bool = Query(False, description="Recalcular recomendação (ignorar cache)")
):
    """
    Obtém a recomendação única e personalizada do Chef para o usuário autenticado.
    
    O Chef analisa o perfil do usuário e escolhe a melhor recomendação do top 3,
    explicando por que essa foi escolhida especificamente para ele.
    
    Args:
        current_user: Usuário autenticado (via JWT)
        db: Sessão do banco de dados
        refresh: Se True, recalcula recomendações ignorando cache
        
    Returns:
        ChefRecommendationResponse: Recomendação única do Chef com explicação
        
    Raises:
        HTTPException: Se não houver recomendações disponíveis
    """
    try:
        logger.info(
            "Gerando recomendação do Chef",
            extra={"user_id": current_user.id, "refresh": refresh}
        )
        
        # 1. Obter contexto do usuário
        user_orders = get_user_orders(db, user_id=current_user.id, limit=100)
        all_restaurants = get_restaurants(db, limit=10000)
        
        # 2. Extrair padrões do usuário
        user_patterns = extract_user_patterns(current_user.id, user_orders, all_restaurants)
        
        user_context = {
            "name": current_user.name,
            "total_orders": len(user_orders),
            "favorite_cuisines": user_patterns.get("favorite_cuisines", [])
        }
        
        # 3. Gerar top 3 recomendações
        top_recommendations = generate_recs(
            user_id=current_user.id,
            db=db,
            limit=3,  # Top 3 para seleção
            exclude_recent=True,
            min_rating=3.0,
            refresh=refresh
        )
        
        if not top_recommendations:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Não encontramos recomendações no momento. Tente novamente em instantes."
            )
        
        # 4. Selecionar a melhor recomendação usando algoritmo de scoring
        chef_selection = select_chef_recommendation(
            recommendations=top_recommendations,
            user_id=current_user.id,
            orders=user_orders,
            db=db
        )
        
        if not chef_selection:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Não foi possível selecionar uma recomendação no momento."
            )
        
        restaurant = chef_selection["restaurant"]
        similarity_score = chef_selection["similarity_score"]
        reasoning = chef_selection.get("reasoning", [])
        confidence = chef_selection.get("confidence", 0.5)
        
        # Garantir que similarity_score está entre 0.0 e 1.0
        similarity_score_clamped = max(0.0, min(1.0, float(similarity_score)))
        confidence_clamped = max(0.0, min(1.0, float(confidence)))
        
        # 5. Gerar explicação personalizada do Chef
        try:
            explanation = generate_chef_explanation(
                user_id=current_user.id,
                restaurant=restaurant,
                reasoning=reasoning,
                similarity_score=similarity_score_clamped,
                confidence=confidence_clamped,
                user_context=user_context,
                user_patterns=user_patterns,
                db=db
            )
        except Exception as e:
            # Fallback: explicação baseada nas razões
            logger.warning(
                "Erro ao gerar explicação do Chef, usando fallback",
                extra={"user_id": current_user.id, "error": str(e)}
            )
            rating = float(restaurant.rating or 0)
            cuisine_type_formatted = restaurant.cuisine_type
            reasoning_text = ". ".join(reasoning) if reasoning else "baseado nas suas preferências"
            
            explanation = (
                f"Eu escolhi {restaurant.name} especialmente para você porque {reasoning_text}. "
                f"Este restaurante de {cuisine_type_formatted} tem uma avaliação de {rating}/5.0 "
                f"e tenho certeza que você vai adorar!"
            )
        
        generated_at = datetime.utcnow()
        
        logger.info(
            "Recomendação do Chef gerada com sucesso",
            extra={
                "user_id": current_user.id,
                "restaurant_id": restaurant.id,
                "confidence": confidence_clamped
            }
        )
        
        return ChefRecommendationResponse(
            restaurant=RestaurantResponse.model_validate(restaurant),
            similarity_score=similarity_score_clamped,
            explanation=explanation,
            reasoning=reasoning,
            confidence=confidence_clamped,
            generated_at=generated_at
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "Erro ao gerar recomendação do Chef",
            extra={"user_id": current_user.id, "error_type": type(e).__name__, "error": str(e)},
            exc_info=True
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro ao gerar recomendação do Chef: {str(e)}"
        )

