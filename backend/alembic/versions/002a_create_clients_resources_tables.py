"""create clients, resources, resource_tags tables

Revision ID: 002a
Revises: 002
Create Date: 2026-06-20
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID

revision: str = "002a"
down_revision: Union[str, None] = "002"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "clients",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("name", sa.String(255), unique=True, nullable=False),
        sa.Column("industry", sa.String(100), nullable=True),
        sa.Column("contact_name", sa.String(255), nullable=True),
        sa.Column("contact_email", sa.String(255), nullable=True),
        sa.Column("contact_phone", sa.String(20), nullable=True),
        sa.Column("engagement_start_date", sa.Date(), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
    )
    op.create_index("ix_clients_is_active", "clients", ["is_active"])
    op.create_index("ix_clients_name", "clients", ["name"])

    op.create_table(
        "resources",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("employee_id", sa.String(50), unique=True, nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("designation", sa.String(100), nullable=False),
        sa.Column("technical_expertise", sa.String(100), nullable=True),
        sa.Column("date_of_joining", sa.Date(), nullable=True),
        sa.Column(
            "reporting_manager_id",
            UUID(as_uuid=True),
            sa.ForeignKey("resources.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("loaded_cost_monthly", sa.Numeric(15, 2), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
    )
    op.create_index("ix_resources_reporting_manager_id", "resources", ["reporting_manager_id"])
    op.create_index("ix_resources_employee_id", "resources", ["employee_id"])
    op.create_index("ix_resources_is_active", "resources", ["is_active"])
    op.create_index("ix_resources_designation", "resources", ["designation"])

    op.create_table(
        "resource_tags",
        sa.Column(
            "resource_id",
            UUID(as_uuid=True),
            sa.ForeignKey("resources.id", ondelete="CASCADE"),
            primary_key=True,
        ),
        sa.Column("tag", sa.String(100), primary_key=True),
    )
    op.create_index("ix_resource_tags_tag", "resource_tags", ["tag"])


def downgrade() -> None:
    op.drop_table("resource_tags")
    op.drop_table("resources")
    op.drop_table("clients")
