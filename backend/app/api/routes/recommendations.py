"""
Endpoints da API para sistema de recomendações personalizadas.
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
from datetime import datetime
from pydantic import BaseModel
import json

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
    extract_user_patterns
)
from app.core.llm_service import (
    generate_insight
)

router = APIRouter(prefix="/api/recommendations", tags=["recomendações"])


class RecommendationsListResponse(BaseModel):
    """Resposta para listagem de recomendações."""
    recommendations: List[RecommendationResponse]
    count: int
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
        recommendations_response = []
        generated_at = datetime.utcnow()
        
        for rec in recs_list:
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
                    insight = (
                        f"Recomendamos {restaurant.name}, um restaurante de {restaurant.cuisine_type} "
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
            
            # Formatar resposta
            recommendations_response.append(RecommendationResponse(
                restaurant=RestaurantResponse.model_validate(restaurant),
                similarity_score=float(similarity_score),
                insight=insight,
                generated_at=generated_at
            ))
        
        return RecommendationsListResponse(
            recommendations=recommendations_response,
            count=len(recommendations_response),
            generated_at=generated_at
        )
        
    except Exception as e:
        # Log do erro (em produção, usar logger adequado)
        import traceback
        traceback.print_exc()
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
        insight = (
            f"Recomendamos {restaurant.name}, um restaurante de {restaurant.cuisine_type} "
            f"com avaliação de {restaurant.rating}/5.0, baseado nas suas preferências."
        )
    
    return {
        "restaurant_id": restaurant_id,
        "insight": insight,
        "generated_at": datetime.utcnow()
    }

