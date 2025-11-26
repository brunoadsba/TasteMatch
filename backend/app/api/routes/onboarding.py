"""
Endpoints da API para onboarding gamificado.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database.base import get_db
from app.api.deps import get_current_user
from app.database.models import User
from app.models.onboarding import OnboardingRequest, OnboardingResponse
from app.core.onboarding_service import complete_onboarding
from app.core.logging_config import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/api/onboarding", tags=["onboarding"])


@router.post("/complete", response_model=OnboardingResponse)
def complete_user_onboarding(
    request: OnboardingRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Completa o onboarding do usuário gerando vetor sintético baseado nas escolhas.
    
    Este endpoint permite que usuários novos criem um perfil de sabor através de
    seleções simples (culinárias, preço, restrições), gerando um vetor sintético
    que permite recomendações personalizadas desde o primeiro acesso.
    
    Args:
        request: Dados do onboarding (culinárias, preço, restrições)
        current_user: Usuário autenticado (via JWT)
        db: Sessão do banco de dados
        
    Returns:
        OnboardingResponse: Confirmação de sucesso ou falha
        
    Raises:
        HTTPException: Se houver erro ao processar onboarding
    """
    try:
        logger.info(
            "Iniciando onboarding",
            extra={
                "user_id": current_user.id,
                "cuisines_count": len(request.selected_cuisines),
                "has_price_preference": request.price_preference is not None
            }
        )
        
        # Completar onboarding
        success = complete_onboarding(
            user_id=current_user.id,
            selected_cuisines=request.selected_cuisines,
            price_preference=request.price_preference,
            dietary_restrictions=request.dietary_restrictions,
            db=db
        )
        
        if success:
            logger.info(
                "Onboarding completado com sucesso",
                extra={"user_id": current_user.id}
            )
            return OnboardingResponse(
                success=True,
                message="Onboarding completado! Seu perfil de sabor foi criado e você já pode receber recomendações personalizadas.",
                has_synthetic_vector=True
            )
        else:
            logger.warning(
                "Onboarding não pôde ser completado (vetor sintético não gerado)",
                extra={"user_id": current_user.id}
            )
            return OnboardingResponse(
                success=False,
                message="Não foi possível gerar seu perfil de sabor no momento. Você ainda receberá recomendações baseadas em popularidade.",
                has_synthetic_vector=False
            )
            
    except Exception as e:
        logger.error(
            "Erro ao completar onboarding",
            extra={"user_id": current_user.id, "error": str(e)},
            exc_info=True
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro ao processar onboarding: {str(e)}"
        )

