"""add_composite_indexes_for_performance

Revision ID: 5d0cda723f59
Revises: f9a885ec7494
Create Date: 2025-01-27 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '5d0cda723f59'
down_revision: Union[str, None] = 'f9a885ec7494'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Índice composto para orders: user_id + order_date DESC (otimiza histórico ordenado)
    op.create_index(
        'ix_orders_user_id_order_date_desc',
        'orders',
        ['user_id', sa.text('order_date DESC')],
        unique=False
    )
    
    # Índice composto para restaurants: cuisine_type + rating DESC (otimiza filtros + ordenação)
    op.create_index(
        'ix_restaurants_cuisine_type_rating_desc',
        'restaurants',
        ['cuisine_type', sa.text('rating DESC')],
        unique=False
    )
    
    # Índice composto para recommendations: user_id + generated_at DESC (otimiza cache de recomendações)
    op.create_index(
        'ix_recommendations_user_id_generated_at_desc',
        'recommendations',
        ['user_id', sa.text('generated_at DESC')],
        unique=False
    )


def downgrade() -> None:
    # Remover índices na ordem inversa
    op.drop_index('ix_recommendations_user_id_generated_at_desc', table_name='recommendations')
    op.drop_index('ix_restaurants_cuisine_type_rating_desc', table_name='restaurants')
    op.drop_index('ix_orders_user_id_order_date_desc', table_name='orders')
