"""
Modelos Pydantic para validação de dados de restaurante.
"""

from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class RestaurantBase(BaseModel):
    """Modelo base de restaurante."""
    name: str
    cuisine_type: str
    description: Optional[str] = None
    rating: float = Field(ge=0.0, le=5.0, default=0.0)
    price_range: Optional[str] = None  # "low", "medium", "high"
    location: Optional[str] = None


class RestaurantCreate(RestaurantBase):
    """Modelo para criação de restaurante."""
    pass


class RestaurantResponse(RestaurantBase):
    """Modelo de resposta de restaurante."""
    id: int
    created_at: datetime
    
    class Config:
        from_attributes = True


class RestaurantWithScore(RestaurantResponse):
    """Modelo de restaurante com score de similaridade (para recomendações)."""
    similarity_score: float = Field(ge=0.0, le=1.0)
    insight: Optional[str] = None

