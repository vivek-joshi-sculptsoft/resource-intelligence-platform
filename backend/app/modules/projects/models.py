"""Stub model for Sprint 2 — full implementation in Sprint 3 (VRIP-43+)."""

import uuid
from datetime import datetime

from sqlalchemy import (
    Boolean,
    DateTime,
    ForeignKey,
    Index,
    String,
    Uuid,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.shared.models import Base


class Project(Base):
    __tablename__ = "projects"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    client_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("clients.id"), nullable=False, index=True
    )
    type: Mapped[str] = mapped_column(String(50), nullable=False, default="TIME_AND_MATERIAL")
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="ACTIVE")
    dm_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid, ForeignKey("resources.id", ondelete="SET NULL"), nullable=True, index=True
    )
    pm_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid, ForeignKey("resources.id", ondelete="SET NULL"), nullable=True, index=True
    )
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    __table_args__ = (Index("ix_projects_status", "status"),)
