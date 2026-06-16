"""Tests for recurring cost processing job — VRIP-92."""

import uuid
from datetime import date, timedelta

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.audit.models import AuditLog
from app.modules.clients.models import Client
from app.modules.nonhuman_costs.jobs import run_process_recurring_costs
from app.modules.nonhuman_costs.models import NonHumanCost
from app.modules.projects.models import Project
from app.modules.resources.models import Resource
from tests.conftest import create_test_user


async def _create_project(db: AsyncSession) -> Project:
    dm = Resource(
        id=uuid.uuid4(), employee_id=f"EMP-{uuid.uuid4().hex[:6]}",
        name="DM", designation="DM",
    )
    pm = Resource(
        id=uuid.uuid4(), employee_id=f"EMP-{uuid.uuid4().hex[:6]}",
        name="PM", designation="PM",
    )
    cl = Client(id=uuid.uuid4(), name=f"Client-{uuid.uuid4().hex[:6]}")
    db.add_all([dm, pm, cl])
    await db.flush()

    proj = Project(
        id=uuid.uuid4(), name=f"Proj-{uuid.uuid4().hex[:6]}",
        client_id=cl.id, type="FIXED_PRICE", dm_id=dm.id, pm_id=pm.id,
    )
    db.add(proj)
    await db.flush()
    return proj


def _make_recurring_cost(
    project_id: uuid.UUID,
    *,
    description: str = "AWS monthly",
    category: str = "CLOUD_INFRA",
    amount: float = 5000.0,
    currency: str = "INR",
    exchange_rate: float = 1.0,
    cost_date: date | None = None,
    recurring_end_date: date | None = None,
) -> NonHumanCost:
    today = date.today()
    return NonHumanCost(
        id=uuid.uuid4(),
        project_id=project_id,
        description=description,
        category=category,
        amount=amount,
        currency=currency,
        exchange_rate=exchange_rate,
        amount_inr=amount * exchange_rate,
        cost_date=cost_date or (today - timedelta(days=60)),
        is_recurring=True,
        recurring_end_date=recurring_end_date or (today + timedelta(days=180)),
    )


# ── Normal Processing ──


@pytest.mark.asyncio
async def test_normal_processing(db: AsyncSession):
    proj = await _create_project(db)
    rc = _make_recurring_cost(proj.id)
    db.add(rc)
    await db.commit()

    result = await run_process_recurring_costs(db)
    await db.commit()

    assert result["candidates"] == 1
    assert result["created"] == 1
    assert result["skipped"] == 0
    assert result["errors"] == 0

    today = date.today()
    month_start = today.replace(day=1)
    entries = await db.execute(
        select(NonHumanCost).where(
            NonHumanCost.project_id == proj.id,
            NonHumanCost.cost_date == month_start,
            NonHumanCost.is_recurring == False,  # noqa: E712
        )
    )
    snapshot = entries.scalar_one()
    assert snapshot.description == "AWS monthly"
    assert snapshot.category == "CLOUD_INFRA"
    assert float(snapshot.amount) == 5000.0
    assert snapshot.currency == "INR"
    assert float(snapshot.exchange_rate) == 1.0
    assert float(snapshot.amount_inr) == 5000.0
    assert snapshot.is_recurring is False
    assert snapshot.recurring_end_date is None


@pytest.mark.asyncio
async def test_generated_entry_audit_log(db: AsyncSession):
    proj = await _create_project(db)
    rc = _make_recurring_cost(proj.id)
    db.add(rc)
    await db.commit()

    await run_process_recurring_costs(db)
    await db.commit()

    entries = await db.execute(
        select(NonHumanCost).where(
            NonHumanCost.project_id == proj.id,
            NonHumanCost.is_recurring == False,  # noqa: E712
        )
    )
    snapshot = entries.scalar_one()

    audit_entries = await db.execute(
        select(AuditLog).where(
            AuditLog.entity_type == "NonHumanCost",
            AuditLog.entity_id == snapshot.id,
            AuditLog.action == "CREATE",
        )
    )
    audit = audit_entries.scalar_one()
    assert audit.changed_by == uuid.UUID(int=0)


# ── Idempotency ──


@pytest.mark.asyncio
async def test_idempotency_no_duplicates(db: AsyncSession):
    proj = await _create_project(db)
    rc = _make_recurring_cost(proj.id)
    db.add(rc)
    await db.commit()

    r1 = await run_process_recurring_costs(db)
    await db.commit()
    assert r1["created"] == 1

    r2 = await run_process_recurring_costs(db)
    await db.commit()
    assert r2["created"] == 0
    assert r2["skipped"] == 1

    today = date.today()
    month_start = today.replace(day=1)
    entries = await db.execute(
        select(NonHumanCost).where(
            NonHumanCost.project_id == proj.id,
            NonHumanCost.cost_date == month_start,
            NonHumanCost.is_recurring == False,  # noqa: E712
        )
    )
    assert len(entries.scalars().all()) == 1


# ── Expired Recurring Cost ──


@pytest.mark.asyncio
async def test_expired_recurring_cost_skipped(db: AsyncSession):
    proj = await _create_project(db)
    rc = _make_recurring_cost(
        proj.id,
        cost_date=date.today() - timedelta(days=365),
        recurring_end_date=date.today() - timedelta(days=1),
    )
    db.add(rc)
    await db.commit()

    result = await run_process_recurring_costs(db)
    await db.commit()

    assert result["candidates"] == 0
    assert result["created"] == 0


# ── Future Recurring Cost ──


@pytest.mark.asyncio
async def test_future_recurring_cost_skipped(db: AsyncSession):
    proj = await _create_project(db)
    rc = _make_recurring_cost(
        proj.id,
        cost_date=date.today() + timedelta(days=30),
        recurring_end_date=date.today() + timedelta(days=180),
    )
    db.add(rc)
    await db.commit()

    result = await run_process_recurring_costs(db)
    await db.commit()

    assert result["candidates"] == 0
    assert result["created"] == 0


# ── Multiple Recurring Costs ──


@pytest.mark.asyncio
async def test_multiple_recurring_costs(db: AsyncSession):
    proj = await _create_project(db)
    rc1 = _make_recurring_cost(proj.id, description="AWS monthly")
    rc2 = _make_recurring_cost(proj.id, description="GitHub license", category="THIRD_PARTY_LICENSE", amount=2000.0)
    db.add_all([rc1, rc2])
    await db.commit()

    result = await run_process_recurring_costs(db)
    await db.commit()

    assert result["candidates"] == 2
    assert result["created"] == 2


# ── Multi-Currency ──


@pytest.mark.asyncio
async def test_multi_currency_processing(db: AsyncSession):
    proj = await _create_project(db)
    rc = _make_recurring_cost(
        proj.id,
        description="AWS US region",
        amount=100.0,
        currency="USD",
        exchange_rate=83.5,
    )
    db.add(rc)
    await db.commit()

    result = await run_process_recurring_costs(db)
    await db.commit()

    assert result["created"] == 1

    today = date.today()
    month_start = today.replace(day=1)
    entries = await db.execute(
        select(NonHumanCost).where(
            NonHumanCost.project_id == proj.id,
            NonHumanCost.cost_date == month_start,
            NonHumanCost.is_recurring == False,  # noqa: E712
        )
    )
    snapshot = entries.scalar_one()
    assert snapshot.currency == "USD"
    assert float(snapshot.exchange_rate) == 83.5
    assert float(snapshot.amount_inr) == 8350.0


# ── Edge: Boundary Dates ──


@pytest.mark.asyncio
async def test_recurring_end_date_equals_today(db: AsyncSession):
    proj = await _create_project(db)
    rc = _make_recurring_cost(
        proj.id,
        cost_date=date.today() - timedelta(days=30),
        recurring_end_date=date.today(),
    )
    db.add(rc)
    await db.commit()

    result = await run_process_recurring_costs(db)
    await db.commit()

    assert result["candidates"] == 1
    assert result["created"] == 1


@pytest.mark.asyncio
async def test_cost_date_equals_today(db: AsyncSession):
    proj = await _create_project(db)
    rc = _make_recurring_cost(
        proj.id,
        cost_date=date.today(),
        recurring_end_date=date.today() + timedelta(days=90),
    )
    db.add(rc)
    await db.commit()

    result = await run_process_recurring_costs(db)
    await db.commit()

    assert result["candidates"] == 1
    assert result["created"] == 1


# ── Inactive (Soft-Deleted) Recurring Cost ──


@pytest.mark.asyncio
async def test_inactive_recurring_cost_not_processed(db: AsyncSession):
    proj = await _create_project(db)
    rc = _make_recurring_cost(proj.id)
    rc.is_active = False
    db.add(rc)
    await db.commit()

    result = await run_process_recurring_costs(db)
    await db.commit()

    assert result["candidates"] == 0
    assert result["created"] == 0
