"""
Configuração base do SQLAlchemy.
Define engine, session e Base declarativa.
"""

from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from app.config import settings

# Normalizar DATABASE_URL: converter postgres:// para postgresql://
# SQLAlchemy 2.0 requer postgresql:// (não postgres://)
database_url = settings.DATABASE_URL
if database_url.startswith("postgres://"):
    database_url = database_url.replace("postgres://", "postgresql://", 1)

# Criar engine do SQLAlchemy
# Pool otimizado para 1GB: 2 workers * (4 + 2) = máximo 12 conexões
# Total máximo: 12 conexões (dentro do limite de 20 do Postgres)
engine = create_engine(
    database_url,
    connect_args={"check_same_thread": False} if "sqlite" in database_url else {},
    echo=settings.DEBUG,  # Log de queries SQL em modo debug
    # Pool conservador para ambiente com 1GB de memória
    pool_size=4,              # 4 conexões fixas por worker
    max_overflow=2,           # 2 extras em picos (total: 6 por worker)
    pool_recycle=1800,        # Reciclar conexões após 30min (evita stale connections)
    pool_pre_ping=True,       # Verificar conexão antes de usar (vital para cloud)
    pool_timeout=10,          # Falhar rápido (10s) se banco estiver cheio
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
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

