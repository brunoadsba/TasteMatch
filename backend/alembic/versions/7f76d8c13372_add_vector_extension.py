"""add_vector_extension

Revision ID: 7f76d8c13372
Revises: a1b2c3d4e5f6
Create Date: 2025-11-28 12:35:25.696502

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '7f76d8c13372'
down_revision: Union[str, None] = 'a1b2c3d4e5f6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """
    Adiciona extensão vector do PostgreSQL para suporte a busca vetorial.
    Esta extensão é necessária para o PGVector usado pelo Chef Virtual.
    
    Nota: Se a extensão não estiver disponível no banco (ex: Fly Postgres sem pgvector),
    esta migration será marcada como aplicada mas a extensão não será criada.
    O sistema continuará funcionando sem busca vetorial otimizada no banco.
    """
    # Criar extensão vector (apenas PostgreSQL)
    # SQLite não suporta extensões, então verificamos se é PostgreSQL
    connection = op.get_bind()
    if connection.dialect.name == 'postgresql':
        # Verificar se extensão já existe antes de tentar criar
        try:
            result = connection.execute(
                sa.text("SELECT 1 FROM pg_extension WHERE extname = 'vector'")
            ).fetchone()
            if result:
                # Extensão já existe, nada a fazer
                import logging
                logger = logging.getLogger('alembic')
                logger.info("Extensão 'vector' já existe no banco")
                return
        except Exception:
            # Se não conseguir verificar, tentar criar mesmo assim
            pass
        
        # Tentar criar extensão em conexão separada com autocommit
        # Isso evita problemas com transações abortadas do Alembic
        try:
            from sqlalchemy import create_engine
            from app.config import settings
            
            # Criar conexão separada com autocommit
            db_url = settings.DATABASE_URL
            if db_url.startswith("postgres://"):
                db_url = db_url.replace("postgres://", "postgresql://", 1)
            
            # Criar engine temporário com autocommit
            temp_engine = create_engine(
                db_url,
                isolation_level="AUTOCOMMIT"
            )
            
            with temp_engine.connect() as temp_conn:
                temp_conn.execute(sa.text('CREATE EXTENSION IF NOT EXISTS vector'))
            
            temp_engine.dispose()
            
            import logging
            logger = logging.getLogger('alembic')
            logger.info("Extensão 'vector' criada com sucesso")
            
        except Exception as e:
            # Se a extensão não estiver disponível no banco, apenas logar warning
            # A migration será marcada como aplicada mesmo sem a extensão
            import logging
            logger = logging.getLogger('alembic')
            logger.warning(
                f"Extensão 'vector' não pôde ser criada: {str(e)[:200]}. "
                "O sistema continuará funcionando, mas sem busca vetorial otimizada no banco. "
                "Para habilitar, instale pgvector no PostgreSQL ou use um banco que suporte a extensão."
            )
            # Não re-raise a exceção - permite que a migration seja marcada como aplicada
            # A aplicação pode funcionar sem pgvector (usando busca em memória)
    # Se for SQLite, não faz nada (será ignorado silenciosamente)


def downgrade() -> None:
    """
    Remove extensão vector (apenas PostgreSQL).
    """
    connection = op.get_bind()
    if connection.dialect.name == 'postgresql':
        # Nota: DROP EXTENSION pode falhar se houver objetos dependentes
        # Em produção, verificar dependências antes de remover
        op.execute('DROP EXTENSION IF EXISTS vector CASCADE')

