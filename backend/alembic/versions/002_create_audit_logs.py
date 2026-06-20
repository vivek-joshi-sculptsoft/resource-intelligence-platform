"""create audit_logs table

Revision ID: 002
Revises: 001
Create Date: 2026-06-10
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "002"
down_revision: Union[str, None] = "001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "audit_logs",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("entity_type", sa.String(50), nullable=False),
        sa.Column(
            "entity_id", sa.dialects.postgresql.UUID(as_uuid=True), nullable=False
        ),
        sa.Column(
            "action",
            sa.Enum("CREATE", "UPDATE", "DELETE", name="audit_action_enum"),
            nullable=False,
        ),
        sa.Column("field_name", sa.String(100), nullable=True),
        sa.Column("old_value", sa.Text(), nullable=True),
        sa.Column("new_value", sa.Text(), nullable=True),
        sa.Column(
            "changed_by", sa.dialects.postgresql.UUID(as_uuid=True), nullable=False
        ),
        sa.Column(
            "changed_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column("metadata", sa.dialects.postgresql.JSONB(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_index(
        "ix_audit_logs_entity",
        "audit_logs",
        ["entity_type", "entity_id"],
    )
    op.create_index("ix_audit_logs_changed_by", "audit_logs", ["changed_by"])
    op.create_index("ix_audit_logs_changed_at", "audit_logs", ["changed_at"])
    op.create_index(
        "ix_audit_logs_entity_type_changed_at",
        "audit_logs",
        ["entity_type", "changed_at"],
    )


def downgrade() -> None:
    op.drop_index("ix_audit_logs_entity_type_changed_at")
    op.drop_index("ix_audit_logs_changed_at")
    op.drop_index("ix_audit_logs_changed_by")
    op.drop_index("ix_audit_logs_entity")
    op.drop_table("audit_logs")
    sa.Enum(name="audit_action_enum").drop(op.get_bind(), checkfirst=True)
