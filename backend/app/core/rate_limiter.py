"""
Rate Limiting para Chef Virtual
Implementa rate limiting para respeitar limites da Groq API (30 RPM)
"""

from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from fastapi import Request
from typing import Optional
from app.database.models import User

# Criar limiter global (por IP)
limiter = Limiter(
    key_func=get_remote_address,
    default_limits=["30/minute"],  # 30 requisições por minuto (limite Groq)
    storage_uri="memory://",  # Em memória (para produção, usar Redis: "redis://localhost:6379")
    strategy="fixed-window"  # Janela fixa de 1 minuto
)


def get_user_id_for_rate_limit(request: Request) -> str:
    """
    Obtém identificador para rate limiting baseado no usuário autenticado ou IP
    
    Args:
        request: Requisição FastAPI
    
    Returns:
        String identificadora (user:{id} ou IP)
    """
    try:
        # Tentar obter usuário autenticado do request state
        # O usuário pode ser adicionado via middleware ou dependency
        if hasattr(request.state, 'current_user'):
            user: Optional[User] = request.state.current_user
            if user and hasattr(user, 'id'):
                return f"user:{user.id}"
    except (AttributeError, KeyError):
        pass
    
    # Fallback para IP do cliente
    return get_remote_address(request)


# Limiter específico para endpoints autenticados (por usuário)
user_limiter = Limiter(
    key_func=get_user_id_for_rate_limit,
    default_limits=["30/minute"],  # 30 requisições por minuto por usuário
    storage_uri="memory://",  # Em memória (para produção, usar Redis)
    strategy="fixed-window"  # Janela fixa de 1 minuto
)

