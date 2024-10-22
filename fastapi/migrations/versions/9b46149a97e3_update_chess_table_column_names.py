"""Update chess table column names

Revision ID: 9b46149a97e3
Revises: d38eed468cb1
Create Date: 2024-10-21 21:00:35.729818

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '9b46149a97e3'
down_revision: Union[str, None] = 'd38eed468cb1'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade():
    # Rename columns in the games table
    op.alter_column('games', 'lichess_game_id', new_column_name='id', schema='chess')
    op.alter_column('games', 'created_at', new_column_name='createdAt', schema='chess')
    op.alter_column('games', 'last_move_at', new_column_name='lastMoveAt', schema='chess')

def downgrade():
    # Revert column name changes
    op.alter_column('games', 'id', new_column_name='lichess_game_id', schema='chess')
    op.alter_column('games', 'createdAt', new_column_name='created_at', schema='chess')
    op.alter_column('games', 'lastMoveAt', new_column_name='last_move_at', schema='chess')
