"""
Endpoint para visualizar métricas de monitoramento LLM.
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional
from datetime import datetime, timedelta

from app.database.base import get_db
from app.api.deps import get_current_user
from app.database.models import User
from app.core.llm_monitoring import get_llm_metrics_summary
from app.core.logging_config import get_logger

router = APIRouter()
logger = get_logger(__name__)


@router.get("/llm/summary")
async def get_llm_metrics_summary_endpoint(
    days: int = Query(7, ge=1, le=90, description="Número de dias para considerar"),
    user_id: Optional[int] = Query(None, description="ID do usuário (opcional, apenas admin)"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Obtém resumo de métricas LLM.
    
    - **days**: Número de dias para considerar (1-90)
    - **user_id**: ID do usuário (opcional, apenas para admin ou próprio usuário)
    
    Retorna:
    - total_calls: Número total de chamadas
    - total_tokens: Total de tokens usados
    - total_cost_usd: Custo total estimado em USD
    - avg_latency_ms: Latência média em milissegundos
    - error_rate: Taxa de erro em porcentagem
    """
    # Se user_id especificado, verificar permissões
    target_user_id = None
    if user_id:
        # Por enquanto, apenas o próprio usuário pode ver suas métricas
        # Em produção, adicionar verificação de admin
        if user_id != current_user.id:
            raise HTTPException(
                status_code=403,
                detail="Você só pode ver suas próprias métricas"
            )
        target_user_id = user_id
    else:
        # Se não especificado, retornar métricas do usuário atual
        target_user_id = current_user.id
    
    try:
        summary = get_llm_metrics_summary(db, user_id=target_user_id, days=days)
        return {
            "user_id": target_user_id,
            "days": days,
            "summary": summary,
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }
    except Exception as e:
        logger.error(f"Erro ao obter resumo de métricas: {e}")
        raise HTTPException(
            status_code=500,
            detail="Erro ao obter métricas"
        )

