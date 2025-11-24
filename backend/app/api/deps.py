"""
Dependências compartilhadas do FastAPI para autenticação e banco de dados.
"""

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from app.database.base import get_db
from app.database.crud import get_user
from app.core.security import decode_access_token
from app.database.models import User

# Security scheme para Bearer Token
security = HTTPBearer()


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
) -> User:
    """
    Dependência para obter o usuário autenticado via JWT.
    
    Args:
        credentials: Credenciais HTTPBearer (contém o token JWT)
        db: Sessão do banco de dados
        
    Returns:
        User: Usuário autenticado
        
    Raises:
        HTTPException: Se o token for inválido ou o usuário não existir
    """
    token = credentials.credentials
    
    # Decodificar token JWT
    payload = decode_access_token(token)
    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token inválido ou expirado",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Extrair user_id do payload (sub = subject)
    # sub é armazenado como string, converter para int
    user_id_str = payload.get("sub")
    if user_id_str is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token inválido: user_id não encontrado",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    try:
        user_id: int = int(user_id_str)
    except (ValueError, TypeError):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token inválido: user_id inválido",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Buscar usuário no banco
    user = get_user(db, user_id=user_id)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Usuário não encontrado",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    return user

