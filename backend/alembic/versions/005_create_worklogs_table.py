"""create worklogs table

Revision ID: 005
Revises: 004
Create Date: 2026-06-15
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import UUID

revision: str = "005"
down_revision: Union[str, None] = "004"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "worklogs",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "resource_id",
            UUID(as_uuid=True),
            sa.ForeignKey("resources.id"),
            nullable=False,
        ),
        sa.Column(
            "project_id",
            UUID(as_uuid=True),
            sa.ForeignKey("projects.id"),
            nullable=False,
        ),
        sa.Column("log_date", sa.Date(), nullable=False),
        sa.Column("hours", sa.Numeric(4, 1), nullable=False),
        sa.Column("note", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
    )

    op.create_index("ix_worklogs_resource_id", "worklogs", ["resource_id"])
    op.create_index("ix_worklogs_project_id", "worklogs", ["project_id"])
    op.create_index("ix_worklogs_log_date", "worklogs", ["log_date"])
    op.create_unique_constraint(
        "uq_worklog_resource_project_date",
        "worklogs",
        ["resource_id", "project_id", "log_date"],
    )


def downgrade() -> None:
    op.drop_constraint("uq_worklog_resource_project_date", "worklogs", type_="unique")
    op.drop_index("ix_worklogs_log_date")
    op.drop_index("ix_worklogs_project_id")
    op.drop_index("ix_worklogs_resource_id")
    op.drop_table("worklogs")
