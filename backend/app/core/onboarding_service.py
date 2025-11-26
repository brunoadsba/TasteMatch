"""
Serviço de onboarding gamificado para gerar vetor sintético de usuários novos.
Resolve o problema de cold start convertendo intenção do usuário em embedding.
"""

import json
from typing import List, Optional
import numpy as np
from sqlalchemy.orm import Session
from sqlalchemy import select, func

from app.database.crud import get_restaurants, create_or_update_user_preferences
from app.database.models import Restaurant
from app.core.logging_config import get_logger

logger = get_logger(__name__)


def normalize_cuisine_type(cuisine_type: str) -> str:
    """
    Normaliza tipo de culinária para corresponder ao formato do banco.
    Converte para minúsculas e singulariza quando necessário.
    """
    normalized = cuisine_type.lower().strip()
    
    # Mapeamento de variações comuns
    mappings = {
        'japonês': 'japonesa',
        'italiano': 'italiana',
        'francês': 'francesa',
        'brasileiro': 'brasileira',
        'chinês': 'chinesa',
        'mexicano': 'mexicana',
        'português': 'portuguesa',
        'indiano': 'indiana',
        'tailandês': 'tailandesa',
    }
    
    return mappings.get(normalized, normalized)


def generate_cold_start_embedding(
    selected_cuisines: List[str],
    price_preference: Optional[str] = None,  # 'low', 'medium', 'high'
    dietary_restrictions: Optional[List[str]] = None,  # ['vegan', 'gluten-free', etc.]
    db: Session = None
) -> Optional[List[float]]:
    """
    Gera um vetor sintético para usuários novos baseado no onboarding.
    
    Técnica: Centróide de Categoria
    - Busca os melhores restaurantes das culinárias escolhidas
    - Calcula a média vetorial (centróide) desses restaurantes
    - Isso coloca o usuário no "centro" do cluster de culinárias que ele gosta
    
    Args:
        selected_cuisines: Lista de tipos de culinária selecionados pelo usuário
        price_preference: Preferência de preço ('low', 'medium', 'high')
        dietary_restrictions: Restrições alimentares (opcional)
        db: Sessão do banco de dados
        
    Returns:
        List[float]: Vetor sintético (embedding) ou None se não conseguir gerar
    """
    if not selected_cuisines or not db:
        return None
    
    try:
        # Normalizar tipos de culinária
        normalized_cuisines = [normalize_cuisine_type(c) for c in selected_cuisines]
        
        # Buscar restaurantes que representam as escolhas (arquétipos)
        # Pegamos os top 20 restaurantes de cada culinária escolhida
        # com alta avaliação (rating >= 4.0) para garantir qualidade
        query = select(Restaurant).where(
            Restaurant.cuisine_type.in_(normalized_cuisines),
            Restaurant.rating >= 4.0,  # Apenas restaurantes bem avaliados
            Restaurant.embedding.isnot(None)  # Deve ter embedding
        )
        
        # Filtro opcional de preço
        if price_preference:
            price_mapping = {
                'low': 'low',
                'cheap': 'low',
                'econômico': 'low',
                'medium': 'medium',
                'moderate': 'medium',
                'moderado': 'medium',
                'high': 'high',
                'expensive': 'high',
                'caro': 'high',
            }
            mapped_price = price_mapping.get(price_preference.lower(), price_preference.lower())
            query = query.where(Restaurant.price_range == mapped_price)
        
        # Executar query e coletar restaurantes
        restaurants = db.execute(query).scalars().all()
        
        # Limitar a 20 restaurantes por culinária para evitar sobrepeso
        # Ordenar por rating e pegar os melhores
        restaurants_sorted = sorted(restaurants, key=lambda r: float(r.rating or 0), reverse=True)
        archetype_restaurants = restaurants_sorted[:min(20 * len(normalized_cuisines), len(restaurants_sorted))]
        
        if not archetype_restaurants:
            logger.warning(
                "Não foi possível encontrar restaurantes para gerar vetor sintético",
                extra={"cuisines": normalized_cuisines, "price_preference": price_preference}
            )
            return None
        
        # Coletar embeddings dos restaurantes arquétipos
        archetype_embeddings = []
        for restaurant in archetype_restaurants:
            try:
                if isinstance(restaurant.embedding, str):
                    embedding = json.loads(restaurant.embedding)
                else:
                    embedding = restaurant.embedding
                
                if embedding and isinstance(embedding, list) and len(embedding) > 0:
                    archetype_embeddings.append(embedding)
            except Exception as e:
                logger.warning(
                    f"Erro ao processar embedding do restaurante {restaurant.id}",
                    extra={"error": str(e)}
                )
                continue
        
        if not archetype_embeddings:
            logger.warning("Nenhum embedding válido encontrado para gerar vetor sintético")
            return None
        
        # Calcular a média (centróide)
        # Isso coloca o usuário no "centro" do cluster de culinárias que ele gosta
        archetype_matrix = np.array(archetype_embeddings)
        synthetic_vector = np.mean(archetype_matrix, axis=0)
        
        # Normalizar o vetor (opcional, mas ajuda na consistência)
        norm = np.linalg.norm(synthetic_vector)
        if norm > 0:
            synthetic_vector = synthetic_vector / norm
        
        logger.info(
            "Vetor sintético gerado com sucesso",
            extra={
                "cuisines": normalized_cuisines,
                "num_restaurants": len(archetype_restaurants),
                "vector_dim": len(synthetic_vector)
            }
        )
        
        return synthetic_vector.tolist()
        
    except Exception as e:
        logger.error(
            "Erro ao gerar vetor sintético",
            extra={"error": str(e), "cuisines": selected_cuisines},
            exc_info=True
        )
        return None


def complete_onboarding(
    user_id: int,
    selected_cuisines: List[str],
    price_preference: Optional[str] = None,
    dietary_restrictions: Optional[List[str]] = None,
    db: Session = None
) -> bool:
    """
    Completa o onboarding do usuário gerando e salvando vetor sintético.
    
    Args:
        user_id: ID do usuário
        selected_cuisines: Lista de culinárias selecionadas
        price_preference: Preferência de preço
        dietary_restrictions: Restrições alimentares
        db: Sessão do banco de dados
        
    Returns:
        bool: True se onboarding foi completado com sucesso, False caso contrário
    """
    if not db:
        return False
    
    try:
        # Gerar vetor sintético
        synthetic_vector = generate_cold_start_embedding(
            selected_cuisines=selected_cuisines,
            price_preference=price_preference,
            dietary_restrictions=dietary_restrictions,
            db=db
        )
        
        if not synthetic_vector:
            logger.warning(
                "Não foi possível gerar vetor sintético para onboarding",
                extra={"user_id": user_id}
            )
            return False
        
        # Salvar no perfil do usuário
        # Agora o usuário tem um vetor antes mesmo de fazer o primeiro pedido!
        create_or_update_user_preferences(
            db=db,
            user_id=user_id,
            preference_embedding=json.dumps(synthetic_vector),
            favorite_cuisines=json.dumps(selected_cuisines)
        )
        
        logger.info(
            "Onboarding completado com sucesso",
            extra={
                "user_id": user_id,
                "cuisines": selected_cuisines,
                "has_synthetic_vector": True
            }
        )
        
        return True
        
    except Exception as e:
        logger.error(
            "Erro ao completar onboarding",
            extra={"user_id": user_id, "error": str(e)},
            exc_info=True
        )
        return False

