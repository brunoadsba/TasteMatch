"""
Configurações da aplicação usando Pydantic Settings.
Gerencia variáveis de ambiente e configurações.
"""

import os
from pathlib import Path
from pydantic_settings import BaseSettings
from pydantic import Field
from typing import Optional


def get_env_file_path() -> str:
    """
    Retorna o caminho do arquivo .env.
    Procura primeiro na raiz do projeto, depois no diretório atual.
    """
    # Caminho do arquivo config.py
    current_file = Path(__file__)
    # Raiz do projeto (2 níveis acima: backend/app/config.py -> raiz)
    project_root = current_file.parent.parent.parent
    root_env = project_root / ".env"
    
    # Se existe .env na raiz, usar ele
    if root_env.exists():
        return str(root_env)
    
    # Caso contrário, procurar no diretório atual
    return ".env"


class Settings(BaseSettings):
    """Configurações da aplicação."""
    
    # Aplicação
    APP_NAME: str = Field(default="TasteMatch", description="Nome da aplicação")
    ENVIRONMENT: str = Field(default="development", description="Ambiente de execução")
    DEBUG: bool = Field(default=True, description="Modo debug")
    SECRET_KEY: str = Field(
        default="change-this-secret-key-in-production-please",
        description="Chave secreta da aplicação (OBRIGATÓRIO em produção!)"
    )
    
    # Banco de Dados
    DATABASE_URL: str = Field(
        default="sqlite:///./tastematch.db",
        description="URL de conexão com o banco de dados"
    )
    
    # JWT
    JWT_SECRET_KEY: str = Field(
        default="change-this-jwt-secret-key-in-production-please",
        description="Chave secreta para JWT (OBRIGATÓRIO em produção!)"
    )
    JWT_ALGORITHM: str = Field(default="HS256", description="Algoritmo JWT")
    JWT_EXPIRATION_HOURS: int = Field(default=24, description="Horas até expiração do token")
    
    # Groq API (LLM)
    GROQ_API_KEY: Optional[str] = Field(default=None, description="API key do Groq")
    
    # OpenAI API (Opcional)
    OPENAI_API_KEY: Optional[str] = Field(default=None, description="API key do OpenAI (opcional)")
    
    # Embeddings
    EMBEDDING_MODEL: str = Field(
        default="sentence-transformers/all-MiniLM-L6-v2",
        description="Modelo de embeddings a ser usado"
    )
    
    class Config:
        env_file = get_env_file_path()
        env_file_encoding = "utf-8"
        case_sensitive = True
    
    @property
    def is_production(self) -> bool:
        """Retorna True se estiver em ambiente de produção."""
        return self.ENVIRONMENT.lower() == "production"
    
    def validate_production_settings(self):
        """Valida configurações críticas para produção."""
        if self.is_production:
            if self.DEBUG:
                raise ValueError("DEBUG deve ser False em produção!")
            if self.SECRET_KEY == "change-this-secret-key-in-production-please":
                raise ValueError("SECRET_KEY deve ser alterada em produção!")
            if self.JWT_SECRET_KEY == "change-this-jwt-secret-key-in-production-please":
                raise ValueError("JWT_SECRET_KEY deve ser alterada em produção!")
            if "sqlite" in self.DATABASE_URL.lower():
                raise ValueError("SQLite não deve ser usado em produção! Use PostgreSQL.")


# Instância global de configurações
settings = Settings()

