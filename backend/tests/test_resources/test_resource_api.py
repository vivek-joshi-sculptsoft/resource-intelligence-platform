import uuid

import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.audit.models import AuditLog
from app.modules.resources.models import Resource, ResourceTag
from tests.conftest import create_test_user, login_as, login_as_role


async def _create_resource(client: AsyncClient, **overrides) -> dict:
    payload = {
        "employee_id": overrides.get("employee_id", f"EMP-{uuid.uuid4().hex[:6]}"),
        "name": overrides.get("name", "Test Resource"),
        "designation": overrides.get("designation", "Senior Engineer"),
        "technical_expertise": overrides.get("technical_expertise", "Python"),
        "date_of_joining": overrides.get("date_of_joining", "2024-01-15"),
        "tags": overrides.get("tags", ["python", "fastapi"]),
    }
    if "reporting_manager_id" in overrides:
        payload["reporting_manager_id"] = overrides["reporting_manager_id"]
    if "loaded_cost_monthly" in overrides:
        payload["loaded_cost_monthly"] = overrides["loaded_cost_monthly"]
    resp = await client.post("/api/v1/resources", json=payload)
    return resp


# ===== CRUD Happy Paths =====

@pytest.mark.asyncio
async def test_create_resource(client: AsyncClient, db: AsyncSession):
    await login_as(client)
    resp = await _create_resource(client, employee_id="EMP-001", name="Alice Dev")
    assert resp.status_code == 201
    data = resp.json()["data"]
    assert data["name"] == "Alice Dev"
    assert data["employee_id"] == "EMP-001"
    assert "python" in data["tags"]
    assert data["total_allocation_pct"] == 0


@pytest.mark.asyncio
async def test_list_resources(client: AsyncClient, db: AsyncSession):
    await login_as(client)
    await _create_resource(client, employee_id="EMP-L1", name="Bob")
    await _create_resource(client, employee_id="EMP-L2", name="Carol")

    resp = await client.get("/api/v1/resources")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data["data"]) >= 2
    assert "meta" in data


@pytest.mark.asyncio
async def test_get_resource(client: AsyncClient, db: AsyncSession):
    await login_as(client)
    create_resp = await _create_resource(client, employee_id="EMP-G1")
    rid = create_resp.json()["data"]["id"]

    resp = await client.get(f"/api/v1/resources/{rid}")
    assert resp.status_code == 200
    assert resp.json()["data"]["id"] == rid


@pytest.mark.asyncio
async def test_update_resource(client: AsyncClient, db: AsyncSession):
    await login_as(client)
    create_resp = await _create_resource(client, employee_id="EMP-U1", name="Old Name")
    rid = create_resp.json()["data"]["id"]

    resp = await client.put(f"/api/v1/resources/{rid}", json={"name": "New Name"})
    assert resp.status_code == 200
    assert resp.json()["data"]["name"] == "New Name"


@pytest.mark.asyncio
async def test_deactivate_resource(client: AsyncClient, db: AsyncSession):
    await login_as(client)
    create_resp = await _create_resource(client, employee_id="EMP-D1")
    rid = create_resp.json()["data"]["id"]

    resp = await client.delete(f"/api/v1/resources/{rid}")
    assert resp.status_code == 200
    assert resp.json()["success"] is True

    detail = await client.get(f"/api/v1/resources/{rid}")
    assert detail.json()["data"]["is_active"] is False


# ===== Validation =====

@pytest.mark.asyncio
async def test_employee_id_unique(client: AsyncClient, db: AsyncSession):
    await login_as(client)
    await _create_resource(client, employee_id="EMP-DUP")
    resp = await _create_resource(client, employee_id="EMP-DUP")
    assert resp.status_code == 409


@pytest.mark.asyncio
async def test_self_referencing_manager_blocked(client: AsyncClient, db: AsyncSession):
    await login_as(client)
    create_resp = await _create_resource(client, employee_id="EMP-SELF")
    rid = create_resp.json()["data"]["id"]

    resp = await client.put(f"/api/v1/resources/{rid}", json={"reporting_manager_id": rid})
    assert resp.status_code == 422


# ===== Tags =====

@pytest.mark.asyncio
async def test_add_and_remove_tag(client: AsyncClient, db: AsyncSession):
    await login_as(client)
    create_resp = await _create_resource(client, employee_id="EMP-TAG", tags=[])
    rid = create_resp.json()["data"]["id"]

    add_resp = await client.post(f"/api/v1/resources/{rid}/tags", json={"tag": "react"})
    assert add_resp.status_code == 200
    assert "react" in add_resp.json()["data"]["tags"]

    del_resp = await client.delete(f"/api/v1/resources/{rid}/tags/react")
    assert del_resp.status_code == 200
    assert "react" not in del_resp.json()["data"]["tags"]


# ===== Access Control =====

@pytest.mark.asyncio
async def test_hr_can_create_resource(client: AsyncClient, db: AsyncSession):
    await login_as_role(client, db, "HR")
    resp = await _create_resource(client, employee_id="EMP-HR1")
    assert resp.status_code == 201


@pytest.mark.asyncio
async def test_pm_cannot_create_resource(client: AsyncClient, db: AsyncSession):
    await login_as_role(client, db, "PM")
    resp = await _create_resource(client, employee_id="EMP-PM1")
    assert resp.status_code == 403


@pytest.mark.asyncio
async def test_engineer_sees_only_self(client: AsyncClient, db: AsyncSession):
    c, user = await login_as_role(client, db, "ENGINEER")
    resp = await client.get("/api/v1/resources")
    assert resp.status_code == 200
    for r in resp.json()["data"]:
        if user.resource_id:
            assert r["id"] == str(user.resource_id)


@pytest.mark.asyncio
async def test_loaded_cost_null_for_pm(client: AsyncClient, db: AsyncSession):
    admin_client = await login_as(client)
    create_resp = await _create_resource(admin_client, employee_id="EMP-COST")
    rid = create_resp.json()["data"]["id"]

    await login_as_role(client, db, "PM")
    resp = await client.get(f"/api/v1/resources/{rid}")
    assert resp.status_code == 200
    assert resp.json()["data"]["loaded_cost_monthly"] is None


# ===== Filters =====

@pytest.mark.asyncio
async def test_search_filter(client: AsyncClient, db: AsyncSession):
    await login_as(client)
    await _create_resource(client, employee_id="EMP-SEARCH", name="Unique Searchable Name")

    resp = await client.get("/api/v1/resources?search=Unique+Searchable")
    assert resp.status_code == 200
    assert len(resp.json()["data"]) >= 1


@pytest.mark.asyncio
async def test_search_filter_matches_tags(client: AsyncClient, db: AsyncSession):
    await login_as(client)
    await _create_resource(
        client, employee_id="EMP-TAGSRCH", name="John Doe", tags=["VueJS", "GraphQL"]
    )

    resp = await client.get("/api/v1/resources?search=VueJS")
    assert resp.status_code == 200
    ids = [r["employee_id"] for r in resp.json()["data"]]
    assert "EMP-TAGSRCH" in ids


@pytest.mark.asyncio
async def test_search_filter_tag_case_insensitive(client: AsyncClient, db: AsyncSession):
    await login_as(client)
    await _create_resource(
        client, employee_id="EMP-TAGCI", name="Jane Smith", tags=["Kubernetes"]
    )

    resp = await client.get("/api/v1/resources?search=kubernetes")
    assert resp.status_code == 200
    ids = [r["employee_id"] for r in resp.json()["data"]]
    assert "EMP-TAGCI" in ids


@pytest.mark.asyncio
async def test_search_filter_tag_partial_match(client: AsyncClient, db: AsyncSession):
    await login_as(client)
    await _create_resource(
        client, employee_id="EMP-TAGPART", name="Bob Brown", tags=["TensorFlow"]
    )

    resp = await client.get("/api/v1/resources?search=Tensor")
    assert resp.status_code == 200
    ids = [r["employee_id"] for r in resp.json()["data"]]
    assert "EMP-TAGPART" in ids


@pytest.mark.asyncio
async def test_search_filter_no_tag_match(client: AsyncClient, db: AsyncSession):
    await login_as(client)
    await _create_resource(
        client, employee_id="EMP-TAGNO", name="Alice Green", tags=["Docker"]
    )

    resp = await client.get("/api/v1/resources?search=NonExistentXYZ999")
    assert resp.status_code == 200
    ids = [r["employee_id"] for r in resp.json()["data"]]
    assert "EMP-TAGNO" not in ids


@pytest.mark.asyncio
async def test_search_combined_with_tag_filter(client: AsyncClient, db: AsyncSession):
    await login_as(client)
    await _create_resource(
        client, employee_id="EMP-COMBO", name="Combo Test", tags=["React", "AWS"]
    )

    # search matches via tag "React", exact tag filter also set to "AWS" — both must hold
    resp = await client.get("/api/v1/resources?search=React&tag=AWS")
    assert resp.status_code == 200
    ids = [r["employee_id"] for r in resp.json()["data"]]
    assert "EMP-COMBO" in ids

    # search matches tag "React" but exact tag filter "NonExistent" excludes it
    resp2 = await client.get("/api/v1/resources?search=React&tag=NonExistent")
    assert resp2.status_code == 200
    ids2 = [r["employee_id"] for r in resp2.json()["data"]]
    assert "EMP-COMBO" not in ids2


@pytest.mark.asyncio
async def test_designation_filter(client: AsyncClient, db: AsyncSession):
    await login_as(client)
    await _create_resource(client, employee_id="EMP-DES", designation="QA Lead")

    resp = await client.get("/api/v1/resources?designation=QA+Lead")
    assert resp.status_code == 200
    names = [r["designation"] for r in resp.json()["data"]]
    assert all(d == "QA Lead" for d in names)


# ===== Pagination =====

@pytest.mark.asyncio
async def test_pagination(client: AsyncClient, db: AsyncSession):
    await login_as(client)
    for i in range(5):
        await _create_resource(client, employee_id=f"EMP-PG-{i}")

    resp = await client.get("/api/v1/resources?page=1&limit=2")
    assert resp.status_code == 200
    assert len(resp.json()["data"]) == 2
    assert resp.json()["meta"]["total"] >= 5


# ===== Audit =====

@pytest.mark.asyncio
async def test_audit_log_on_create(client: AsyncClient, db: AsyncSession):
    await login_as(client)
    resp = await _create_resource(client, employee_id="EMP-AUD")
    assert resp.status_code == 201

    logs = await db.execute(
        select(AuditLog).where(
            AuditLog.entity_type == "resource",
            AuditLog.action == "CREATE",
        )
    )
    assert len(list(logs.scalars().all())) >= 1


# ===== loaded_cost_monthly Access Control =====


@pytest.mark.asyncio
async def test_ceo_can_set_loaded_cost_on_create(client: AsyncClient, db: AsyncSession):
    """CEO (resource_profiles EDIT + ctc_loaded_cost VIEW) can set loaded_cost_monthly."""
    await login_as(client)
    resp = await _create_resource(client, employee_id="EMP-COST1", loaded_cost_monthly=150000.00)
    assert resp.status_code == 201
    assert resp.json()["data"]["loaded_cost_monthly"] == 150000.00


@pytest.mark.asyncio
async def test_hr_cannot_set_loaded_cost_on_create(client: AsyncClient, db: AsyncSession):
    """HR has resource_profiles EDIT but ctc_loaded_cost NONE — blocked."""
    await login_as_role(client, db, "HR")
    payload = {
        "employee_id": f"EMP-{uuid.uuid4().hex[:6]}",
        "name": "HR Cost Test",
        "designation": "Engineer",
        "loaded_cost_monthly": 100000.00,
    }
    resp = await client.post("/api/v1/resources", json=payload)
    assert resp.status_code == 403


@pytest.mark.asyncio
async def test_ceo_can_update_loaded_cost(client: AsyncClient, db: AsyncSession):
    """CEO can update loaded_cost_monthly."""
    await login_as(client)
    create_resp = await _create_resource(client, employee_id="EMP-UCOST1")
    rid = create_resp.json()["data"]["id"]

    resp = await client.put(f"/api/v1/resources/{rid}", json={"loaded_cost_monthly": 200000.00})
    assert resp.status_code == 200
    assert resp.json()["data"]["loaded_cost_monthly"] == 200000.00


@pytest.mark.asyncio
async def test_finance_can_update_loaded_cost(client: AsyncClient, db: AsyncSession):
    """Finance has resource_profiles VIEW + ctc_loaded_cost VIEW — can update only cost."""
    await login_as(client)
    create_resp = await _create_resource(client, employee_id="EMP-FCOST1")
    rid = create_resp.json()["data"]["id"]

    await login_as_role(client, db, "FINANCE")
    resp = await client.put(f"/api/v1/resources/{rid}", json={"loaded_cost_monthly": 175000.00})
    assert resp.status_code == 200
    assert resp.json()["data"]["loaded_cost_monthly"] == 175000.00


@pytest.mark.asyncio
async def test_finance_cannot_update_profile_fields(client: AsyncClient, db: AsyncSession):
    """Finance can update cost but NOT name/designation (resource_profiles VIEW not EDIT)."""
    await login_as(client)
    create_resp = await _create_resource(client, employee_id="EMP-FCOST2")
    rid = create_resp.json()["data"]["id"]

    await login_as_role(client, db, "FINANCE")
    resp = await client.put(f"/api/v1/resources/{rid}", json={"name": "Hacker"})
    assert resp.status_code == 403


@pytest.mark.asyncio
async def test_hr_cannot_update_loaded_cost(client: AsyncClient, db: AsyncSession):
    """HR has resource_profiles EDIT but ctc_loaded_cost NONE — cost update blocked."""
    await login_as(client)
    create_resp = await _create_resource(client, employee_id="EMP-HRCOST")
    rid = create_resp.json()["data"]["id"]

    await login_as_role(client, db, "HR")
    resp = await client.put(f"/api/v1/resources/{rid}", json={"loaded_cost_monthly": 100000.00})
    assert resp.status_code == 403


@pytest.mark.asyncio
async def test_dm_sees_null_loaded_cost(client: AsyncClient, db: AsyncSession):
    """DM has ctc_loaded_cost NONE — field returns null."""
    await login_as(client)
    create_resp = await _create_resource(
        client, employee_id="EMP-DMCOST", loaded_cost_monthly=120000.00
    )
    rid = create_resp.json()["data"]["id"]

    await login_as_role(client, db, "DM")
    resp = await client.get(f"/api/v1/resources/{rid}")
    assert resp.status_code == 200
    assert resp.json()["data"]["loaded_cost_monthly"] is None


@pytest.mark.asyncio
async def test_loaded_cost_null_in_list_for_hr(client: AsyncClient, db: AsyncSession):
    """HR sees null for loaded_cost_monthly in list view."""
    await login_as(client)
    await _create_resource(client, employee_id="EMP-HRCL", loaded_cost_monthly=130000.00)

    await login_as_role(client, db, "HR")
    resp = await client.get("/api/v1/resources")
    assert resp.status_code == 200
    for r in resp.json()["data"]:
        assert r["loaded_cost_monthly"] is None


@pytest.mark.asyncio
async def test_ceo_sees_loaded_cost_in_list(client: AsyncClient, db: AsyncSession):
    """CEO can see loaded_cost_monthly in list view."""
    await login_as(client)
    await _create_resource(client, employee_id="EMP-CEOL", loaded_cost_monthly=140000.00)

    resp = await client.get("/api/v1/resources?search=EMP-CEOL")
    assert resp.status_code == 200
    items = resp.json()["data"]
    assert len(items) >= 1
    assert items[0]["loaded_cost_monthly"] == 140000.00


@pytest.mark.asyncio
async def test_audit_log_on_loaded_cost_update(client: AsyncClient, db: AsyncSession):
    """Audit log captures loaded_cost_monthly changes."""
    await login_as(client)
    create_resp = await _create_resource(client, employee_id="EMP-ACOST")
    rid = create_resp.json()["data"]["id"]

    await client.put(f"/api/v1/resources/{rid}", json={"loaded_cost_monthly": 250000.00})

    logs = await db.execute(
        select(AuditLog).where(
            AuditLog.entity_type == "resource",
            AuditLog.action == "UPDATE",
        )
    )
    audit_entries = list(logs.scalars().all())
    cost_logged = any("loaded_cost_monthly" in (entry.field_name or "") for entry in audit_entries)
    assert cost_logged
