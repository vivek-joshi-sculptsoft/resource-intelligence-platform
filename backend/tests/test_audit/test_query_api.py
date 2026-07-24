"""Integration tests for GET /api/v1/audit-logs. See FSD §13."""
import uuid
from datetime import datetime, timedelta, timezone

import pytest
from httpx import AsyncClient

from app.modules.audit.models import AuditAction, AuditLog
from app.modules.auth.models import User
from app.modules.clients.models import Client
from app.modules.projects.models import Project
from app.modules.resources.models import Resource
from app.modules.allocations.models import Assignment
from tests.conftest import create_test_user, login_as, login_as_role, test_session_factory

ENDPOINT = "/api/v1/audit-logs"


async def _seed_audit_data(project_id: uuid.UUID | None = None, resource_id: uuid.UUID | None = None):
    """Create audit log entries + supporting entities for tests."""
    async with test_session_factory() as db:
        # Create resources for DM and PM
        dm_resource_id = uuid.uuid4()
        pm_resource_id = uuid.uuid4()
        engineer_resource_id = uuid.uuid4()
        suffix = uuid.uuid4().hex[:8]

        dm_resource = Resource(
            id=dm_resource_id, name="DM Resource", employee_id=f"EMP-DM-{suffix}",
            designation="DM",
        )
        pm_resource = Resource(
            id=pm_resource_id, name="PM Resource", employee_id=f"EMP-PM-{suffix}",
            designation="PM",
        )
        eng_resource = Resource(
            id=engineer_resource_id, name="Eng Resource", employee_id=f"EMP-ENG-{suffix}",
            designation="Engineer",
        )
        db.add_all([dm_resource, pm_resource, eng_resource])
        await db.flush()

        client_id = uuid.uuid4()
        client_entity = Client(id=client_id, name=f"Audit Test Client {suffix}")
        db.add(client_entity)
        await db.flush()

        # Create project owned by DM
        pid = project_id or uuid.uuid4()
        project = Project(
            id=pid, name="Audit Test Project",
            client_id=client_id,
            status="ACTIVE", type="TIME_AND_MATERIAL",
            dm_id=dm_resource_id, pm_id=pm_resource_id,
        )
        db.add(project)
        await db.flush()

        # Create assignment on that project
        assign_id = uuid.uuid4()
        assignment = Assignment(
            id=assign_id, project_id=pid, resource_id=engineer_resource_id,
            allocation_pct=100, start_date=datetime.now(timezone.utc).date(),
            status="ACTIVE",
        )
        db.add(assignment)
        await db.flush()

        # Create audit log entries
        user_id = uuid.uuid4()
        now = datetime.now(timezone.utc)

        entries = [
            AuditLog(
                entity_type="Project", entity_id=pid,
                action=AuditAction.CREATE, field_name=None,
                old_value=None, new_value='{"name": "Audit Test Project"}',
                changed_by=user_id, changed_at=now - timedelta(days=5),
            ),
            AuditLog(
                entity_type="Project", entity_id=pid,
                action=AuditAction.UPDATE, field_name="status",
                old_value='"DRAFT"', new_value='"ACTIVE"',
                changed_by=user_id, changed_at=now - timedelta(days=3),
            ),
            AuditLog(
                entity_type="Assignment", entity_id=assign_id,
                action=AuditAction.CREATE, field_name=None,
                old_value=None, new_value='{"allocation_pct": 100}',
                changed_by=user_id, changed_at=now - timedelta(days=2),
            ),
            AuditLog(
                entity_type="Resource", entity_id=engineer_resource_id,
                action=AuditAction.UPDATE, field_name="designation",
                old_value='"Junior"', new_value='"Senior"',
                changed_by=user_id, changed_at=now - timedelta(days=1),
            ),
        ]
        db.add_all(entries)
        await db.commit()

        return {
            "project_id": pid,
            "assign_id": assign_id,
            "dm_resource_id": dm_resource_id,
            "pm_resource_id": pm_resource_id,
            "engineer_resource_id": engineer_resource_id,
            "user_id": user_id,
        }


@pytest.mark.asyncio
async def test_ceo_sees_all_audit_logs(client: AsyncClient, db):
    data = await _seed_audit_data()
    await login_as(client)
    resp = await client.get(ENDPOINT)
    assert resp.status_code == 200
    body = resp.json()
    assert len(body["data"]) >= 4
    assert "meta" in body
    assert body["meta"]["page"] == 1


@pytest.mark.asyncio
async def test_cto_sees_all_audit_logs(client: AsyncClient, db):
    await _seed_audit_data()
    await login_as_role(client, db, "CTO")
    resp = await client.get(ENDPOINT)
    assert resp.status_code == 200
    assert len(resp.json()["data"]) >= 4


@pytest.mark.asyncio
async def test_finance_gets_403(client: AsyncClient, db):
    await login_as_role(client, db, "FINANCE")
    resp = await client.get(ENDPOINT)
    assert resp.status_code == 403


@pytest.mark.asyncio
async def test_hr_gets_403(client: AsyncClient, db):
    await login_as_role(client, db, "HR")
    resp = await client.get(ENDPOINT)
    assert resp.status_code == 403


@pytest.mark.asyncio
async def test_engineer_gets_403(client: AsyncClient, db):
    await login_as_role(client, db, "ENGINEER")
    resp = await client.get(ENDPOINT)
    assert resp.status_code == 403


@pytest.mark.asyncio
async def test_filter_by_entity_type(client: AsyncClient, db):
    await _seed_audit_data()
    await login_as(client)
    resp = await client.get(ENDPOINT, params={"entity_type": "Project"})
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert all(item["entity_type"] == "Project" for item in data)


@pytest.mark.asyncio
async def test_filter_by_entity_id(client: AsyncClient, db):
    seed = await _seed_audit_data()
    await login_as(client)
    resp = await client.get(ENDPOINT, params={"entity_id": str(seed["project_id"])})
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert all(item["entity_id"] == str(seed["project_id"]) for item in data)


@pytest.mark.asyncio
async def test_filter_by_date_range(client: AsyncClient, db):
    await _seed_audit_data()
    await login_as(client)
    now = datetime.now(timezone.utc)
    start = (now - timedelta(days=4)).strftime("%Y-%m-%d")
    end = (now - timedelta(days=2)).strftime("%Y-%m-%d")
    resp = await client.get(ENDPOINT, params={"start_date": start, "end_date": end})
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert len(data) >= 1


@pytest.mark.asyncio
async def test_pagination(client: AsyncClient, db):
    await _seed_audit_data()
    await login_as(client)
    resp = await client.get(ENDPOINT, params={"page": 1, "limit": 2})
    assert resp.status_code == 200
    body = resp.json()
    assert len(body["data"]) <= 2
    assert body["meta"]["limit"] == 2


@pytest.mark.asyncio
async def test_sort_ascending(client: AsyncClient, db):
    await _seed_audit_data()
    await login_as(client)
    resp = await client.get(ENDPOINT, params={"sort": "asc"})
    assert resp.status_code == 200
    data = resp.json()["data"]
    if len(data) >= 2:
        assert data[0]["changed_at"] <= data[1]["changed_at"]


@pytest.mark.asyncio
async def test_default_sort_descending(client: AsyncClient, db):
    await _seed_audit_data()
    await login_as(client)
    resp = await client.get(ENDPOINT)
    assert resp.status_code == 200
    data = resp.json()["data"]
    if len(data) >= 2:
        assert data[0]["changed_at"] >= data[1]["changed_at"]


@pytest.mark.asyncio
async def test_changed_by_is_nested_object(client: AsyncClient, db):
    await _seed_audit_data()
    await login_as(client)
    resp = await client.get(ENDPOINT)
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert len(data) > 0
    first = data[0]
    assert "changed_by" in first
    assert "id" in first["changed_by"]
    assert "name" in first["changed_by"]


@pytest.mark.asyncio
async def test_old_new_values_parsed_not_raw_json(client: AsyncClient, db):
    await _seed_audit_data()
    await login_as(client)
    resp = await client.get(ENDPOINT, params={"entity_type": "Project"})
    assert resp.status_code == 200
    data = resp.json()["data"]
    update_entries = [d for d in data if d["action"] == "UPDATE"]
    if update_entries:
        entry = update_entries[0]
        assert entry["old_value"] != '"DRAFT"'
        assert isinstance(entry["old_value"], str)


@pytest.mark.asyncio
async def test_entity_history_endpoint(client: AsyncClient, db):
    seed = await _seed_audit_data()
    await login_as(client)
    resp = await client.get(f"{ENDPOINT}/Project/{seed['project_id']}")
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert len(data) >= 2
    assert all(item["entity_type"] == "Project" for item in data)


@pytest.mark.asyncio
async def test_dm_sees_portfolio_audit_logs(client: AsyncClient, db):
    seed = await _seed_audit_data()
    # Create DM user linked to the DM resource
    dm_user = await create_test_user(db, "DM", email="dm-audit@test.com")
    from sqlalchemy import update
    from app.modules.auth.models import User as UserModel
    await db.execute(
        update(UserModel).where(UserModel.id == dm_user.id).values(resource_id=seed["dm_resource_id"])
    )
    await db.commit()

    await client.post("/api/v1/auth/login", json={"email": "dm-audit@test.com", "password": "TestPass123"})
    resp = await client.get(ENDPOINT)
    assert resp.status_code == 200
    data = resp.json()["data"]
    # DM should see audit logs for entities in their portfolio
    entity_types = {item["entity_type"] for item in data}
    assert len(data) >= 1


@pytest.mark.asyncio
async def test_dm_cannot_see_other_portfolio(client: AsyncClient, db):
    await _seed_audit_data()
    # Create a DM with a different resource_id (not linked to any project)
    other_resource_id = uuid.uuid4()
    async with test_session_factory() as s:
        other_resource = Resource(
            id=other_resource_id, name="Other DM", employee_id=f"EMP-OTH-{uuid.uuid4().hex[:8]}",
            designation="DM",
        )
        s.add(other_resource)
        await s.commit()

    dm_user = await create_test_user(db, "DM", email="other-dm-audit@test.com")
    from sqlalchemy import update
    from app.modules.auth.models import User as UserModel
    await db.execute(
        update(UserModel).where(UserModel.id == dm_user.id).values(resource_id=other_resource_id)
    )
    await db.commit()

    await client.post("/api/v1/auth/login", json={"email": "other-dm-audit@test.com", "password": "TestPass123"})
    resp = await client.get(ENDPOINT)
    assert resp.status_code == 200
    # Should see 0 logs since they have no portfolio
    assert len(resp.json()["data"]) == 0


@pytest.mark.asyncio
async def test_empty_result(client: AsyncClient, db):
    await login_as(client)
    resp = await client.get(ENDPOINT, params={"entity_type": "NonExistentType"})
    assert resp.status_code == 200
    body = resp.json()
    assert body["data"] == []
    assert body["meta"]["total"] == 0


@pytest.mark.asyncio
async def test_entity_history_dm_forbidden_for_other_portfolio(client: AsyncClient, db):
    seed = await _seed_audit_data()
    # DM with no portfolio
    other_resource_id = uuid.uuid4()
    async with test_session_factory() as s:
        s.add(Resource(
            id=other_resource_id, name="No Portfolio DM", employee_id=f"EMP-NP-{uuid.uuid4().hex[:8]}",
            designation="DM",
        ))
        await s.commit()

    dm_user = await create_test_user(db, "DM", email="noportfolio-dm@test.com")
    from sqlalchemy import update
    from app.modules.auth.models import User as UserModel
    await db.execute(
        update(UserModel).where(UserModel.id == dm_user.id).values(resource_id=other_resource_id)
    )
    await db.commit()

    await client.post("/api/v1/auth/login", json={"email": "noportfolio-dm@test.com", "password": "TestPass123"})
    resp = await client.get(f"{ENDPOINT}/Project/{seed['project_id']}")
    assert resp.status_code == 403
