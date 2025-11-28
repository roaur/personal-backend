"""add gin index to game_metrics

Revision ID: f859aa21abf4
Revises: 2cd8b9959866
Create Date: 2025-11-28 10:48:13.226586

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'f859aa21abf4'
down_revision: Union[str, None] = '2cd8b9959866'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_index('ix_game_metrics_metrics', 'game_metrics', ['metrics'], unique=False, schema='chess', postgresql_using='gin')


def downgrade() -> None:
    op.drop_index('ix_game_metrics_metrics', table_name='game_metrics', schema='chess')
