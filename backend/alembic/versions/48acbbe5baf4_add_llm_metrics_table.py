"""add_llm_metrics_table

Revision ID: 48acbbe5baf4
Revises: cf593ece42df
Create Date: 2025-01-XX XX:XX:XX.XXXXXX

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = '48acbbe5baf4'
down_revision: Union[str, None] = 'cf593ece42df'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Criar tabela llm_metrics
    op.create_table(
        'llm_metrics',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=True),  # Nullable para métricas globais
        sa.Column('model', sa.String(length=100), nullable=False),
        sa.Column('question', sa.Text(), nullable=True),  # Opcional, pode ser None por privacidade
        sa.Column('input_tokens', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('output_tokens', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('total_tokens', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('latency_ms', sa.Integer(), nullable=True),
        sa.Column('estimated_cost_usd', sa.DECIMAL(precision=10, scale=6), nullable=False, server_default='0.0'),
        sa.Column('response_length', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('error', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_llm_metrics_id'), 'llm_metrics', ['id'], unique=False)
    op.create_index(op.f('ix_llm_metrics_user_id'), 'llm_metrics', ['user_id'], unique=False)
    op.create_index(op.f('ix_llm_metrics_created_at'), 'llm_metrics', ['created_at'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_llm_metrics_created_at'), table_name='llm_metrics')
    op.drop_index(op.f('ix_llm_metrics_user_id'), table_name='llm_metrics')
    op.drop_index(op.f('ix_llm_metrics_id'), table_name='llm_metrics')
    op.drop_table('llm_metrics')

