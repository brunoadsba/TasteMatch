"""
Lógica de recomendação personalizada usando embeddings semânticos.
Implementa algoritmo híbrido: collaborative filtering + content-based filtering.
"""

import json
from datetime import datetime
from typing import List, Optional, Dict, Any
from collections import Counter
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
from sqlalchemy.orm import Session

from app.database.crud import (
    get_user_orders,
    get_restaurants,
    get_user_preferences,
    create_or_update_user_preferences
)
from app.database.models import Restaurant, Order
from app.core.embeddings import get_embedding_model
from app.core.logging_config import get_logger

logger = get_logger(__name__)


def calculate_weight(order_date: datetime, rating: Optional[int]) -> float:
    """
    Calcula peso baseado em recência e rating do pedido.
    
    Args:
        order_date: Data do pedido
        rating: Avaliação do pedido (1-5) ou None
        
    Returns:
        float: Peso calculado (0.0 a 1.0+)
    """
    # Peso de recência: decai ao longo do ano
    days_ago = (datetime.now() - order_date).days
    recency_weight = max(0.0, 1.0 - (days_ago / 365.0))
    
    # Peso de rating: normalizado para 0.0 a 1.0
    rating_weight = (rating / 5.0) if rating else 0.5
    
    # Combinação: pedidos recentes e bem avaliados têm mais peso
    return recency_weight * rating_weight


def calculate_user_preference_embedding(
    user_id: int,
    orders: List[Order],
    restaurants: List[Restaurant],
    db: Session
) -> Optional[List[float]]:
    """
    Calcula embedding agregado das preferências do usuário.
    Usa média ponderada dos embeddings dos restaurantes que o usuário pediu.
    
    Args:
        user_id: ID do usuário
        orders: Lista de pedidos do usuário
        restaurants: Lista de todos os restaurantes (para buscar embeddings)
        db: Sessão do banco de dados
        
    Returns:
        Optional[List[float]]: Embedding do usuário (384 dimensões) ou None se não houver pedidos
    """
    if not orders:
        return None
    
    # Criar dicionário de restaurantes para busca rápida
    restaurants_dict = {r.id: r for r in restaurants}
    
    restaurant_embeddings = []
    weights = []
    
    for order in orders:
        restaurant = restaurants_dict.get(order.restaurant_id)
        if not restaurant or not restaurant.embedding:
            continue
        
        # Carregar embedding do restaurante
        if isinstance(restaurant.embedding, str):
            embedding = json.loads(restaurant.embedding)
        else:
            embedding = restaurant.embedding
        
        # Calcular peso baseado em recência e rating
        weight = calculate_weight(order.order_date, order.rating)
        
        restaurant_embeddings.append(embedding)
        weights.append(weight)
    
    if not restaurant_embeddings:
        return None
    
    # Média ponderada dos embeddings
    restaurant_embeddings_array = np.array(restaurant_embeddings)
    weights_array = np.array(weights)
    
    user_embedding = np.average(restaurant_embeddings_array, axis=0, weights=weights_array)
    
    return user_embedding.tolist()


def extract_user_patterns(
    user_id: int,
    orders: List[Order],
    restaurants: List[Restaurant]
) -> Dict[str, Any]:
    """
    Extrai padrões comportamentais do usuário do histórico de pedidos.
    
    Args:
        user_id: ID do usuário
        orders: Lista de pedidos do usuário
        restaurants: Lista de restaurantes
        
    Returns:
        dict: Padrões extraídos (culinárias favoritas, horários, ticket médio, etc.)
    """
    patterns = {
        "favorite_cuisines": [],
        "preferred_days": [],
        "preferred_hours": [],
        "average_order_value": 0.0,
        "total_orders": len(orders)
    }
    
    if not orders:
        return patterns
    
    # Criar dicionário de restaurantes
    restaurants_dict = {r.id: r for r in restaurants}
    
    # Culinárias favoritas (top 3)
    cuisine_counts = Counter()
    total_amount = 0.0
    valid_orders = 0
    day_counts = Counter()
    hour_ranges = []
    
    for order in orders:
        restaurant = restaurants_dict.get(order.restaurant_id)
        if restaurant:
            cuisine_counts[restaurant.cuisine_type] += 1
        
        # Contar por dia da semana
        day_counts[order.order_date.weekday()] += 1
        
        # Horários preferidos (manhã, tarde, noite)
        hour = order.order_date.hour
        if 6 <= hour < 12:
            hour_ranges.append("manhã")
        elif 12 <= hour < 18:
            hour_ranges.append("tarde")
        else:
            hour_ranges.append("noite")
        
        # Ticket médio
        if order.total_amount:
            total_amount += float(order.total_amount)
            valid_orders += 1
    
    patterns["favorite_cuisines"] = [cuisine for cuisine, _ in cuisine_counts.most_common(3)]
    patterns["preferred_days"] = [day for day, _ in day_counts.most_common(3)]
    patterns["preferred_hours"] = list(set(hour_ranges))
    patterns["average_order_value"] = round(total_amount / valid_orders if valid_orders > 0 else 0.0, 2)
    
    return patterns


def calculate_similarity(
    user_embedding: List[float],
    restaurant_embedding: List[float]
) -> float:
    """
    Calcula similaridade coseno entre embedding do usuário e do restaurante.
    
    Args:
        user_embedding: Embedding do usuário (384 dimensões)
        restaurant_embedding: Embedding do restaurante (384 dimensões)
        
    Returns:
        float: Similaridade coseno (0.0 a 1.0)
    """
    user_vec = np.array(user_embedding).reshape(1, -1)
    rest_vec = np.array(restaurant_embedding).reshape(1, -1)
    similarity = cosine_similarity(user_vec, rest_vec)[0][0]
    return float(similarity)


def get_popular_restaurants(
    db: Session,
    limit: int = 10,
    min_rating: float = 3.5
) -> List[Dict[str, Any]]:
    """
    Retorna restaurantes populares como fallback para cold start.
    Ordena por rating (maior primeiro).
    
    Args:
        db: Sessão do banco de dados
        limit: Número de restaurantes a retornar
        min_rating: Rating mínimo
        
    Returns:
        List[Dict]: Lista de restaurantes com similarity_score = 0.5 (fallback)
    """
    restaurants = get_restaurants(
        db=db,
        skip=0,
        limit=limit * 2,  # Buscar mais para filtrar
        min_rating=min_rating
    )
    
    # Ordenar por rating (decrescente)
    restaurants_sorted = sorted(restaurants, key=lambda r: float(r.rating or 0), reverse=True)
    
    # Remover duplicatas por ID antes de retornar
    seen_ids = set()
    unique_restaurants = []
    for restaurant in restaurants_sorted:
        if restaurant.id not in seen_ids:
            unique_restaurants.append(restaurant)
            seen_ids.add(restaurant.id)
    
    recommendations = []
    for restaurant in unique_restaurants[:limit]:
        recommendations.append({
            "restaurant": restaurant,
            "similarity_score": 0.5  # Score neutro para fallback
        })
    
    return recommendations


def generate_recommendations(
    user_id: int,
    db: Session,
    limit: int = 10,
    exclude_recent: bool = True,
    min_rating: float = 3.0,
    refresh: bool = False
) -> List[Dict[str, Any]]:
    """
    Gera recomendações personalizadas para um usuário.
    
    Algoritmo:
    1. Calcula embedding do usuário baseado no histórico de pedidos
    2. Calcula similaridade coseno com todos os restaurantes
    3. Filtra e ordena por similaridade
    4. Retorna top N recomendações
    
    Args:
        user_id: ID do usuário
        db: Sessão do banco de dados
        limit: Número de recomendações a retornar
        exclude_recent: Se True, exclui restaurantes pedidos recentemente
        min_rating: Rating mínimo para recomendar
        refresh: Se True, recalcula embedding do usuário (ignora cache)
        
    Returns:
        List[Dict]: Lista de recomendações com restaurant e similarity_score
    """
    # 1. Obter pedidos do usuário
    orders = get_user_orders(db, user_id=user_id, skip=0, limit=1000)
    
    # 2. Cold start: se usuário não tem pedidos, retornar populares
    if not orders:
        return get_popular_restaurants(db, limit=limit, min_rating=min_rating)
    
    # 3. Verificar cache de preferências (se não for refresh)
    user_embedding = None
    if not refresh:
        preferences = get_user_preferences(db, user_id=user_id)
        if preferences and preferences.preference_embedding:
            try:
                if isinstance(preferences.preference_embedding, str):
                    user_embedding = json.loads(preferences.preference_embedding)
                else:
                    user_embedding = preferences.preference_embedding
            except:
                pass  # Se erro ao carregar, recalcular
    
    # 4. Se não há embedding cached, calcular novo
    if user_embedding is None:
        # Obter todos os restaurantes
        restaurants = get_restaurants(db, skip=0, limit=10000)
        
        # Calcular embedding do usuário
        user_embedding = calculate_user_preference_embedding(
            user_id=user_id,
            orders=orders,
            restaurants=restaurants,
            db=db
        )
        
        # Se ainda não conseguiu calcular (sem restaurantes com embeddings), fallback
        if user_embedding is None:
            return get_popular_restaurants(db, limit=limit, min_rating=min_rating)
        
        # Cachear embedding nas preferências do usuário
        try:
            favorite_cuisines = extract_user_patterns(user_id, orders, restaurants)["favorite_cuisines"]
            create_or_update_user_preferences(
                db=db,
                user_id=user_id,
                preference_embedding=json.dumps(user_embedding),
                favorite_cuisines=json.dumps(favorite_cuisines) if favorite_cuisines else None
            )
        except Exception as e:
            # Se erro ao salvar cache, continuar (não crítico)
            pass
    
    # 5. Obter todos os restaurantes para calcular similaridade
    all_restaurants = get_restaurants(db, skip=0, limit=10000, min_rating=min_rating)
    
    # 6. IDs de restaurantes pedidos recentemente (para excluir se solicitado)
    recent_restaurant_ids = set()
    if exclude_recent:
        recent_orders = sorted(orders, key=lambda o: o.order_date, reverse=True)[:10]
        recent_restaurant_ids = {order.restaurant_id for order in recent_orders}
    
    # 7. Calcular similaridade com cada restaurante
    recommendations = []
    seen_restaurant_ids = set()  # Rastrear restaurantes já processados para evitar duplicatas
    
    for restaurant in all_restaurants:
        # Pular se já processado (evitar duplicatas)
        if restaurant.id in seen_restaurant_ids:
            continue
        
        # Pular restaurantes recentes se solicitado
        if restaurant.id in recent_restaurant_ids:
            continue
        
        # Verificar se restaurante tem embedding
        if not restaurant.embedding:
            continue
        
        # Carregar embedding do restaurante
        try:
            if isinstance(restaurant.embedding, str):
                restaurant_embedding = json.loads(restaurant.embedding)
            else:
                restaurant_embedding = restaurant.embedding
            
            # Calcular similaridade
            similarity = calculate_similarity(user_embedding, restaurant_embedding)
            
            recommendations.append({
                "restaurant": restaurant,
                "similarity_score": similarity
            })
            
            # Marcar como processado
            seen_restaurant_ids.add(restaurant.id)
        except Exception as e:
            # Se erro ao processar restaurante, pular
            continue
    
    # 8. Ordenar por similaridade (maior primeiro)
    recommendations.sort(key=lambda x: x["similarity_score"], reverse=True)
    
    # 9. Retornar top N (garantir que não há duplicatas mesmo após ordenação)
    unique_recommendations = []
    unique_ids = set()
    for rec in recommendations:
        restaurant_id = rec["restaurant"].id
        if restaurant_id not in unique_ids:
            unique_recommendations.append(rec)
            unique_ids.add(restaurant_id)
            if len(unique_recommendations) >= limit:
                break
    
    return unique_recommendations


def select_chef_recommendation(
    recommendations: List[Dict[str, Any]],
    user_id: int,
    orders: List[Order],
    db: Session
) -> Optional[Dict[str, Any]]:
    """
    Seleciona a melhor recomendação do top 3 usando algoritmo de scoring ponderado.
    
    Algoritmo de scoring:
    - Similaridade (peso 40%): Score de similaridade já calculado
    - Rating do restaurante (peso 20%): Normalizado para 0.0-1.0
    - Novidade (peso 20%): Não pedido recentemente (+0.2) ou pedido recentemente (-0.2)
    - Match com padrões (peso 20%): Match com culinárias favoritas do usuário
    
    Args:
        recommendations: Lista de top 3 recomendações (já ordenadas por similaridade)
        user_id: ID do usuário
        orders: Lista de pedidos do usuário
        db: Sessão do banco de dados
        
    Returns:
        Optional[Dict]: Melhor recomendação com razões ou None se lista vazia
    """
    if not recommendations:
        return None
    
    # Extrair padrões do usuário
    restaurants = get_restaurants(db, skip=0, limit=10000)
    user_patterns = extract_user_patterns(user_id, orders, restaurants)
    favorite_cuisines = set(user_patterns.get("favorite_cuisines", []))
    
    # IDs de restaurantes pedidos recentemente (últimos 10 pedidos)
    recent_restaurant_ids = set()
    if orders:
        recent_orders = sorted(orders, key=lambda o: o.order_date, reverse=True)[:10]
        recent_restaurant_ids = {order.restaurant_id for order in recent_orders}
    
    # Calcular score ponderado para cada recomendação
    scored_recommendations = []
    
    for rec in recommendations[:3]:  # Top 3 apenas
        restaurant = rec["restaurant"]
        similarity_score = rec["similarity_score"]
        
        # 1. Similaridade (peso 40%) - já normalizado 0.0-1.0
        similarity_weight = similarity_score * 0.4
        
        # 2. Rating do restaurante (peso 20%) - normalizar para 0.0-1.0
        rating_normalized = float(restaurant.rating or 0) / 5.0
        rating_weight = rating_normalized * 0.2
        
        # 3. Novidade (peso 20%)
        # Se não foi pedido recentemente: +0.2 (peso completo), se foi: 0.0 (sem bônus)
        novelty_weight = 0.2 if restaurant.id not in recent_restaurant_ids else 0.0
        
        # 4. Match com padrões (peso 20%)
        # Se a culinária está nas favoritas: +0.2, senão: 0.0
        pattern_match = 0.2 if restaurant.cuisine_type in favorite_cuisines else 0.0
        pattern_weight = pattern_match * 0.2
        
        # Score final (soma ponderada)
        final_score = similarity_weight + rating_weight + novelty_weight + pattern_weight
        
        # Razões para a escolha
        reasoning = []
        if similarity_score > 0.7:
            reasoning.append("Alta similaridade com suas preferências")
        if rating_normalized > 0.8:
            reasoning.append(f"Excelente avaliação ({restaurant.rating}/5.0)")
        if restaurant.id not in recent_restaurant_ids:
            reasoning.append("Restaurante novo para você")
        if restaurant.cuisine_type in favorite_cuisines:
            reasoning.append(f"Combina com seu gosto por {restaurant.cuisine_type}")
        
        scored_recommendations.append({
            "restaurant": restaurant,
            "similarity_score": similarity_score,
            "final_score": final_score,
            "reasoning": reasoning,
            "confidence": min(1.0, max(0.0, final_score))  # Garantir 0.0-1.0
        })
    
    # Ordenar por score final (maior primeiro)
    scored_recommendations.sort(key=lambda x: x["final_score"], reverse=True)
    
    # Retornar a melhor recomendação
    if scored_recommendations:
        return scored_recommendations[0]
    
    return None

