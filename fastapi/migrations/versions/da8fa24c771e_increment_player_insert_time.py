"""increment player insert time

Revision ID: da8fa24c771e
Revises: 76fc0b4316a2
Create Date: 2024-11-13 08:00:52.578089

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'da8fa24c771e'
down_revision: Union[str, None] = '76fc0b4316a2'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        'players'
        , sa.Column(
            'insert_ts', 
            sa.BigInteger, 
            server_default=sa.text("extract(epoch from current_timestamp) * 1000")
        )
        , schema="chess"
    )


def downgrade() -> None:
    op.drop_column(
        'players'
        , 'ts_insert'
        , schema="chess"
    )
