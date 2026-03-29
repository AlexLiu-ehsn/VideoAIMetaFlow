"""新增 analysis_duration 欄位

Revision ID: 002
Revises: 001
Create Date: 2026-03-29

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "002"
down_revision: Union[str, None] = "001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("videos", sa.Column("analysis_duration", sa.Float(), nullable=True))


def downgrade() -> None:
    op.drop_column("videos", "analysis_duration")
