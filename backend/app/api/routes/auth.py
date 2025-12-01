"""
Endpoints de autenticação: registro e login de usuários.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.database.base import get_db
from app.database.crud import get_user_by_email, create_user
from app.models.user import UserCreate, UserResponse
from app.core.security import (
    get_password_hash,
    verify_password,
    create_access_token
)
from app.core.logging_config import get_logger
from pydantic import BaseModel

logger = get_logger(__name__)
router = APIRouter(prefix="/auth", tags=["autenticação"])


class TokenResponse(BaseModel):
    """Resposta com token JWT e informações do usuário."""
    user: UserResponse
    token: str


class LoginRequest(BaseModel):
    """Requisição de login."""
    email: str
    password: str


@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
def register(
    user_data: UserCreate,
    db: Session = Depends(get_db)
):
    """
    Registra um novo usuário no sistema.
    
    Args:
        user_data: Dados do novo usuário (email, name, password)
        db: Sessão do banco de dados
        
    Returns:
        TokenResponse: Usuário criado e token JWT
        
    Raises:
        HTTPException: Se o email já existir ou dados inválidos
    """
    # Verificar se email já existe
    try:
        existing_user = get_user_by_email(db, email=user_data.email)
        if existing_user:
            logger.warning(
                "Tentativa de registro com email já cadastrado",
                extra={"email": user_data.email}
            )
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email já cadastrado. Use outro email ou faça login."
            )
    except Exception as e:
        # Se houver erro ao verificar (ex: banco indisponível), logar e relançar
        logger.error(
            f"Erro ao verificar email existente: {type(e).__name__}: {str(e)}",
            extra={"email": user_data.email}
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erro ao processar registro. Tente novamente."
        )
    
    # Hash da senha
    password_hash = get_password_hash(user_data.password)
    
    # Criar usuário
    db_user = create_user(db, user_data, password_hash)
    
    # Gerar token JWT
    token_data = {
        "sub": str(db_user.id),  # subject = user_id (deve ser string)
        "email": db_user.email
    }
    token = create_access_token(data=token_data)
    
    logger.info(
        "Usuário registrado com sucesso",
        extra={"user_id": db_user.id, "email": db_user.email}
    )
    
    return TokenResponse(
        user=UserResponse.model_validate(db_user),
        token=token
    )


@router.post("/login", response_model=TokenResponse)
def login(
    login_data: LoginRequest,
    db: Session = Depends(get_db)
):
    """
    Autentica um usuário existente e retorna token JWT.
    
    Args:
        login_data: Email e senha do usuário
        db: Sessão do banco de dados
        
    Returns:
        TokenResponse: Usuário autenticado e token JWT
        
    Raises:
        HTTPException: Se as credenciais forem inválidas ou banco indisponível
    """
    # Buscar usuário por email
    user = get_user_by_email(db, email=login_data.email)
    if not user:
        logger.warning(
            "Tentativa de login com email não cadastrado",
            extra={"email": login_data.email}
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Email ou senha incorretos",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Verificar senha
    if not verify_password(login_data.password, user.password_hash):
        logger.warning(
            "Tentativa de login com senha incorreta",
            extra={"user_id": user.id, "email": user.email}
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Email ou senha incorretos",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Gerar token JWT
    token_data = {
        "sub": str(user.id),  # subject = user_id (deve ser string)
        "email": user.email
    }
    token = create_access_token(data=token_data)
    
    logger.info(
        "Login realizado com sucesso",
        extra={"user_id": user.id, "email": user.email}
    )
    
    return TokenResponse(
        user=UserResponse.model_validate(user),
        token=token
    )

