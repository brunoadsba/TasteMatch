"""
Endpoints relacionados a pedidos.
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import select, func
from typing import List, Optional, Dict, Any
from datetime import datetime
from app.database.base import get_db
from app.api.deps import get_current_user
from app.database.models import User, Order, Restaurant
from app.models.order import OrderCreate, OrderResponse
from app.database.crud import get_user_orders, create_order, get_restaurant
from pydantic import BaseModel
import json

router = APIRouter(prefix="/api/orders", tags=["pedidos"])


class OrderListResponse(BaseModel):
    """Resposta da listagem de pedidos."""
    orders: List[Dict[str, Any]]
    total: int
    count: int


@router.get("", response_model=OrderListResponse)
def list_user_orders(
    limit: int = Query(20, ge=1, le=100, description="Número de pedidos"),
    offset: int = Query(0, ge=0, description="Offset para paginação"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Lista histórico de pedidos do usuário autenticado.
    
    Args:
        limit: Número de pedidos a retornar
        offset: Offset para paginação
        current_user: Usuário autenticado
        db: Sessão do banco de dados
        
    Returns:
        OrderListResponse: Lista de pedidos do usuário
    """
    # Buscar pedidos do usuário
    orders = get_user_orders(
        db=db,
        user_id=current_user.id,
        skip=offset,
        limit=limit
    )
    
    # Contar total de pedidos do usuário
    count_stmt = select(func.count(Order.id)).where(Order.user_id == current_user.id)
    total = db.execute(count_stmt).scalar() or 0
    
    # Buscar informações dos restaurantes para incluir nome
    # Usando eager loading já otimizado no crud.py (get_user_orders)
    restaurants = {}
    for order in orders:
        if order.restaurant:
            restaurants[order.restaurant_id] = order.restaurant
    
    # Formatar pedidos com nome do restaurante
    orders_data = []
    for order in orders:
        restaurant = restaurants.get(order.restaurant_id)
        order_dict = {
            "id": order.id,
            "restaurant_id": order.restaurant_id,
            "restaurant_name": restaurant.name if restaurant else None,
            "order_date": order.order_date.isoformat() + "Z",
            "total_amount": float(order.total_amount) if order.total_amount else None,
            "items": json.loads(order.items) if order.items else [],
            "rating": order.rating,
            "created_at": order.created_at.isoformat() + "Z"
        }
        orders_data.append(order_dict)
    
    return OrderListResponse(
        orders=orders_data,
        total=total,
        count=len(orders)
    )


@router.post("", response_model=OrderResponse, status_code=status.HTTP_201_CREATED)
def create_new_order(
    order_data: OrderCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Cria um novo pedido para o usuário autenticado.
    
    Args:
        order_data: Dados do pedido
        current_user: Usuário autenticado
        db: Sessão do banco de dados
        
    Returns:
        OrderResponse: Pedido criado
        
    Raises:
        HTTPException: Se restaurante não for encontrado ou dados inválidos
    """
    # Verificar se restaurante existe
    restaurant = get_restaurant(db, restaurant_id=order_data.restaurant_id)
    if not restaurant:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Restaurante com ID {order_data.restaurant_id} não encontrado"
        )
    
    # Criar pedido (user_id será o do usuário autenticado)
    db_order = create_order(
        db=db,
        order=order_data,
        user_id=current_user.id
    )
    
    # Converter items de JSON string para lista se necessário
    order_dict = {
        "id": db_order.id,
        "user_id": db_order.user_id,
        "restaurant_id": db_order.restaurant_id,
        "order_date": db_order.order_date,
        "total_amount": db_order.total_amount,
        "items": json.loads(db_order.items) if db_order.items else None,
        "rating": db_order.rating,
        "created_at": db_order.created_at
    }
    
    return OrderResponse.model_validate(order_dict)


@router.delete("/simulation", status_code=status.HTTP_200_OK)
def reset_simulation(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Remove todos os pedidos simulados do usuário autenticado.
    
    Args:
        current_user: Usuário autenticado
        db: Sessão do banco de dados
        
    Returns:
        dict: Número de pedidos deletados
    """
    # Contar pedidos antes de deletar
    count_stmt = select(func.count(Order.id)).where(
        Order.user_id == current_user.id,
        Order.is_simulation == True
    )
    total_before = db.execute(count_stmt).scalar() or 0
    
    # Deletar apenas pedidos simulados do usuário autenticado
    delete_stmt = select(Order).where(
        Order.user_id == current_user.id,
        Order.is_simulation == True
    )
    orders_to_delete = db.execute(delete_stmt).scalars().all()
    
    for order in orders_to_delete:
        db.delete(order)
    
    db.commit()
    deleted_count = total_before
    
    return {"deleted": deleted_count, "message": f"{deleted_count} pedido(s) simulado(s) removido(s)"}

