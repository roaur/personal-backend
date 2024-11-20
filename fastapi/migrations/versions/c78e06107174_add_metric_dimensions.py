"""add metric dimensions

Revision ID: c78e06107174
Revises: da8fa24c771e
Create Date: 2024-11-19 08:33:26.886998

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'c78e06107174'
down_revision: Union[str, None] = 'da8fa24c771e'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('metric',
    sa.Column('metric_id', sa.Integer(), nullable=False, autoincrement=True),
    sa.Column('metric_name', sa.Text(), nullable=False),
    sa.Column('metric_description', sa.Text(), nullable=True),
    sa.PrimaryKeyConstraint('metric_id'),
    sa.UniqueConstraint('metric_description'),
    sa.UniqueConstraint('metric_name'),
    schema='chess'
    )
    op.create_table('game_metric',
    sa.Column('game_id', sa.Text(), nullable=False),
    sa.Column('metric_id', sa.Integer(), nullable=False),
    sa.Column('metric_value', sa.Numeric(), nullable=True),
    sa.ForeignKeyConstraint(['game_id'], ['chess.games.game_id'], ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['metric_id'], ['chess.metric.metric_id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('game_id', 'metric_id'),
    schema='chess'
    )
    op.drop_table('dag_metadata')
    # ### end Alembic commands ###

    op.execute("""
        INSERT INTO chess.metric (metric_name, metric_description)
        VALUES 
            ('queen_trade', 'Whether queens were traded'),
            ('castling', 'Type of castling performed');
    """)


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('dag_metadata',
    sa.Column('id', sa.INTEGER(), autoincrement=True, nullable=False),
    sa.Column('dag_name', sa.TEXT(), autoincrement=False, nullable=False),
    sa.Column('last_match_time', sa.BIGINT(), autoincrement=False, nullable=False),
    sa.PrimaryKeyConstraint('id', name='dag_metadata_pkey'),
    sa.UniqueConstraint('dag_name', name='dag_metadata_dag_name_key')
    )
    op.drop_table('game_metric', schema='chess')
    op.drop_table('metric', schema='chess')
    # ### end Alembic commands ###
