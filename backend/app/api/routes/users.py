"""
Endpoints relacionados a usuários autenticados.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import Dict, Any
from app.database.base import get_db
from app.api.deps import get_current_user
from app.database.models import User, Order
from app.models.user import UserResponse
from app.database.crud import get_user_orders
from sqlalchemy import select, func
import json
from collections import Counter
from datetime import datetime

router = APIRouter(prefix="/api/users", tags=["usuários"])


@router.get("/me", response_model=UserResponse)
def get_current_user_info(
    current_user: User = Depends(get_current_user)
):
    """
    Obtém informações do usuário autenticado.
    
    Args:
        current_user: Usuário autenticado (via dependency)
        
    Returns:
        UserResponse: Informações do usuário
        
    Raises:
        HTTPException: Se o banco de dados não estiver disponível
    """
    return UserResponse.model_validate(current_user)


@router.get("/me/preferences")
def get_user_preferences(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Obtém preferências agregadas do usuário baseadas no histórico de pedidos.
    
    Args:
        current_user: Usuário autenticado
        db: Sessão do banco de dados
        
    Returns:
        dict: Preferências do usuário (culinárias favoritas, ticket médio, etc.)
    """
    # Buscar todos os pedidos do usuário
    orders = get_user_orders(db, user_id=current_user.id, limit=1000)
    
    if not orders:
        return {
            "user_id": current_user.id,
            "favorite_cuisines": [],
            "total_orders": 0,
            "average_order_value": 0.0,
            "last_updated": datetime.utcnow().isoformat() + "Z"
        }
    
    # Buscar informações dos restaurantes dos pedidos
    restaurant_ids = [order.restaurant_id for order in orders]
    from app.database.models import Restaurant
    
    stmt = select(Restaurant).where(Restaurant.id.in_(restaurant_ids))
    restaurants = {r.id: r for r in db.execute(stmt).scalars().all()}
    
    # Extrair culinárias favoritas (top 3 mais pedidas)
    cuisine_counts = Counter()
    total_amount = 0.0
    valid_orders = 0
    
    for order in orders:
        restaurant = restaurants.get(order.restaurant_id)
        if restaurant:
            cuisine_counts[restaurant.cuisine_type] += 1
        
        if order.total_amount:
            total_amount += float(order.total_amount)
            valid_orders += 1
    
    favorite_cuisines = [cuisine for cuisine, _ in cuisine_counts.most_common(3)]
    average_order_value = total_amount / valid_orders if valid_orders > 0 else 0.0
    
    return {
        "user_id": current_user.id,
        "favorite_cuisines": favorite_cuisines,
        "total_orders": len(orders),
        "average_order_value": round(average_order_value, 2),
        "last_updated": datetime.utcnow().isoformat() + "Z"
    }

