"""
Modelos Pydantic para validação de dados de usuário.
"""

from pydantic import BaseModel, EmailStr
from datetime import datetime
from typing import Optional


class UserBase(BaseModel):
    """Modelo base de usuário."""
    email: EmailStr
    name: str


class UserCreate(UserBase):
    """Modelo para criação de usuário."""
    password: str


class UserResponse(UserBase):
    """Modelo de resposta de usuário (sem senha)."""
    id: int
    created_at: datetime
    
    class Config:
        from_attributes = True

