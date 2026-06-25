"""create non_human_costs table

Revision ID: 007
Revises: 006
Create Date: 2026-06-25
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import UUID

revision: str = "007"
down_revision: Union[str, None] = "006"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "non_human_costs",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "project_id",
            UUID(as_uuid=True),
            sa.ForeignKey("projects.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("description", sa.String(500), nullable=False),
        sa.Column("category", sa.String(30), nullable=False),
        sa.Column("amount", sa.Numeric(15, 2), nullable=False),
        sa.Column("currency", sa.String(3), nullable=False, server_default="INR"),
        sa.Column(
            "exchange_rate", sa.Numeric(10, 4), nullable=False, server_default=sa.text("1.0")
        ),
        sa.Column("amount_inr", sa.Numeric(15, 2), nullable=False),
        sa.Column("cost_date", sa.Date(), nullable=False),
        sa.Column("is_recurring", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("recurring_end_date", sa.Date(), nullable=True),
        sa.Column(
            "created_by",
            UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
    )

    op.create_index("ix_non_human_costs_project_id", "non_human_costs", ["project_id"])
    op.create_index("ix_non_human_costs_category", "non_human_costs", ["category"])
    op.create_index("ix_non_human_costs_is_recurring", "non_human_costs", ["is_recurring"])
    op.create_index("ix_non_human_costs_cost_date", "non_human_costs", ["cost_date"])


def downgrade() -> None:
    op.drop_index("ix_non_human_costs_cost_date")
    op.drop_index("ix_non_human_costs_is_recurring")
    op.drop_index("ix_non_human_costs_category")
    op.drop_index("ix_non_human_costs_project_id")
    op.drop_table("non_human_costs")
