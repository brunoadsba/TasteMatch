"""
Modelos Pydantic para validação de dados de recomendação.
"""

from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional
from app.models.restaurant import RestaurantResponse


class RecommendationResponse(BaseModel):
    """Modelo de resposta de recomendação."""
    restaurant: RestaurantResponse
    similarity_score: float = Field(ge=0.0, le=1.0)
    insight: Optional[str] = None
    generated_at: datetime

