"""create auth tables: roles, role_permissions, users, system_config

Revision ID: 001
Revises: None
Create Date: 2026-06-10
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID

revision: str = "001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

access_level_enum = sa.Enum("NONE", "VIEW", "EDIT", name="access_level_enum")
scope_enum = sa.Enum("ALL", "OWN_PORTFOLIO", "SELF_ONLY", name="scope_enum")


def upgrade() -> None:
    access_level_enum.create(op.get_bind(), checkfirst=True)
    scope_enum.create(op.get_bind(), checkfirst=True)

    op.create_table(
        "roles",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("name", sa.String(100), unique=True, nullable=False),
        sa.Column("code", sa.String(20), unique=True, nullable=False),
        sa.Column("permission_level", sa.Integer, nullable=False),
        sa.Column("is_active", sa.Boolean, nullable=False, server_default=sa.text("true")),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
    )

    op.create_table(
        "role_permissions",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("role_id", UUID(as_uuid=True), sa.ForeignKey("roles.id"), nullable=False),
        sa.Column("data_type", sa.String(50), nullable=False),
        sa.Column("access_level", access_level_enum, nullable=False),
        sa.Column("scope", scope_enum, nullable=False, server_default="ALL"),
        sa.Column("is_configurable", sa.Boolean, nullable=False, server_default=sa.text("false")),
        sa.UniqueConstraint("role_id", "data_type", name="uq_role_data_type"),
    )
    op.create_index("ix_role_permissions_role_id", "role_permissions", ["role_id"])

    op.create_table(
        "users",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("email", sa.String(255), unique=True, nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("password_hash", sa.String(255), nullable=False),
        sa.Column("role_id", UUID(as_uuid=True), sa.ForeignKey("roles.id"), nullable=False),
        sa.Column("resource_id", UUID(as_uuid=True), nullable=True),
        sa.Column("is_active", sa.Boolean, nullable=False, server_default=sa.text("true")),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_users_role_id", "users", ["role_id"])
    op.create_index("ix_users_resource_id", "users", ["resource_id"])

    op.create_table(
        "system_config",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("key", sa.String(100), unique=True, nullable=False),
        sa.Column("value", sa.String(500), nullable=False),
        sa.Column("description", sa.String(500), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
    )


def downgrade() -> None:
    op.drop_table("system_config")
    op.drop_table("users")
    op.drop_table("role_permissions")
    op.drop_table("roles")
    scope_enum.drop(op.get_bind(), checkfirst=True)
    access_level_enum.drop(op.get_bind(), checkfirst=True)
