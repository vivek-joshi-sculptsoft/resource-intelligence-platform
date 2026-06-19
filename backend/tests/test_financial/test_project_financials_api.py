"""Tests for GET /api/v1/projects/:projectId/financials — VRIP-99."""

import uuid
from datetime import date, timedelta

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from tests.conftest import create_test_user, login_as, login_as_role


def _f(value):
    """Decimal fields serialize as strings in JSON (see utilization module convention)."""
    return None if value is None else float(value)


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


async def _create_invoice(client: AsyncClient, project_id: str, **overrides) -> dict:
    payload = {
        "invoice_date": date.today().isoformat(),
        "amount": 88000.00,
        "currency": "INR",
        "exchange_rate": 1.0,
        **overrides,
    }
    resp = await client.post(f"/api/v1/projects/{project_id}/invoices", json=payload)
    assert resp.status_code == 201, resp.text
    return resp.json()["data"]


async def _transition_invoice(client: AsyncClient, project_id: str, invoice_id: str, status: str) -> dict:
    resp = await client.put(
        f"/api/v1/projects/{project_id}/invoices/{invoice_id}/status",
        json={"status": status},
    )
    assert resp.status_code == 200, resp.text
    return resp.json()["data"]


async def _setup_full_scenario(client: AsyncClient, db: AsyncSession) -> dict:
    """Builds a project with: a billable resource, a shadow resource, a non-human
    cost, and an APPROVED invoice. Numbers are chosen so margin% comes out to exactly
    50.00 for both projected and actual margin — see calculation below.

    Resource A (non-shadow): loaded_cost=20000, allocation=100% -> cost = 20000
        billing_rate=500, billability=100% -> revenue = 100% * 22 * 8 * 500 = 88000
    Resource B (shadow): loaded_cost=20000, allocation=100% -> cost = 20000 (no revenue)
    NonHumanCost: amount_inr = 4000
    => resource_cost = 40000, total_cost = 44000
    => projected_revenue = 88000, projected_margin = 44000 (50.00%)
    Invoice (APPROVED): amount_inr = 88000
    => actual_revenue = 88000, actual_margin = 44000 (50.00%)
    """
    cl = await _create_client_entity(client)
    dm = await _create_resource(client, "DM Person")
    pm = await _create_resource(client, "PM Person")
    proj = await _create_project(
        client,
        cl["id"],
        dm["id"],
        pm["id"],
        type="TIME_AND_MATERIAL",
        contract_end_date=(date.today() + timedelta(days=365)).isoformat(),
    )

    res_a = await _create_resource(client, "Billable Dev", loaded_cost_monthly=20000)
    res_b = await _create_resource(client, "Shadow Dev", loaded_cost_monthly=20000)

    await _create_assignment(
        client, proj["id"], res_a["id"], billing_rate=500, billability_pct=100
    )
    await _create_assignment(
        client,
        proj["id"],
        res_b["id"],
        is_shadow=True,
        billability_pct=0,
    )
    await _create_cost(client, proj["id"], amount=4000.00)

    client, _ = await login_as_role(client, db, "FINANCE")
    inv = await _create_invoice(client, proj["id"], amount=88000.00)
    await _transition_invoice(client, proj["id"], inv["id"], "SUBMITTED")
    await _transition_invoice(client, proj["id"], inv["id"], "APPROVED")

    return {"project": proj, "dm": dm, "pm": pm, "res_a": res_a, "res_b": res_b}


@pytest.mark.asyncio
async def test_ceo_sees_full_breakdown(client: AsyncClient, db: AsyncSession):
    await login_as(client)
    ctx = await _setup_full_scenario(client, db)

    await login_as(client)
    resp = await client.get(f"/api/v1/projects/{ctx['project']['id']}/financials")
    assert resp.status_code == 200, resp.text
    data = resp.json()["data"]

    assert _f(data["resource_cost_inr"]) == 40000.0
    assert _f(data["non_human_cost_inr"]) == 4000.0
    assert _f(data["total_cost_inr"]) == 44000.0
    assert _f(data["projected_revenue_inr"]) == 88000.0
    assert _f(data["actual_revenue_inr"]) == 88000.0
    assert _f(data["projected_margin_inr"]) == 44000.0
    assert _f(data["projected_margin_pct"]) == 50.0
    assert _f(data["actual_margin_inr"]) == 44000.0
    assert _f(data["actual_margin_pct"]) == 50.0
    assert data["missing_costs"] == []
    assert data["missing_rates"] == []
    assert _f(data["exchange_rate_used"]) == 1.0

    breakdown = {item["resource_name"]: item for item in data["resource_cost_breakdown"]}
    assert _f(breakdown["Billable Dev"]["cost_contribution_inr"]) == 20000.0
    assert _f(breakdown["Shadow Dev"]["cost_contribution_inr"]) == 20000.0


@pytest.mark.asyncio
async def test_finance_sees_full_breakdown(client: AsyncClient, db: AsyncSession):
    await login_as(client)
    ctx = await _setup_full_scenario(client, db)

    await login_as_role(client, db, "FINANCE")
    resp = await client.get(f"/api/v1/projects/{ctx['project']['id']}/financials")
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert _f(data["total_cost_inr"]) == 44000.0
    assert _f(data["actual_revenue_inr"]) == 88000.0


@pytest.mark.asyncio
async def test_dm_own_portfolio_partial_visibility(client: AsyncClient, db: AsyncSession):
    """DM has NONE on ctc_loaded_cost and invoicing — those fields must be null,
    while billing_rates (and therefore projected_revenue) remain visible."""
    await login_as(client)
    ctx = await _setup_full_scenario(client, db)

    dm_user = await create_test_user(db, "DM", email=f"dm-{uuid.uuid4().hex[:6]}@test.com")
    dm_user.resource_id = uuid.UUID(ctx["dm"]["id"])
    await db.commit()
    await client.post("/api/v1/auth/login", json={"email": dm_user.email, "password": "TestPass123"})

    resp = await client.get(f"/api/v1/projects/{ctx['project']['id']}/financials")
    assert resp.status_code == 200
    data = resp.json()["data"]

    assert data["resource_cost_inr"] is None
    assert data["total_cost_inr"] is None
    assert data["actual_revenue_inr"] is None
    assert _f(data["projected_revenue_inr"]) == 88000.0
    assert data["projected_margin_inr"] is None  # total_cost is None -> margin null
    for item in data["resource_cost_breakdown"]:
        assert item["loaded_cost_monthly"] is None
        assert item["cost_contribution_inr"] is None


@pytest.mark.asyncio
async def test_dm_other_portfolio_forbidden(client: AsyncClient, db: AsyncSession):
    await login_as(client)
    ctx = await _setup_full_scenario(client, db)

    await login_as(client)
    other_dm_resource = await _create_resource(client, "Other DM")
    other_dm_user = await create_test_user(
        db, "DM", email=f"other-dm-{uuid.uuid4().hex[:6]}@test.com"
    )
    other_dm_user.resource_id = uuid.UUID(other_dm_resource["id"])
    await db.commit()
    await client.post(
        "/api/v1/auth/login", json={"email": other_dm_user.email, "password": "TestPass123"}
    )

    resp = await client.get(f"/api/v1/projects/{ctx['project']['id']}/financials")
    assert resp.status_code == 403


@pytest.mark.asyncio
async def test_pm_forbidden(client: AsyncClient, db: AsyncSession):
    """project_margin is NONE for PM per ACCESS-MATRIX — entire endpoint is blocked."""
    await login_as(client)
    ctx = await _setup_full_scenario(client, db)

    pm_user = await create_test_user(db, "PM", email=f"pm-{uuid.uuid4().hex[:6]}@test.com")
    pm_user.resource_id = uuid.UUID(ctx["pm"]["id"])
    await db.commit()
    await client.post("/api/v1/auth/login", json={"email": pm_user.email, "password": "TestPass123"})

    resp = await client.get(f"/api/v1/projects/{ctx['project']['id']}/financials")
    assert resp.status_code == 403


@pytest.mark.asyncio
async def test_hr_forbidden(client: AsyncClient, db: AsyncSession):
    await login_as(client)
    ctx = await _setup_full_scenario(client, db)

    await login_as_role(client, db, "HR")
    resp = await client.get(f"/api/v1/projects/{ctx['project']['id']}/financials")
    assert resp.status_code == 403


@pytest.mark.asyncio
async def test_engineer_forbidden(client: AsyncClient, db: AsyncSession):
    await login_as(client)
    ctx = await _setup_full_scenario(client, db)

    await login_as_role(client, db, "ENGINEER")
    resp = await client.get(f"/api/v1/projects/{ctx['project']['id']}/financials")
    assert resp.status_code == 403


@pytest.mark.asyncio
async def test_missing_loaded_cost_nulls_resource_cost(client: AsyncClient, db: AsyncSession):
    await login_as(client)
    cl = await _create_client_entity(client)
    dm = await _create_resource(client, "DM")
    pm = await _create_resource(client, "PM")
    proj = await _create_project(client, cl["id"], dm["id"], pm["id"])

    no_cost_resource = await _create_resource(client, "No Cost Dev")  # loaded_cost_monthly=None
    await _create_assignment(client, proj["id"], no_cost_resource["id"], billing_rate=500)

    resp = await client.get(f"/api/v1/projects/{proj['id']}/financials")
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert data["resource_cost_inr"] is None
    assert data["total_cost_inr"] is None
    assert "No Cost Dev" in data["missing_costs"]


@pytest.mark.asyncio
async def test_missing_billing_rate_nulls_projected_revenue(client: AsyncClient, db: AsyncSession):
    await login_as(client)
    cl = await _create_client_entity(client)
    dm = await _create_resource(client, "DM")
    pm = await _create_resource(client, "PM")
    proj = await _create_project(client, cl["id"], dm["id"], pm["id"])

    resource = await _create_resource(client, "No Rate Dev", loaded_cost_monthly=10000)
    await _create_assignment(client, proj["id"], resource["id"])  # no billing_rate

    resp = await client.get(f"/api/v1/projects/{proj['id']}/financials")
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert data["projected_revenue_inr"] is None
    assert "No Rate Dev" in data["missing_rates"]


@pytest.mark.asyncio
async def test_no_invoices_actual_revenue_is_zero(client: AsyncClient, db: AsyncSession):
    await login_as(client)
    cl = await _create_client_entity(client)
    dm = await _create_resource(client, "DM")
    pm = await _create_resource(client, "PM")
    proj = await _create_project(client, cl["id"], dm["id"], pm["id"])

    resp = await client.get(f"/api/v1/projects/{proj['id']}/financials")
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert _f(data["actual_revenue_inr"]) == 0.0
    assert _f(data["resource_cost_inr"]) == 0.0
    assert _f(data["non_human_cost_inr"]) == 0.0
    assert _f(data["total_cost_inr"]) == 0.0
    assert _f(data["projected_revenue_inr"]) == 0.0


@pytest.mark.asyncio
async def test_multi_currency_uses_latest_invoice_exchange_rate(client: AsyncClient, db: AsyncSession):
    """No exchange_rate field exists on Project/Assignment, so projected revenue for a
    non-INR project reuses the most recent invoice's exchange_rate (VRIP-99 design decision)."""
    await login_as(client)
    cl = await _create_client_entity(client)
    dm = await _create_resource(client, "DM")
    pm = await _create_resource(client, "PM")
    proj = await _create_project(
        client,
        cl["id"],
        dm["id"],
        pm["id"],
        type="TIME_AND_MATERIAL",
        billing_currency="USD",
        contract_end_date=(date.today() + timedelta(days=365)).isoformat(),
    )

    resource = await _create_resource(client, "USD Dev")
    await _create_assignment(client, proj["id"], resource["id"], billing_rate=100)
    # projected_revenue (USD) = 100% * 22 * 8 * 100 = 17600

    client, _ = await login_as_role(client, db, "FINANCE")
    await _create_invoice(
        client,
        proj["id"],
        invoice_date=(date.today() - timedelta(days=10)).isoformat(),
        amount=1000,
        currency="USD",
        exchange_rate=80.0,
        billing_period_start=(date.today() - timedelta(days=40)).isoformat(),
        billing_period_end=(date.today() - timedelta(days=11)).isoformat(),
    )
    await _create_invoice(
        client,
        proj["id"],
        invoice_date=date.today().isoformat(),
        amount=1000,
        currency="USD",
        exchange_rate=85.0,
        billing_period_start=(date.today() - timedelta(days=10)).isoformat(),
        billing_period_end=date.today().isoformat(),
    )

    await login_as(client)
    resp = await client.get(f"/api/v1/projects/{proj['id']}/financials")
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert _f(data["exchange_rate_used"]) == 85.0
    assert _f(data["projected_revenue_inr"]) == 17600 * 85.0


@pytest.mark.asyncio
async def test_inr_project_exchange_rate_is_one(client: AsyncClient, db: AsyncSession):
    await login_as(client)
    cl = await _create_client_entity(client)
    dm = await _create_resource(client, "DM")
    pm = await _create_resource(client, "PM")
    proj = await _create_project(client, cl["id"], dm["id"], pm["id"])

    resp = await client.get(f"/api/v1/projects/{proj['id']}/financials")
    assert resp.status_code == 200
    assert _f(resp.json()["data"]["exchange_rate_used"]) == 1.0


@pytest.mark.asyncio
async def test_project_not_found(client: AsyncClient, db: AsyncSession):
    await login_as(client)
    resp = await client.get(f"/api/v1/projects/{uuid.uuid4()}/financials")
    assert resp.status_code == 404
