"""
Modelos Pydantic para onboarding gamificado.
"""

from pydantic import BaseModel, Field
from typing import List, Optional


class OnboardingRequest(BaseModel):
    """Request para completar onboarding."""
    selected_cuisines: List[str] = Field(
        ...,
        min_items=1,
        max_items=5,
        description="Lista de culinárias selecionadas (1-5)"
    )
    price_preference: Optional[str] = Field(
        None,
        description="Preferência de preço: 'low', 'medium', 'high'"
    )
    dietary_restrictions: Optional[List[str]] = Field(
        None,
        description="Restrições alimentares (ex: ['vegan', 'gluten-free'])"
    )


class OnboardingResponse(BaseModel):
    """Response após completar onboarding."""
    success: bool
    message: str
    has_synthetic_vector: bool = Field(
        ...,
        description="Indica se vetor sintético foi gerado e salvo"
    )

