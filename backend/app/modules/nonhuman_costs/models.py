"""See FSD §2.10 — NonHumanCost entity."""

import uuid
from datetime import date, datetime

from sqlalchemy import (
    Boolean,
    Date,
    DateTime,
    ForeignKey,
    Index,
    Numeric,
    String,
    Uuid,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.shared.models import Base


class NonHumanCost(Base):
    """See FSD §2.10 — NonHumanCost entity for project expenses beyond human resources."""

    __tablename__ = "non_human_costs"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    project_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True
    )
    description: Mapped[str] = mapped_column(String(500), nullable=False)
    category: Mapped[str] = mapped_column(String(30), nullable=False)
    amount: Mapped[float] = mapped_column(Numeric(15, 2), nullable=False)
    currency: Mapped[str] = mapped_column(String(3), nullable=False, default="INR")
    exchange_rate: Mapped[float] = mapped_column(Numeric(10, 4), nullable=False, default=1.0)
    amount_inr: Mapped[float] = mapped_column(Numeric(15, 2), nullable=False)
    cost_date: Mapped[date] = mapped_column(Date, nullable=False)
    is_recurring: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    recurring_end_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    created_by: Mapped[uuid.UUID | None] = mapped_column(
        Uuid, ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), onupdate=func.now(), nullable=True
    )

    __table_args__ = (
        Index("ix_non_human_costs_category", "category"),
        Index("ix_non_human_costs_is_recurring", "is_recurring"),
        Index("ix_non_human_costs_cost_date", "cost_date"),
    )

    project: Mapped["Project"] = relationship(lazy="selectin")  # type: ignore[name-defined]  # noqa: F821
    creator: Mapped["User"] = relationship(lazy="selectin")  # type: ignore[name-defined]  # noqa: F821
