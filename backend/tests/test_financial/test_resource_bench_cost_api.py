"""Tests for resource bench cost endpoint — VRIP-101.

GET /api/v1/resources/:resourceId/bench-cost.
"""

import uuid
from datetime import date, timedelta

import pytest
from httpx import AsyncClient

from tests.conftest import login_as_role


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


@pytest.mark.asyncio
async def test_bench_cost_never_assigned_uses_date_of_joining(client: AsyncClient, db):
    admin, _ = await login_as_role(client, db, "CEO")
    joined = date.today() - timedelta(days=10)
    resource = await _create_resource(
        admin, date_of_joining=joined.isoformat(), loaded_cost_monthly=66000
    )

    resp = await admin.get(f"/api/v1/resources/{resource['id']}/bench-cost")
    assert resp.status_code == 200, resp.text
    data = resp.json()["data"]
    assert data["days_on_bench"] == 10
    assert data["bench_start_date"] == joined.isoformat()
    assert _f(data["daily_bench_cost_inr"]) == pytest.approx(3000.0)
    assert _f(data["total_bench_cost_inr"]) == pytest.approx(30000.0)


@pytest.mark.asyncio
async def test_bench_cost_after_release_uses_released_at(client: AsyncClient, db):
    admin, _ = await login_as_role(client, db, "CEO")
    dm = await _create_resource(admin, name="DM One")
    pm = await _create_resource(admin, name="PM One")
    resource = await _create_resource(admin, loaded_cost_monthly=44000)
    client_entity = await _create_client_entity(admin)
    project = await _create_project(admin, client_entity["id"], dm["id"], pm["id"])
    assignment = await _create_assignment(admin, project["id"], resource["id"])

    release_resp = await admin.post(f"/api/v1/assignments/{assignment['id']}/release")
    assert release_resp.status_code == 200, release_resp.text

    resp = await admin.get(f"/api/v1/resources/{resource['id']}/bench-cost")
    assert resp.status_code == 200, resp.text
    data = resp.json()["data"]
    assert data["days_on_bench"] == 0
    assert data["bench_start_date"] == date.today().isoformat()


@pytest.mark.asyncio
async def test_bench_cost_returns_null_for_resource_with_active_assignment(
    client: AsyncClient, db
):
    admin, _ = await login_as_role(client, db, "CEO")
    dm = await _create_resource(admin, name="DM Two")
    pm = await _create_resource(admin, name="PM Two")
    resource = await _create_resource(admin, loaded_cost_monthly=44000)
    client_entity = await _create_client_entity(admin)
    project = await _create_project(admin, client_entity["id"], dm["id"], pm["id"])
    await _create_assignment(admin, project["id"], resource["id"])

    resp = await admin.get(f"/api/v1/resources/{resource['id']}/bench-cost")
    assert resp.status_code == 200, resp.text
    assert resp.json()["data"] is None


@pytest.mark.asyncio
async def test_bench_cost_null_loaded_cost_returns_null_cost_fields(
    client: AsyncClient, db
):
    admin, _ = await login_as_role(client, db, "CEO")
    joined = date.today() - timedelta(days=5)
    resource = await _create_resource(admin, date_of_joining=joined.isoformat())

    resp = await admin.get(f"/api/v1/resources/{resource['id']}/bench-cost")
    assert resp.status_code == 200, resp.text
    data = resp.json()["data"]
    assert data["days_on_bench"] == 5
    assert data["daily_bench_cost_inr"] is None
    assert data["total_bench_cost_inr"] is None


@pytest.mark.asyncio
async def test_bench_cost_unauthorized_role_gets_null_financial_fields(
    client: AsyncClient, db
):
    admin, _ = await login_as_role(client, db, "CEO")
    joined = date.today() - timedelta(days=10)
    resource = await _create_resource(
        admin, date_of_joining=joined.isoformat(), loaded_cost_monthly=66000
    )

    dm_client, _ = await login_as_role(client, db, "DM")
    resp = await dm_client.get(f"/api/v1/resources/{resource['id']}/bench-cost")
    assert resp.status_code == 200, resp.text
    data = resp.json()["data"]
    assert data["days_on_bench"] == 10
    assert data["daily_bench_cost_inr"] is None
    assert data["total_bench_cost_inr"] is None


@pytest.mark.asyncio
async def test_bench_cost_forbidden_for_role_without_bench_data_access(
    client: AsyncClient, db
):
    admin, _ = await login_as_role(client, db, "CEO")
    resource = await _create_resource(admin)

    pm_client, _ = await login_as_role(client, db, "PM")
    resp = await pm_client.get(f"/api/v1/resources/{resource['id']}/bench-cost")
    assert resp.status_code == 403, resp.text


@pytest.mark.asyncio
async def test_bench_cost_not_found(client: AsyncClient, db):
    admin, _ = await login_as_role(client, db, "CEO")
    resp = await admin.get(f"/api/v1/resources/{uuid.uuid4()}/bench-cost")
    assert resp.status_code == 404, resp.text
