"""
Endpoints relacionados a restaurantes.
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import select, func
from typing import List, Optional
from app.database.base import get_db
from app.database.crud import get_restaurant, get_restaurants
from app.models.restaurant import RestaurantResponse
from pydantic import BaseModel

router = APIRouter(prefix="/api/restaurants", tags=["restaurantes"])


class RestaurantListResponse(BaseModel):
    """Resposta da listagem de restaurantes."""
    restaurants: List[RestaurantResponse]
    total: int
    page: int
    limit: int
    
    class Config:
        from_attributes = True


@router.get("", response_model=RestaurantListResponse)
def list_restaurants(
    page: int = Query(1, ge=1, description="Número da página"),
    limit: int = Query(20, ge=1, le=100, description="Itens por página"),
    cuisine_type: Optional[str] = Query(None, description="Filtrar por tipo de culinária"),
    min_rating: Optional[float] = Query(None, ge=0.0, le=5.0, description="Rating mínimo"),
    price_range: Optional[str] = Query(None, description="Filtrar por faixa de preço (low, medium, high)"),
    search: Optional[str] = Query(None, description="Busca textual no nome e descrição"),
    sort_by: Optional[str] = Query(None, description="Ordenação (rating_desc, rating_asc, name_asc, name_desc)"),
    db: Session = Depends(get_db)
):
    """
    Lista restaurantes com paginação e filtros opcionais.
    
    Args:
        page: Número da página (inicia em 1)
        limit: Itens por página (máximo 100)
        cuisine_type: Filtrar por tipo de culinária
        min_rating: Rating mínimo (0.0 a 5.0)
        price_range: Filtrar por faixa de preço (low, medium, high)
        search: Busca textual no nome e descrição
        sort_by: Ordenação (rating_desc, rating_asc, name_asc, name_desc)
        db: Sessão do banco de dados
        
    Returns:
        RestaurantListResponse: Lista de restaurantes paginada
    """
    # Calcular offset
    skip = (page - 1) * limit
    
    # Buscar restaurantes com filtros
    restaurants = get_restaurants(
        db=db,
        skip=skip,
        limit=limit,
        cuisine_type=cuisine_type,
        min_rating=min_rating,
        price_range=price_range,
        search=search,
        sort_by=sort_by
    )
    
    # Contar total de restaurantes (com filtros aplicados)
    from app.database.models import Restaurant
    
    count_stmt = select(func.count(Restaurant.id))
    if cuisine_type:
        count_stmt = count_stmt.where(Restaurant.cuisine_type == cuisine_type)
    if min_rating is not None:
        count_stmt = count_stmt.where(Restaurant.rating >= min_rating)
    if price_range:
        count_stmt = count_stmt.where(Restaurant.price_range == price_range)
    if search:
        search_pattern = f"%{search}%"
        count_stmt = count_stmt.where(
            (Restaurant.name.ilike(search_pattern)) |
            (Restaurant.description.ilike(search_pattern))
        )
    
    total = db.execute(count_stmt).scalar() or 0
    
    return RestaurantListResponse(
        restaurants=[RestaurantResponse.model_validate(r) for r in restaurants],
        total=total,
        page=page,
        limit=limit
    )


@router.get("/{restaurant_id}", response_model=RestaurantResponse)
def get_restaurant_details(
    restaurant_id: int,
    db: Session = Depends(get_db)
):
    """
    Obtém detalhes de um restaurante específico.
    
    Args:
        restaurant_id: ID do restaurante
        db: Sessão do banco de dados
        
    Returns:
        RestaurantResponse: Detalhes do restaurante
        
    Raises:
        HTTPException: Se restaurante não for encontrado
    """
    restaurant = get_restaurant(db, restaurant_id=restaurant_id)
    
    if not restaurant:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Restaurante com ID {restaurant_id} não encontrado"
        )
    
    return RestaurantResponse.model_validate(restaurant)

