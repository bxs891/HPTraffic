"""create example table

Revision ID: 0001_create_example_table
Revises:
Create Date: 2026-01-01 00:00:00
"""

from alembic import op
import sqlalchemy as sa


revision = "0001_create_example_table"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "example_records",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_example_records_id"), "example_records", ["id"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_example_records_id"), table_name="example_records")
    op.drop_table("example_records")
