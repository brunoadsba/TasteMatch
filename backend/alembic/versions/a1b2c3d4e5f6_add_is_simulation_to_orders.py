"""add_is_simulation_to_orders

Revision ID: a1b2c3d4e5f6
Revises: 5d0cda723f59
Create Date: 2025-11-25 15:45:44.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a1b2c3d4e5f6'
down_revision: Union[str, None] = '5d0cda723f59'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Adicionar coluna is_simulation à tabela orders
    op.add_column(
        'orders',
        sa.Column('is_simulation', sa.Boolean(), nullable=False, server_default='false')
    )


def downgrade() -> None:
    # Remover coluna is_simulation
    op.drop_column('orders', 'is_simulation')

