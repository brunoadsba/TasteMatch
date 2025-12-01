"""
Alembic environment configuration.
"""

from logging.config import fileConfig
from sqlalchemy import pool
from alembic import context

# Importar configurações e modelos
import sys
from pathlib import Path

# Adicionar o diretório backend ao path
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

from app.config import settings
from app.database.base import Base
from app.database.models import User, Restaurant, Order, Recommendation, UserPreferences  # noqa

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

# Interpret the config file for Python logging.
# This line sets up loggers basically.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Normalizar DATABASE_URL: converter postgres:// para postgresql://
# SQLAlchemy 2.0 requer postgresql:// (não postgres://)
database_url = settings.DATABASE_URL
if database_url.startswith("postgres://"):
    database_url = database_url.replace("postgres://", "postgresql://", 1)

# Override sqlalchemy.url with settings from environment
# IMPORTANTE: Escapar % para evitar erro de interpolação do ConfigParser
# URLs com caracteres codificados (%23, %40, etc.) precisam ter % duplicado (%%) 
# para o ConfigParser não tentar fazer interpolação
database_url_escaped = database_url.replace("%", "%%")
config.set_main_option("sqlalchemy.url", database_url_escaped)

# Armazenar URL original para uso direto nas funções de migração
# (evita problemas com unescape do ConfigParser)
DATABASE_URL = database_url

# add your model's MetaData object here
# for 'autogenerate' support
target_metadata = Base.metadata

# other values from the config, defined by the needs of env.py,
# can be acquired:
# my_important_option = config.get_main_option("my_important_option")
# ... etc.


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode.

    This configures the context with just a URL
    and not an Engine, though an Engine is acceptable
    here as well.  By skipping the Engine creation
    we don't even need a DBAPI to be available.

    Calls to context.execute() here emit the given string to the
    script output.

    """
    # Usar URL original diretamente (sem passar pelo ConfigParser)
    url = DATABASE_URL
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode.

    In this scenario we need to create an Engine
    and associate a connection with the context.

    """
    # Usar URL original diretamente para criar engine (evita problemas com ConfigParser)
    from sqlalchemy import create_engine
    connectable = create_engine(
        DATABASE_URL,
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection, target_metadata=target_metadata
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()

