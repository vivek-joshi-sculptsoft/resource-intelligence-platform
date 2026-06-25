"""Tests for client and company financial aggregation endpoints — VRIP-100.

GET /api/v1/clients/:clientId/financials and GET /api/v1/dashboard/financials.
"""

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


async def _create_milestone(client: AsyncClient, project_id: str, **overrides) -> dict:
    payload = {
        "name": f"Milestone-{uuid.uuid4().hex[:6]}",
        "planned_delivery_date": (date.today() + timedelta(days=30)).isoformat(),
        "amount": 88000.00,
        **overrides,
    }
    resp = await client.post(f"/api/v1/projects/{project_id}/milestones", json=payload)
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


async def _transition_invoice(
    client: AsyncClient, project_id: str, invoice_id: str, status: str
) -> dict:
    resp = await client.put(
        f"/api/v1/projects/{project_id}/invoices/{invoice_id}/status",
        json={"status": status},
    )
    assert resp.status_code == 200, resp.text
    return resp.json()["data"]


async def _setup_project(
    client: AsyncClient,
    db: AsyncSession,
    client_id: str,
    dm_id: str,
    pm_id: str,
    project_type: str = "TIME_AND_MATERIAL",
) -> dict:
    """Builds a project with one billable resource, a non-human cost, and an APPROVED
    invoice. resource_cost=20000, non_human=4000, total_cost=24000.
    billing_rate=500 -> projected_revenue = 100% * 22 * 8 * 500 = 88000. invoice=88000."""
    proj = await _create_project(
        client,
        client_id,
        dm_id,
        pm_id,
        type=project_type,
        contract_end_date=(date.today() + timedelta(days=365)).isoformat(),
    )
    resource = await _create_resource(
        client, f"Dev-{uuid.uuid4().hex[:6]}", loaded_cost_monthly=20000
    )
    await _create_assignment(
        client, proj["id"], resource["id"], billing_rate=500, billability_pct=100
    )
    await _create_cost(client, proj["id"], amount=4000.00)

    invoice_overrides: dict = {"amount": 88000.00}
    if project_type == "FIXED_PRICE":
        milestone = await _create_milestone(client, proj["id"])
        for status in ("DELIVERED", "APPROVED"):
            resp = await client.put(
                f"/api/v1/projects/{proj['id']}/milestones/{milestone['id']}/status",
                json={"status": status},
            )
            assert resp.status_code == 200, resp.text
        invoice_overrides["milestone_id"] = milestone["id"]

    client, _ = await login_as_role(client, db, "FINANCE")
    inv = await _create_invoice(client, proj["id"], **invoice_overrides)
    await _transition_invoice(client, proj["id"], inv["id"], "SUBMITTED")
    await _transition_invoice(client, proj["id"], inv["id"], "APPROVED")

    return proj


@pytest.mark.asyncio
async def test_ceo_sees_client_financials_aggregated_across_projects(
    client: AsyncClient, db: AsyncSession
):
    await login_as(client)
    cl = await _create_client_entity(client)
    dm = await _create_resource(client, "DM Person")
    pm = await _create_resource(client, "PM Person")

    await _setup_project(client, db, cl["id"], dm["id"], pm["id"])
    await login_as(client)
    await _setup_project(client, db, cl["id"], dm["id"], pm["id"])

    await login_as(client)
    resp = await client.get(f"/api/v1/clients/{cl['id']}/financials")
    assert resp.status_code == 200, resp.text
    data = resp.json()["data"]

    assert _f(data["total_resource_cost_inr"]) == 40000.0
    assert _f(data["total_non_human_cost_inr"]) == 8000.0
    assert _f(data["total_cost_inr"]) == 48000.0
    assert _f(data["total_projected_revenue_inr"]) == 176000.0
    assert _f(data["total_actual_revenue_inr"]) == 176000.0
    assert _f(data["projected_margin_inr"]) == 128000.0
    assert _f(data["actual_margin_inr"]) == 128000.0
    assert len(data["per_project"]) == 2
    for item in data["per_project"]:
        assert _f(item["total_cost_inr"]) == 24000.0
        assert _f(item["projected_revenue_inr"]) == 88000.0


@pytest.mark.asyncio
async def test_client_financials_empty_when_no_projects(client: AsyncClient, db: AsyncSession):
    await login_as(client)
    cl = await _create_client_entity(client)

    resp = await client.get(f"/api/v1/clients/{cl['id']}/financials")
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert _f(data["total_cost_inr"]) == 0.0
    assert _f(data["total_projected_revenue_inr"]) == 0.0
    assert data["per_project"] == []


@pytest.mark.asyncio
async def test_client_financials_not_found(client: AsyncClient, db: AsyncSession):
    await login_as(client)
    resp = await client.get(f"/api/v1/clients/{uuid.uuid4()}/financials")
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_client_financials_dm_scoped_to_own_portfolio(client: AsyncClient, db: AsyncSession):
    await login_as(client)
    cl = await _create_client_entity(client)
    dm = await _create_resource(client, "DM Person")
    other_dm = await _create_resource(client, "Other DM")
    pm = await _create_resource(client, "PM Person")

    await _setup_project(client, db, cl["id"], dm["id"], pm["id"])
    await login_as(client)
    await _setup_project(client, db, cl["id"], other_dm["id"], pm["id"])

    await login_as(client)
    dm_user = await create_test_user(db, "DM", email=f"dm-{uuid.uuid4().hex[:6]}@test.com")
    dm_user.resource_id = uuid.UUID(dm["id"])
    await db.commit()
    await client.post(
        "/api/v1/auth/login", json={"email": dm_user.email, "password": "TestPass123"}
    )

    resp = await client.get(f"/api/v1/clients/{cl['id']}/financials")
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert len(data["per_project"]) == 1


@pytest.mark.asyncio
async def test_client_financials_pm_forbidden(client: AsyncClient, db: AsyncSession):
    await login_as(client)
    cl = await _create_client_entity(client)

    await login_as_role(client, db, "PM")
    resp = await client.get(f"/api/v1/clients/{cl['id']}/financials")
    assert resp.status_code == 403


@pytest.mark.asyncio
async def test_ceo_sees_company_financials_with_revenue_by_type(
    client: AsyncClient, db: AsyncSession
):
    await login_as(client)
    cl = await _create_client_entity(client)
    dm = await _create_resource(client, "DM Person")
    pm = await _create_resource(client, "PM Person")

    await _setup_project(client, db, cl["id"], dm["id"], pm["id"], project_type="TIME_AND_MATERIAL")
    await login_as(client)
    await _setup_project(client, db, cl["id"], dm["id"], pm["id"], project_type="FIXED_PRICE")

    await login_as(client)
    resp = await client.get("/api/v1/dashboard/financials")
    assert resp.status_code == 200, resp.text
    data = resp.json()["data"]

    assert _f(data["total_resource_cost_inr"]) == 40000.0
    assert _f(data["total_cost_inr"]) == 48000.0
    assert _f(data["total_projected_revenue_inr"]) == 176000.0
    assert _f(data["total_actual_revenue_inr"]) == 176000.0
    assert _f(data["total_projected_margin_inr"]) == 128000.0

    by_type = {item["project_type"]: item for item in data["revenue_by_project_type"]}
    assert _f(by_type["TIME_AND_MATERIAL"]["projected_revenue_inr"]) == 88000.0
    assert _f(by_type["FIXED_PRICE"]["projected_revenue_inr"]) == 88000.0


@pytest.mark.asyncio
async def test_company_financials_empty_when_no_projects(client: AsyncClient, db: AsyncSession):
    await login_as(client)
    resp = await client.get("/api/v1/dashboard/financials")
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert _f(data["total_cost_inr"]) == 0.0
    assert data["revenue_by_project_type"] == []


@pytest.mark.asyncio
async def test_company_financials_dm_scoped_to_own_portfolio(client: AsyncClient, db: AsyncSession):
    await login_as(client)
    cl = await _create_client_entity(client)
    dm = await _create_resource(client, "DM Person")
    other_dm = await _create_resource(client, "Other DM")
    pm = await _create_resource(client, "PM Person")

    await _setup_project(client, db, cl["id"], dm["id"], pm["id"])
    await login_as(client)
    await _setup_project(client, db, cl["id"], other_dm["id"], pm["id"])

    await login_as(client)
    dm_user = await create_test_user(db, "DM", email=f"dm2-{uuid.uuid4().hex[:6]}@test.com")
    dm_user.resource_id = uuid.UUID(dm["id"])
    await db.commit()
    await client.post(
        "/api/v1/auth/login", json={"email": dm_user.email, "password": "TestPass123"}
    )

    resp = await client.get("/api/v1/dashboard/financials")
    assert resp.status_code == 200
    data = resp.json()["data"]
    # DM has NONE on ctc_loaded_cost (see ACCESS-MATRIX.md), but VIEW on billing_rates —
    # projected revenue is visible and scoped to just the DM's own project (88000, not 176000).
    assert _f(data["total_projected_revenue_inr"]) == 88000.0


@pytest.mark.asyncio
async def test_company_financials_pm_forbidden(client: AsyncClient, db: AsyncSession):
    await login_as_role(client, db, "PM")
    resp = await client.get("/api/v1/dashboard/financials")
    assert resp.status_code == 403


@pytest.mark.asyncio
async def test_company_financials_hr_forbidden(client: AsyncClient, db: AsyncSession):
    await login_as_role(client, db, "HR")
    resp = await client.get("/api/v1/dashboard/financials")
    assert resp.status_code == 403
