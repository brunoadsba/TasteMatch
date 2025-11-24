"""
Configurações da aplicação usando Pydantic Settings.
Gerencia variáveis de ambiente e configurações.
"""

from pydantic_settings import BaseSettings
from pydantic import Field
from typing import Optional


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
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True


# Instância global de configurações
settings = Settings()

