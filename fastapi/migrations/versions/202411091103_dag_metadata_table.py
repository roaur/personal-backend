"""dag metadata table

Revision ID: 76fc0b4316a2
Revises: d38eed468cb1
Create Date: 2024-11-09 11:03:40.202581

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '202411091103'
down_revision: Union[str, None] = '202410192037'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "dag_metadata",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("dag_name", sa.Text, nullable=False, unique=True),
        sa.Column("last_match_time", sa.BigInteger, nullable=False),
        sa.PrimaryKeyConstraint("id")
    )


def downgrade() -> None:
    # drop the table
    op.drop_table("dag_metadata")
