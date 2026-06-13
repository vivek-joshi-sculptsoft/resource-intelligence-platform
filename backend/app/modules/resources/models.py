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


class Resource(Base):
    """See FSD §2.5 — Resource entity."""

    __tablename__ = "resources"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    employee_id: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    designation: Mapped[str] = mapped_column(String(100), nullable=False)
    technical_expertise: Mapped[str | None] = mapped_column(String(100), nullable=True)
    date_of_joining: Mapped[date | None] = mapped_column(Date, nullable=True)
    reporting_manager_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid,
        ForeignKey("resources.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    loaded_cost_monthly: Mapped[float | None] = mapped_column(Numeric(15, 2), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    __table_args__ = (
        Index("ix_resources_employee_id", "employee_id"),
        Index("ix_resources_is_active", "is_active"),
        Index("ix_resources_designation", "designation"),
    )

    tags: Mapped[list["ResourceTag"]] = relationship(
        back_populates="resource", cascade="all, delete-orphan"
    )
    reporting_manager: Mapped["Resource | None"] = relationship(
        remote_side="Resource.id", lazy="selectin"
    )


class ResourceTag(Base):
    """See FSD §2.5 — ResourceTag join table."""

    __tablename__ = "resource_tags"

    resource_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("resources.id", ondelete="CASCADE"), primary_key=True
    )
    tag: Mapped[str] = mapped_column(String(100), primary_key=True)

    __table_args__ = (Index("ix_resource_tags_tag", "tag"),)

    resource: Mapped["Resource"] = relationship(back_populates="tags")
