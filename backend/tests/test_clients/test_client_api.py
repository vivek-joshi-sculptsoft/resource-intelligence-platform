import uuid

import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.audit.models import AuditLog
from tests.conftest import login_as, login_as_role


async def _create_client(client: AsyncClient, **overrides) -> dict:
    payload = {
        "name": overrides.get("name", f"Client-{uuid.uuid4().hex[:6]}"),
        "industry": overrides.get("industry", "Technology"),
        "contact_name": overrides.get("contact_name", "John Doe"),
        "contact_email": overrides.get("contact_email", "john@example.com"),
        "contact_phone": overrides.get("contact_phone", "+91-9876543210"),
        "engagement_start_date": overrides.get("engagement_start_date", "2024-01-01"),
        "notes": overrides.get("notes", "Test client"),
    }
    resp = await client.post("/api/v1/clients", json=payload)
    return resp


# ===== CRUD Happy Paths =====

@pytest.mark.asyncio
async def test_create_client(client: AsyncClient, db: AsyncSession):
    await login_as(client)
    resp = await _create_client(client, name="Acme Corp")
    assert resp.status_code == 201
    data = resp.json()["data"]
    assert data["name"] == "Acme Corp"
    assert data["industry"] == "Technology"
    assert data["dashboard"]["active_project_count"] == 0


@pytest.mark.asyncio
async def test_list_clients(client: AsyncClient, db: AsyncSession):
    await login_as(client)
    await _create_client(client, name="Client-List-A")
    await _create_client(client, name="Client-List-B")

    resp = await client.get("/api/v1/clients")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data["data"]) >= 2
    assert "meta" in data


@pytest.mark.asyncio
async def test_get_client(client: AsyncClient, db: AsyncSession):
    await login_as(client)
    create_resp = await _create_client(client, name="Client-Get")
    cid = create_resp.json()["data"]["id"]

    resp = await client.get(f"/api/v1/clients/{cid}")
    assert resp.status_code == 200
    assert resp.json()["data"]["id"] == cid
    assert "projects" in resp.json()["data"]
    assert "dashboard" in resp.json()["data"]


@pytest.mark.asyncio
async def test_update_client(client: AsyncClient, db: AsyncSession):
    await login_as(client)
    create_resp = await _create_client(client, name="Client-Old")
    cid = create_resp.json()["data"]["id"]

    resp = await client.put(f"/api/v1/clients/{cid}", json={"name": "Client-New"})
    assert resp.status_code == 200
    assert resp.json()["data"]["name"] == "Client-New"


@pytest.mark.asyncio
async def test_deactivate_client(client: AsyncClient, db: AsyncSession):
    await login_as(client)
    create_resp = await _create_client(client, name="Client-Deact")
    cid = create_resp.json()["data"]["id"]

    resp = await client.delete(f"/api/v1/clients/{cid}")
    assert resp.status_code == 200
    assert resp.json()["success"] is True


# ===== Validation =====

@pytest.mark.asyncio
async def test_name_unique(client: AsyncClient, db: AsyncSession):
    await login_as(client)
    await _create_client(client, name="Unique Client Name")
    resp = await _create_client(client, name="Unique Client Name")
    assert resp.status_code == 409


# ===== Access Control =====

@pytest.mark.asyncio
async def test_ceo_can_create(client: AsyncClient, db: AsyncSession):
    await login_as(client)
    resp = await _create_client(client, name="CEO-Client")
    assert resp.status_code == 201


@pytest.mark.asyncio
async def test_dm_cannot_create(client: AsyncClient, db: AsyncSession):
    await login_as_role(client, db, "DM")
    resp = await _create_client(client, name="DM-Client")
    assert resp.status_code == 403


@pytest.mark.asyncio
async def test_engineer_forbidden(client: AsyncClient, db: AsyncSession):
    await login_as_role(client, db, "ENGINEER")
    resp = await client.get("/api/v1/clients")
    assert resp.status_code == 403


@pytest.mark.asyncio
async def test_finance_can_read(client: AsyncClient, db: AsyncSession):
    admin = await login_as(client)
    await _create_client(admin, name="Finance-Visible")

    await login_as_role(client, db, "FINANCE")
    resp = await client.get("/api/v1/clients")
    assert resp.status_code == 200


@pytest.mark.asyncio
async def test_finance_cannot_create(client: AsyncClient, db: AsyncSession):
    await login_as_role(client, db, "FINANCE")
    resp = await _create_client(client, name="Finance-Create")
    assert resp.status_code == 403


# ===== Dashboard =====

@pytest.mark.asyncio
async def test_dashboard_returns_null_financials(client: AsyncClient, db: AsyncSession):
    await login_as(client)
    create_resp = await _create_client(client, name="Dashboard-Test")
    cid = create_resp.json()["data"]["id"]

    resp = await client.get(f"/api/v1/clients/{cid}/dashboard")
    assert resp.status_code == 200
    dash = resp.json()["data"]
    assert dash["total_monthly_billing_inr"] is None
    assert dash["total_cost_inr"] is None
    assert dash["aggregate_margin_inr"] is None


# ===== Pagination & Search =====

@pytest.mark.asyncio
async def test_search_clients(client: AsyncClient, db: AsyncSession):
    await login_as(client)
    await _create_client(client, name="ZZZ Unique Searchable Client")

    resp = await client.get("/api/v1/clients?search=ZZZ+Unique")
    assert resp.status_code == 200
    assert len(resp.json()["data"]) >= 1


@pytest.mark.asyncio
async def test_pagination_clients(client: AsyncClient, db: AsyncSession):
    await login_as(client)
    for i in range(5):
        await _create_client(client, name=f"Paginated-Client-{uuid.uuid4().hex[:4]}")

    resp = await client.get("/api/v1/clients?page=1&limit=2")
    assert resp.status_code == 200
    assert len(resp.json()["data"]) == 2
    assert resp.json()["meta"]["total"] >= 5


# ===== Audit =====

@pytest.mark.asyncio
async def test_audit_log_on_create(client: AsyncClient, db: AsyncSession):
    await login_as(client)
    await _create_client(client, name="Audit-Client")

    logs = await db.execute(
        select(AuditLog).where(
            AuditLog.entity_type == "client",
            AuditLog.action == "CREATE",
        )
    )
    assert len(list(logs.scalars().all())) >= 1
