"""create assignments table

Revision ID: 004
Revises: 003
Create Date: 2026-06-14
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import UUID

revision: str = "004"
down_revision: Union[str, None] = "003"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "assignments",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "project_id",
            UUID(as_uuid=True),
            sa.ForeignKey("projects.id"),
            nullable=False,
        ),
        sa.Column(
            "resource_id",
            UUID(as_uuid=True),
            sa.ForeignKey("resources.id"),
            nullable=False,
        ),
        sa.Column("allocation_pct", sa.Integer(), nullable=False),
        sa.Column("billability_pct", sa.Integer(), nullable=False, server_default="0"),
        sa.Column(
            "is_shadow",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("false"),
        ),
        sa.Column("project_designation", sa.String(100), nullable=True),
        sa.Column("project_expertise", sa.String(100), nullable=True),
        sa.Column("billing_rate", sa.Numeric(10, 2), nullable=True),
        sa.Column("start_date", sa.Date(), nullable=False),
        sa.Column("end_date", sa.Date(), nullable=True),
        sa.Column("status", sa.String(20), nullable=False, server_default="ACTIVE"),
        sa.Column("released_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.CheckConstraint(
            "allocation_pct >= 1 AND allocation_pct <= 100",
            name="ck_allocation_pct_range",
        ),
        sa.CheckConstraint(
            "billability_pct >= 0 AND billability_pct <= 100",
            name="ck_billability_pct_range",
        ),
    )

    op.create_index("ix_assignments_project_id", "assignments", ["project_id"])
    op.create_index("ix_assignments_resource_id", "assignments", ["resource_id"])
    op.create_index("ix_assignments_status", "assignments", ["status"])
    op.create_index("ix_assignments_end_date", "assignments", ["end_date"])

    # Partial unique index: one ACTIVE assignment per (resource_id, project_id)
    op.execute(
        "CREATE UNIQUE INDEX uq_active_assignment_per_resource_project "
        "ON assignments (resource_id, project_id) "
        "WHERE status = 'ACTIVE'"
    )


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS uq_active_assignment_per_resource_project")
    op.drop_index("ix_assignments_end_date")
    op.drop_index("ix_assignments_status")
    op.drop_index("ix_assignments_resource_id")
    op.drop_index("ix_assignments_project_id")
    op.drop_table("assignments")
