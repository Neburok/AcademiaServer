"""crear tabla notas

Revision ID: 0001
Revises:
Create Date: 2026-03-07 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "0001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "notas",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("title", sa.String(), nullable=True),
        sa.Column("type", sa.String(), nullable=True),
        sa.Column("source", sa.String(), nullable=True),
        sa.Column("schema_version", sa.String(), nullable=True),
        sa.Column("content_hash", sa.String(), nullable=True),
        sa.Column("created_at", sa.String(), nullable=False),
        sa.Column("tags", sa.JSON(), nullable=True),
        sa.Column("links", sa.JSON(), nullable=True),
        sa.Column("topics", sa.JSON(), nullable=True),
        sa.Column("priority", sa.String(), nullable=True),
        sa.Column("summary", sa.Text(), nullable=True),
        sa.Column("reminder_datetime", sa.String(), nullable=True),
        sa.Column("reminded", sa.Boolean(), nullable=True),
        sa.Column("embedding", sa.LargeBinary(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_notas_content_hash"), "notas", ["content_hash"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_notas_content_hash"), table_name="notas")
    op.drop_table("notas")
