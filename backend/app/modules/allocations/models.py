"""See FSD §2.7 — Assignment entity."""

import uuid
from datetime import date, datetime
from typing import TYPE_CHECKING

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Date,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    Uuid,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.shared.models import Base

if TYPE_CHECKING:
    from app.modules.projects.models import Project
    from app.modules.resources.models import Resource


class Assignment(Base):
    """See FSD §2.7 — Assignment entity."""

    __tablename__ = "assignments"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    project_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("projects.id"), nullable=False)
    resource_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("resources.id"), nullable=False)
    allocation_pct: Mapped[int] = mapped_column(Integer, nullable=False)
    billability_pct: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    is_shadow: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    project_designation: Mapped[str | None] = mapped_column(String(100), nullable=True)
    project_expertise: Mapped[str | None] = mapped_column(String(100), nullable=True)
    billing_rate: Mapped[float | None] = mapped_column(Numeric(10, 2), nullable=True)
    start_date: Mapped[date] = mapped_column(Date, nullable=False)
    end_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="ACTIVE")
    released_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), onupdate=func.now(), nullable=True
    )

    __table_args__ = (
        Index("ix_assignments_project_id", "project_id"),
        Index("ix_assignments_resource_id", "resource_id"),
        Index("ix_assignments_status", "status"),
        Index("ix_assignments_end_date", "end_date"),
        CheckConstraint(
            "allocation_pct >= 1 AND allocation_pct <= 100", name="ck_allocation_pct_range"
        ),
        CheckConstraint(
            "billability_pct >= 0 AND billability_pct <= 100", name="ck_billability_pct_range"
        ),
    )

    project: Mapped["Project"] = relationship(lazy="selectin")
    resource: Mapped["Resource"] = relationship(lazy="selectin")
