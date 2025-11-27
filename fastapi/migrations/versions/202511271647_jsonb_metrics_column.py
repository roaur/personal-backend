"""jsonb metrics column

Revision ID: 2cd8b9959866
Revises: 202511251700
Create Date: 2025-11-27 16:47:32.017060

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB


# revision identifiers, used by Alembic.
revision: str = '2cd8b9959866'
down_revision: Union[str, None] = '202511251700'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table('game_metrics',
    sa.Column('game_id', sa.Text(), nullable=False),
    sa.Column('metrics', JSONB(), nullable=False),
    sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
    sa.PrimaryKeyConstraint('id', name='game_metrics_pkey'),
    sa.UniqueConstraint('game_id', name='uq_game_id'),
    schema='chess'
    )

    op.execute("DROP TABLE IF EXISTS chess.game_metric")
    op.execute("DROP TABLE IF EXISTS chess.game_features")
    op.execute("DROP TABLE IF EXISTS chess.dag_metadata")


def downgrade() -> None:
    op.create_table('dag_metadata',
    sa.Column('id', sa.INTEGER(), autoincrement=True, nullable=False),
    sa.Column('dag_name', sa.TEXT(), autoincrement=False, nullable=False),
    sa.Column('last_match_time', sa.BIGINT(), autoincrement=False, nullable=False),
    sa.PrimaryKeyConstraint('id', name='dag_metadata_pkey'),
    sa.UniqueConstraint('dag_name', name='dag_metadata_dag_name_key'),
    schema='chess'
    )
    op.drop_table('game_metrics', schema='chess')

    op.create_table('game_metric',
    sa.Column('game_id', sa.Text(), nullable=False),
    sa.Column('metric_id', sa.Integer(), nullable=False),
    sa.Column('metric_value', sa.Numeric(), nullable=True),
    sa.ForeignKeyConstraint(['game_id'], ['chess.games.game_id'], ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['metric_id'], ['chess.metric.metric_id'], ondelete='CASCADE'),
    schema='chess'
    )

    op.create_table('game_features',
    sa.Column('game_id', sa.Text(), nullable=False),
    sa.Column('feature_id', sa.Integer(), nullable=False),
    sa.Column('feature_value', sa.Numeric(), nullable=True),
    sa.ForeignKeyConstraint(['game_id'], ['chess.games.game_id'], ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['feature_id'], ['chess.feature.feature_id'], ondelete='CASCADE'),
    schema='chess'
    )
