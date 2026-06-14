"""create projects table

Revision ID: 003
Revises: 002
Create Date: 2026-06-14
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import UUID

revision: str = "003"
down_revision: Union[str, None] = "002"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "projects",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column(
            "client_id",
            UUID(as_uuid=True),
            sa.ForeignKey("clients.id"),
            nullable=False,
        ),
        sa.Column("type", sa.String(50), nullable=False, server_default="TIME_AND_MATERIAL"),
        sa.Column("billing_currency", sa.String(3), nullable=False, server_default="INR"),
        sa.Column("contract_value", sa.Numeric(15, 2), nullable=True),
        sa.Column("start_date", sa.Date(), nullable=True),
        sa.Column("contract_end_date", sa.Date(), nullable=True),
        sa.Column(
            "dm_id",
            UUID(as_uuid=True),
            sa.ForeignKey("resources.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column(
            "pm_id",
            UUID(as_uuid=True),
            sa.ForeignKey("resources.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column(
            "worklog_enabled",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("false"),
        ),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("status", sa.String(20), nullable=False, server_default="ACTIVE"),
        sa.Column(
            "is_active",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("true"),
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
    )

    op.create_index("ix_projects_client_id", "projects", ["client_id"])
    op.create_index("ix_projects_dm_id", "projects", ["dm_id"])
    op.create_index("ix_projects_pm_id", "projects", ["pm_id"])
    op.create_index("ix_projects_status", "projects", ["status"])


def downgrade() -> None:
    op.drop_index("ix_projects_status")
    op.drop_index("ix_projects_pm_id")
    op.drop_index("ix_projects_dm_id")
    op.drop_index("ix_projects_client_id")
    op.drop_table("projects")
