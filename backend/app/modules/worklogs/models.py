"""See FSD §2.11 — Worklog entity."""

import uuid
from datetime import date, datetime
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import (
    Date,
    DateTime,
    ForeignKey,
    Index,
    Numeric,
    Text,
    UniqueConstraint,
    Uuid,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.shared.models import Base

if TYPE_CHECKING:
    from app.modules.projects.models import Project
    from app.modules.resources.models import Resource


class Worklog(Base):
    __tablename__ = "worklogs"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    resource_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("resources.id"), nullable=False
    )
    project_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("projects.id"), nullable=False
    )
    log_date: Mapped[date] = mapped_column(Date, nullable=False)
    hours: Mapped[Decimal] = mapped_column(Numeric(4, 1), nullable=False)
    note: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    __table_args__ = (
        UniqueConstraint("resource_id", "project_id", "log_date", name="uq_worklog_resource_project_date"),
        Index("ix_worklogs_resource_id", "resource_id"),
        Index("ix_worklogs_project_id", "project_id"),
        Index("ix_worklogs_log_date", "log_date"),
    )

    resource: Mapped["Resource"] = relationship(lazy="selectin")
    project: Mapped["Project"] = relationship(lazy="selectin")
