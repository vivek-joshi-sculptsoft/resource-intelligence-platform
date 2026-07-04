"""Tests for GET /api/v1/dashboard/company-finance — VRIP-130."""

import uuid
from datetime import date, timedelta

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from tests.conftest import create_test_user, login_as, login_as_role


async def _create_resource(client: AsyncClient, name: str = "Test Dev", **overrides) -> dict:
    payload = {
        "employee_id": f"EMP-{uuid.uuid4().hex[:6]}",
        "name": name,
        "designation": "Senior Developer",
        **overrides,
    }
    resp = await client.post("/api/v1/resources", json=payload)
    assert resp.status_code == 201, resp.text
    return resp.json()["data"]


async def _create_client_entity(client: AsyncClient, name: str = "Test Client") -> dict:
    resp = await client.post("/api/v1/clients", json={"name": name})
    assert resp.status_code == 201, resp.text
    return resp.json()["data"]


async def _create_project(
    client: AsyncClient, client_id: str, dm_id: str, pm_id: str, **overrides
) -> dict:
    payload = {
        "name": f"Project-{uuid.uuid4().hex[:6]}",
        "client_id": client_id,
        "type": "FIXED_PRICE",
        "dm_id": dm_id,
        "pm_id": pm_id,
        **overrides,
    }
    resp = await client.post("/api/v1/projects", json=payload)
    assert resp.status_code == 201, resp.text
    return resp.json()["data"]


async def _create_assignment(
    client: AsyncClient, project_id: str, resource_id: str, **overrides
) -> dict:
    payload = {
        "resource_id": resource_id,
        "allocation_pct": 100,
        "billability_pct": 100,
        "is_shadow": False,
        "start_date": date.today().isoformat(),
        **overrides,
    }
    resp = await client.post(f"/api/v1/projects/{project_id}/assignments", json=payload)
    assert resp.status_code == 201, resp.text
    return resp.json()["data"]


async def _create_cost(client: AsyncClient, project_id: str, **overrides) -> dict:
    payload = {
        "description": "Cloud hosting",
        "category": "CLOUD_INFRA",
        "amount": 4000.00,
        "currency": "INR",
        "cost_date": date.today().isoformat(),
        **overrides,
    }
    resp = await client.post(f"/api/v1/projects/{project_id}/costs", json=payload)
    assert resp.status_code == 201, resp.text
    return resp.json()["data"]


async def _create_invoice_db(db: AsyncSession, project_id: str, **overrides) -> None:
    """Insert invoice directly — CEO can only VIEW invoices, not create them."""
    from app.modules.invoicing.models import Invoice

    inv = Invoice(
        id=uuid.uuid4(),
        project_id=uuid.UUID(project_id),
        invoice_date=overrides.get("invoice_date", date.today()),
        amount=overrides.get("amount", 100000.00),
        currency=overrides.get("currency", "INR"),
        exchange_rate=overrides.get("exchange_rate", 1.0),
        amount_inr=overrides.get("amount_inr", 100000.00),
        status=overrides.get("status", "APPROVED"),
    )
    db.add(inv)
    await db.commit()


# --- Access Control Tests ---


@pytest.mark.asyncio
async def test_ceo_can_access(client: AsyncClient, db: AsyncSession):
    await login_as(client)
    resp = await client.get("/api/v1/dashboard/company-finance")
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert "period_start" in data
    assert "actual_revenue_inr" in data


@pytest.mark.asyncio
async def test_cto_can_access(client: AsyncClient, db: AsyncSession):
    await login_as_role(client, db, "CTO")
    resp = await client.get("/api/v1/dashboard/company-finance")
    assert resp.status_code == 200


@pytest.mark.asyncio
async def test_finance_can_access(client: AsyncClient, db: AsyncSession):
    await login_as_role(client, db, "FINANCE")
    resp = await client.get("/api/v1/dashboard/company-finance")
    assert resp.status_code == 200


@pytest.mark.asyncio
async def test_dm_gets_403(client: AsyncClient, db: AsyncSession):
    """DM has OWN_PORTFOLIO scope on project_margin — no access to company-wide finance."""
    await login_as_role(client, db, "DM")
    resp = await client.get("/api/v1/dashboard/company-finance")
    assert resp.status_code == 403


@pytest.mark.asyncio
async def test_pm_gets_403(client: AsyncClient, db: AsyncSession):
    await login_as_role(client, db, "PM")
    resp = await client.get("/api/v1/dashboard/company-finance")
    assert resp.status_code == 403


@pytest.mark.asyncio
async def test_hr_gets_403(client: AsyncClient, db: AsyncSession):
    await login_as_role(client, db, "HR")
    resp = await client.get("/api/v1/dashboard/company-finance")
    assert resp.status_code == 403


@pytest.mark.asyncio
async def test_engineer_gets_403(client: AsyncClient, db: AsyncSession):
    await login_as_role(client, db, "ENGINEER")
    resp = await client.get("/api/v1/dashboard/company-finance")
    assert resp.status_code == 403


# --- Date Range Tests ---


@pytest.mark.asyncio
async def test_this_month_default(client: AsyncClient, db: AsyncSession):
    await login_as(client)
    resp = await client.get("/api/v1/dashboard/company-finance")
    assert resp.status_code == 200
    data = resp.json()["data"]
    today = date.today()
    assert data["period_start"] == today.replace(day=1).isoformat()
    assert data["period_end"] == today.isoformat()


@pytest.mark.asyncio
async def test_last_3_months(client: AsyncClient, db: AsyncSession):
    await login_as(client)
    resp = await client.get("/api/v1/dashboard/company-finance?range=LAST_3_MONTHS")
    assert resp.status_code == 200
    data = resp.json()["data"]
    today = date.today()
    month = today.month - 2
    year = today.year
    if month <= 0:
        month += 12
        year -= 1
    expected_start = date(year, month, 1).isoformat()
    assert data["period_start"] == expected_start
    assert data["period_end"] == today.isoformat()


@pytest.mark.asyncio
async def test_custom_range(client: AsyncClient, db: AsyncSession):
    await login_as(client)
    resp = await client.get(
        "/api/v1/dashboard/company-finance?range=CUSTOM&start_date=2026-01-01&end_date=2026-06-30"
    )
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert data["period_start"] == "2026-01-01"
    assert data["period_end"] == "2026-06-30"


@pytest.mark.asyncio
async def test_custom_range_missing_dates(client: AsyncClient, db: AsyncSession):
    await login_as(client)
    resp = await client.get("/api/v1/dashboard/company-finance?range=CUSTOM")
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_custom_range_end_before_start(client: AsyncClient, db: AsyncSession):
    await login_as(client)
    resp = await client.get(
        "/api/v1/dashboard/company-finance?range=CUSTOM&start_date=2026-06-30&end_date=2026-01-01"
    )
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_invalid_range_value(client: AsyncClient, db: AsyncSession):
    await login_as(client)
    resp = await client.get("/api/v1/dashboard/company-finance?range=INVALID")
    assert resp.status_code == 422


# --- Calculation Tests ---


@pytest.mark.asyncio
async def test_actual_revenue_from_invoices(client: AsyncClient, db: AsyncSession):
    """Actual revenue = SUM(invoice.amount_inr) where status IN (APPROVED, PAID) in period."""
    await login_as(client)

    resource = await _create_resource(client, loaded_cost_monthly=100000)
    cl = await _create_client_entity(client)
    project = await _create_project(
        client, cl["id"], resource["id"], resource["id"]
    )

    today = date.today()
    await _create_invoice_db(db, project["id"], amount_inr=50000, invoice_date=today)
    await _create_invoice_db(db, project["id"], amount_inr=30000, invoice_date=today, status="PAID")
    # DRAFT invoice should not count
    await _create_invoice_db(db, project["id"], amount_inr=99999, invoice_date=today, status="DRAFT")

    resp = await client.get("/api/v1/dashboard/company-finance?range=THIS_MONTH")
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert float(data["actual_revenue_inr"]) == 80000.0


@pytest.mark.asyncio
async def test_projected_revenue_from_assignments(client: AsyncClient, db: AsyncSession):
    """Projected revenue = billability_pct/100 × working_days_in_period × 8 × billing_rate."""
    await login_as(client)

    resource = await _create_resource(client, loaded_cost_monthly=100000)
    cl = await _create_client_entity(client)
    project = await _create_project(
        client, cl["id"], resource["id"], resource["id"]
    )

    today = date.today()
    period_start = today.replace(day=1)

    await _create_assignment(
        client,
        project["id"],
        resource["id"],
        billability_pct=100,
        billing_rate=100.0,
        start_date=period_start.isoformat(),
    )

    resp = await client.get("/api/v1/dashboard/company-finance?range=THIS_MONTH")
    assert resp.status_code == 200
    data = resp.json()["data"]
    # Projected revenue should be > 0 (exact value depends on working days in month)
    assert float(data["projected_revenue_inr"]) > 0


@pytest.mark.asyncio
async def test_shadow_assignments_excluded_from_projected_revenue(
    client: AsyncClient, db: AsyncSession
):
    """Shadow assignments contribute to cost but NOT projected revenue."""
    await login_as(client)

    resource = await _create_resource(client, loaded_cost_monthly=100000)
    cl = await _create_client_entity(client)
    project = await _create_project(
        client, cl["id"], resource["id"], resource["id"]
    )

    today = date.today()
    period_start = today.replace(day=1)

    await _create_assignment(
        client,
        project["id"],
        resource["id"],
        billability_pct=0,
        billing_rate=100.0,
        is_shadow=True,
        start_date=period_start.isoformat(),
    )

    resp = await client.get("/api/v1/dashboard/company-finance?range=THIS_MONTH")
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert float(data["projected_revenue_inr"]) == 0
    # But resource cost should be > 0
    assert float(data["resource_cost_inr"]) > 0


@pytest.mark.asyncio
async def test_non_human_costs_one_time(client: AsyncClient, db: AsyncSession):
    """One-time costs within period contribute to total cost."""
    await login_as(client)

    resource = await _create_resource(client, loaded_cost_monthly=100000)
    cl = await _create_client_entity(client)
    project = await _create_project(
        client, cl["id"], resource["id"], resource["id"]
    )

    today = date.today()
    await _create_cost(client, project["id"], amount=5000, cost_date=today.isoformat())

    resp = await client.get("/api/v1/dashboard/company-finance?range=THIS_MONTH")
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert float(data["non_human_cost_inr"]) == 5000.0


@pytest.mark.asyncio
async def test_non_human_costs_recurring(client: AsyncClient, db: AsyncSession):
    """Recurring costs active during period contribute to total cost."""
    await login_as(client)

    resource = await _create_resource(client, loaded_cost_monthly=100000)
    cl = await _create_client_entity(client)
    project = await _create_project(
        client, cl["id"], resource["id"], resource["id"]
    )

    today = date.today()
    # Recurring cost started last month, ends in the future
    last_month = today - timedelta(days=40)
    future = today + timedelta(days=60)
    await _create_cost(
        client,
        project["id"],
        amount=3000,
        cost_date=last_month.isoformat(),
        is_recurring=True,
        recurring_end_date=future.isoformat(),
    )

    resp = await client.get("/api/v1/dashboard/company-finance?range=THIS_MONTH")
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert float(data["non_human_cost_inr"]) == 3000.0


@pytest.mark.asyncio
async def test_margin_calculations(client: AsyncClient, db: AsyncSession):
    """Margin = Revenue - Total Cost; Margin % = Margin / Revenue × 100."""
    await login_as(client)

    resource = await _create_resource(client, loaded_cost_monthly=100000)
    cl = await _create_client_entity(client)
    project = await _create_project(
        client, cl["id"], resource["id"], resource["id"]
    )

    today = date.today()
    await _create_invoice_db(db, project["id"], amount_inr=200000, invoice_date=today)
    await _create_cost(client, project["id"], amount=50000, cost_date=today.isoformat())

    resp = await client.get("/api/v1/dashboard/company-finance?range=THIS_MONTH")
    assert resp.status_code == 200
    data = resp.json()["data"]

    actual_revenue = float(data["actual_revenue_inr"])
    total_cost = float(data["total_cost_inr"])
    actual_margin = float(data["actual_margin_inr"])

    assert actual_revenue == 200000.0
    assert actual_margin == actual_revenue - total_cost


# --- Filter Tests ---


@pytest.mark.asyncio
async def test_project_filter(client: AsyncClient, db: AsyncSession):
    """project_id filter narrows results to that project only."""
    await login_as(client)

    resource = await _create_resource(client, loaded_cost_monthly=100000)
    cl = await _create_client_entity(client)
    p1 = await _create_project(client, cl["id"], resource["id"], resource["id"])
    p2 = await _create_project(client, cl["id"], resource["id"], resource["id"])

    today = date.today()
    await _create_invoice_db(db, p1["id"], amount_inr=100000, invoice_date=today)
    await _create_invoice_db(db, p2["id"], amount_inr=50000, invoice_date=today)

    # No filter — both projects
    resp = await client.get("/api/v1/dashboard/company-finance?range=THIS_MONTH")
    data = resp.json()["data"]
    assert float(data["actual_revenue_inr"]) == 150000.0

    # Filter by p1
    resp = await client.get(f"/api/v1/dashboard/company-finance?range=THIS_MONTH&project_id={p1['id']}")
    data = resp.json()["data"]
    assert float(data["actual_revenue_inr"]) == 100000.0


@pytest.mark.asyncio
async def test_client_filter(client: AsyncClient, db: AsyncSession):
    """client_id filter narrows results to projects of that client."""
    await login_as(client)

    resource = await _create_resource(client, loaded_cost_monthly=100000)
    cl1 = await _create_client_entity(client, name="Client A")
    cl2 = await _create_client_entity(client, name="Client B")
    p1 = await _create_project(client, cl1["id"], resource["id"], resource["id"])
    p2 = await _create_project(client, cl2["id"], resource["id"], resource["id"])

    today = date.today()
    await _create_invoice_db(db, p1["id"], amount_inr=100000, invoice_date=today)
    await _create_invoice_db(db, p2["id"], amount_inr=75000, invoice_date=today)

    # Filter by cl1
    resp = await client.get(f"/api/v1/dashboard/company-finance?range=THIS_MONTH&client_id={cl1['id']}")
    data = resp.json()["data"]
    assert float(data["actual_revenue_inr"]) == 100000.0


@pytest.mark.asyncio
async def test_incomplete_data_flag(client: AsyncClient, db: AsyncSession):
    """Projects missing loaded_cost or billing_rate are flagged."""
    await login_as(client)

    # Resource WITHOUT loaded_cost_monthly
    resource_no_cost = await _create_resource(client, name="NoCost Dev")
    cl = await _create_client_entity(client)
    project = await _create_project(
        client, cl["id"], resource_no_cost["id"], resource_no_cost["id"]
    )

    today = date.today()
    await _create_assignment(
        client,
        project["id"],
        resource_no_cost["id"],
        start_date=today.replace(day=1).isoformat(),
        billing_rate=100.0,
    )

    resp = await client.get("/api/v1/dashboard/company-finance?range=THIS_MONTH")
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert data["projects_with_incomplete_financial_data"] >= 1


@pytest.mark.asyncio
async def test_empty_period_returns_zeros(client: AsyncClient, db: AsyncSession):
    """When nothing falls in the selected period, return zero values."""
    await login_as(client)

    resp = await client.get(
        "/api/v1/dashboard/company-finance?range=CUSTOM&start_date=2020-01-01&end_date=2020-01-31"
    )
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert float(data["actual_revenue_inr"]) == 0
    assert float(data["projected_revenue_inr"]) == 0
    assert float(data["total_cost_inr"]) == 0


@pytest.mark.asyncio
async def test_assignment_spanning_period_boundary(client: AsyncClient, db: AsyncSession):
    """Assignment that starts before period and ends after period: only count working days in period."""
    await login_as(client)

    resource = await _create_resource(client, loaded_cost_monthly=220000)
    cl = await _create_client_entity(client)
    project = await _create_project(
        client, cl["id"], resource["id"], resource["id"]
    )

    # Assignment spans entire year, query only January
    await _create_assignment(
        client,
        project["id"],
        resource["id"],
        billability_pct=100,
        billing_rate=100.0,
        start_date="2026-01-01",
        end_date="2026-12-31",
    )

    resp = await client.get(
        "/api/v1/dashboard/company-finance?range=CUSTOM&start_date=2026-01-01&end_date=2026-01-31"
    )
    assert resp.status_code == 200
    data = resp.json()["data"]
    # Jan 2026 has 22 weekdays; revenue = 100% × 22 × 8 × 100 = 17600
    assert float(data["projected_revenue_inr"]) == 17600.0


@pytest.mark.asyncio
async def test_response_shape(client: AsyncClient, db: AsyncSession):
    """Response has all expected fields per API.md spec."""
    await login_as(client)
    resp = await client.get("/api/v1/dashboard/company-finance")
    assert resp.status_code == 200
    data = resp.json()["data"]
    expected_keys = {
        "period_start",
        "period_end",
        "actual_revenue_inr",
        "projected_revenue_inr",
        "resource_cost_inr",
        "non_human_cost_inr",
        "total_cost_inr",
        "projected_margin_inr",
        "projected_margin_pct",
        "actual_margin_inr",
        "actual_margin_pct",
        "projects_with_incomplete_financial_data",
    }
    assert set(data.keys()) == expected_keys
