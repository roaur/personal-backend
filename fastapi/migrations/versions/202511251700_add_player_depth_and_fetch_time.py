"""add player depth and fetch time

Revision ID: 202511251700
Revises: 202411190833
Create Date: 2025-11-25 17:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '202511251700'
down_revision: Union[str, None] = '202411190833'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('players', sa.Column('last_fetched_at', sa.TIMESTAMP(timezone=True), nullable=True), schema='chess')
    op.add_column('players', sa.Column('depth', sa.Integer(), nullable=True), schema='chess')


def downgrade() -> None:
    op.drop_column('players', 'depth', schema='chess')
    op.drop_column('players', 'last_fetched_at', schema='chess')
