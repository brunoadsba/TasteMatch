"""
Configuração base do SQLAlchemy.
Define engine, session e Base declarativa.
"""

import os
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from app.config import settings

# Normalizar DATABASE_URL: converter postgres:// para postgresql://
# SQLAlchemy 2.0 requer postgresql:// (não postgres://)
database_url = settings.DATABASE_URL
if database_url.startswith("postgres://"):
    database_url = database_url.replace("postgres://", "postgresql://", 1)

# Configuração explícita é melhor que implícita (12-factor app)
# Definir variável de ambiente: DB_PROVIDER=supabase
IS_SUPABASE = os.getenv("DB_PROVIDER", "").lower() == "supabase"

# Configurar connect_args com SSL e keepalives para Supabase
connect_args = {}
if IS_SUPABASE:
    connect_args = {
        "sslmode": "require",
        "keepalives": 1,
        "keepalives_idle": 30,
        "keepalives_interval": 10,
        "keepalives_count": 5,
        # Se usar Supabase Transaction Pooler (porta 6543) com alguns drivers,
        # pode ser necessário desativar prepared statements:
        # "prepare_threshold": None
    }
elif "sqlite" in database_url:
    connect_args["check_same_thread"] = False

# Pool otimizado para Supabase (mais conexões disponíveis)
# Supabase aguenta mais conexões, aproveite
# Em Transaction Mode, evite overflow agressivo
if IS_SUPABASE:
    pool_size = 20
    max_overflow = 0  # Evitar overflow agressivo em Transaction Mode
    pool_recycle = 300  # Reciclar conexões mais rápido no pooler
else:
    # Pool conservador para ambiente com 1GB de memória (Fly.io)
    # 2 workers * (4 + 2) = máximo 12 conexões
    pool_size = 4
    max_overflow = 2
    pool_recycle = 1800  # Reciclar conexões após 30min

# Criar engine do SQLAlchemy
engine = create_engine(
    database_url,
    connect_args=connect_args,
    echo=settings.DEBUG,  # Log de queries SQL em modo debug
    pool_size=pool_size,
    max_overflow=max_overflow,
    pool_recycle=pool_recycle,
    pool_pre_ping=True,  # Verificar conexão antes de usar (vital para cloud)
    pool_timeout=10,  # Falhar rápido (10s) se banco estiver cheio
)

# Session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base declarativa para modelos
Base = declarative_base()


def get_db():
    """
    Dependency para obter sessão do banco de dados.
    Usado com FastAPI Depends().
    
    Yields:
        Session: Sessão do banco de dados
    
    Note:
        pool_pre_ping=True no engine já verifica conexão automaticamente.
        Erros de conexão serão tratados quando ocorrerem durante o uso da sessão.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

