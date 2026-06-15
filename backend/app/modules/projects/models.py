"""See FSD §2.6 — Project entity."""

import uuid
from datetime import date, datetime
from typing import TYPE_CHECKING

from sqlalchemy import (
    Boolean,
    Date,
    DateTime,
    ForeignKey,
    Index,
    Numeric,
    String,
    Text,
    Uuid,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.shared.models import Base

if TYPE_CHECKING:
    from app.modules.clients.models import Client
    from app.modules.resources.models import Resource


class Project(Base):
    """See FSD §2.6 — Project entity."""

    __tablename__ = "projects"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    client_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("clients.id"), nullable=False)
    type: Mapped[str] = mapped_column(String(50), nullable=False, default="TIME_AND_MATERIAL")
    billing_currency: Mapped[str] = mapped_column(String(3), nullable=False, default="INR")
    contract_value: Mapped[float | None] = mapped_column(Numeric(15, 2), nullable=True)
    start_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    contract_end_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    dm_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("resources.id", ondelete="RESTRICT"), nullable=False
    )
    pm_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("resources.id", ondelete="RESTRICT"), nullable=False
    )
    worklog_enabled: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="ACTIVE")
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), onupdate=func.now(), nullable=True
    )

    __table_args__ = (
        Index("ix_projects_client_id", "client_id"),
        Index("ix_projects_dm_id", "dm_id"),
        Index("ix_projects_pm_id", "pm_id"),
        Index("ix_projects_status", "status"),
    )

    client: Mapped["Client"] = relationship(lazy="selectin")
    dm: Mapped["Resource"] = relationship(foreign_keys=[dm_id], lazy="selectin")
    pm: Mapped["Resource"] = relationship(foreign_keys=[pm_id], lazy="selectin")
