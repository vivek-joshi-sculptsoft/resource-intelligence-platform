import enum
import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, Enum, ForeignKey, Integer, String, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.shared.models import Base


class AccessLevel(enum.StrEnum):
    NONE = "NONE"
    VIEW = "VIEW"
    EDIT = "EDIT"


class Scope(enum.StrEnum):
    ALL = "ALL"
    OWN_PORTFOLIO = "OWN_PORTFOLIO"
    SELF_ONLY = "SELF_ONLY"


class Role(Base):
    __tablename__ = "roles"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    code: Mapped[str] = mapped_column(String(20), unique=True, nullable=False)
    permission_level: Mapped[int] = mapped_column(Integer, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    permissions: Mapped[list["RolePermission"]] = relationship(back_populates="role")
    users: Mapped[list["User"]] = relationship(back_populates="role")


class RolePermission(Base):
    __tablename__ = "role_permissions"
    __table_args__ = (UniqueConstraint("role_id", "data_type", name="uq_role_data_type"),)

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    role_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("roles.id"), nullable=False, index=True
    )
    data_type: Mapped[str] = mapped_column(String(50), nullable=False)
    access_level: Mapped[AccessLevel] = mapped_column(
        Enum(AccessLevel, name="access_level_enum"), nullable=False
    )
    scope: Mapped[Scope] = mapped_column(
        Enum(Scope, name="scope_enum"), nullable=False, default=Scope.ALL
    )
    is_configurable: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    role: Mapped["Role"] = relationship(back_populates="permissions")


class User(Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    role_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("roles.id"), nullable=False, index=True
    )
    resource_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), nullable=True, index=True
    )
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), onupdate=func.now(), nullable=True
    )

    role: Mapped["Role"] = relationship(back_populates="users")


class SystemConfig(Base):
    __tablename__ = "system_config"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    key: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    value: Mapped[str] = mapped_column(String(500), nullable=False)
    description: Mapped[str | None] = mapped_column(String(500), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), onupdate=func.now(), nullable=True
    )
