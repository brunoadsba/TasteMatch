"""
Modelos Pydantic para validação de dados de pedido.
"""

from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, List, Dict
from decimal import Decimal


class OrderBase(BaseModel):
    """Modelo base de pedido."""
    restaurant_id: int
    order_date: datetime
    total_amount: Optional[Decimal] = None
    items: Optional[List[Dict]] = None
    rating: Optional[int] = Field(ge=1, le=5, default=None)


class OrderCreate(OrderBase):
    """Modelo para criação de pedido."""
    pass


class OrderResponse(OrderBase):
    """Modelo de resposta de pedido."""
    id: int
    user_id: int
    created_at: datetime
    
    class Config:
        from_attributes = True

