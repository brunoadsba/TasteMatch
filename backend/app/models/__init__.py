"""
Modelos Pydantic para validação de dados.
"""

from app.models.user import UserBase, UserCreate, UserResponse
from app.models.restaurant import (
    RestaurantBase,
    RestaurantCreate,
    RestaurantResponse,
    RestaurantWithScore,
)
from app.models.order import OrderBase, OrderCreate, OrderResponse
from app.models.recommendation import RecommendationResponse

__all__ = [
    # User
    "UserBase",
    "UserCreate",
    "UserResponse",
    # Restaurant
    "RestaurantBase",
    "RestaurantCreate",
    "RestaurantResponse",
    "RestaurantWithScore",
    # Order
    "OrderBase",
    "OrderCreate",
    "OrderResponse",
    # Recommendation
    "RecommendationResponse",
]

