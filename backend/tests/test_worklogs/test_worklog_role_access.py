"""Tests for worklog write access across all 7 roles — See VRIP-131 AC, shared/ACCESS-MATRIX.md (worklogs)."""

import uuid
from datetime import date, timedelta

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.allocations.models import Assignment
from app.modules.auth.models import User
from app.modules.clients.models import Client
from app.modules.projects.models import Project
from app.modules.resources.models import Resource
from tests.conftest import create_test_user

BASE_URL = "/api/v1/worklogs"

# Roles with EDIT on worklogs (self-scoped) per shared/ACCESS-MATRIX.md
EDIT_ROLES = ["CEO", "CTO", "DM", "PM", "ENGINEER"]
# Roles with VIEW-only on worklogs — cannot log hours
VIEW_ONLY_ROLES = ["FINANCE", "HR"]


async def _seed_resource(db: AsyncSession, name: str, **kwargs) -> Resource:
    r = Resource(
        id=uuid.uuid4(),
        employee_id=f"EMP-{uuid.uuid4().hex[:6]}",
        name=name,
        designation=kwargs.get("designation", "Developer"),
        date_of_joining=date.today() - timedelta(days=90),
        is_active=True,
    )
    db.add(r)
    await db.flush()
    return r


async def _seed_client(db: AsyncSession) -> Client:
    c = Client(id=uuid.uuid4(), name=f"Client-{uuid.uuid4().hex[:4]}", is_active=True)
    db.add(c)
    await db.flush()
    return c


async def _seed_project(db: AsyncSession, client_id, dm_id, pm_id, **kwargs) -> Project:
    p = Project(
        id=uuid.uuid4(),
        name=kwargs.get("name", f"Proj-{uuid.uuid4().hex[:4]}"),
        client_id=client_id,
        dm_id=dm_id,
        pm_id=pm_id,
        worklog_enabled=True,
        status="ACTIVE",
        is_active=True,
    )
    db.add(p)
    await db.flush()
    return p


async def _seed_assignment(db: AsyncSession, project_id, resource_id, **kwargs) -> Assignment:
    a = Assignment(
        id=uuid.uuid4(),
        project_id=project_id,
        resource_id=resource_id,
        allocation_pct=kwargs.get("allocation_pct", 100),
        billability_pct=kwargs.get("billability_pct", 100),
        start_date=kwargs.get("start_date", date.today() - timedelta(days=60)),
        end_date=kwargs.get("end_date"),
        status=kwargs.get("status", "ACTIVE"),
    )
    db.add(a)
    await db.flush()
    return a


async def _setup_role_with_assignment(db: AsyncSession, client: AsyncClient, role_code: str) -> tuple[AsyncClient, Resource, Project, User]:
    """Create a user of the given role, linked to a resource with an ACTIVE assignment."""
    dm = await _seed_resource(db, f"DM-{role_code}")
    resource = await _seed_resource(db, f"{role_code} Res")
    cl = await _seed_client(db)
    project = await _seed_project(db, cl.id, dm.id, dm.id, name=f"Proj-{role_code}")
    await _seed_assignment(db, project.id, resource.id)
    await db.commit()

    user = await create_test_user(db, role_code, name=f"{role_code} User")
    user.resource_id = resource.id
    await db.commit()
    resp = await client.post("/api/v1/auth/login", json={"email": user.email, "password": "TestPass123"})
    assert resp.status_code == 200
    return client, resource, project, user


# ──────────────────────────────────────────────
# POST /api/v1/worklogs — EDIT roles succeed
# ──────────────────────────────────────────────


@pytest.mark.parametrize("role_code", EDIT_ROLES)
@pytest.mark.asyncio
async def test_create_worklog_succeeds_for_edit_role(client: AsyncClient, db: AsyncSession, role_code: str):
    client, resource, project, _ = await _setup_role_with_assignment(db, client, role_code)
    resp = await client.post(BASE_URL, json={
        "project_id": str(project.id),
        "log_date": str(date.today()),
        "hours": 4.0,
        "note": f"{role_code} logging hours",
    })
    assert resp.status_code == 201, resp.text
    data = resp.json()["data"]
    assert data["resource"]["id"] == str(resource.id)


# ──────────────────────────────────────────────
# POST/PUT/DELETE /api/v1/worklogs — VIEW-only roles get 403
# ──────────────────────────────────────────────


@pytest.mark.parametrize("role_code", VIEW_ONLY_ROLES)
@pytest.mark.asyncio
async def test_create_worklog_forbidden_for_view_only_role(client: AsyncClient, db: AsyncSession, role_code: str):
    client, resource, project, _ = await _setup_role_with_assignment(db, client, role_code)
    resp = await client.post(BASE_URL, json={
        "project_id": str(project.id),
        "log_date": str(date.today()),
        "hours": 4.0,
    })
    assert resp.status_code == 403


@pytest.mark.parametrize("role_code", VIEW_ONLY_ROLES)
@pytest.mark.asyncio
async def test_update_worklog_forbidden_for_view_only_role(client: AsyncClient, db: AsyncSession, role_code: str):
    # Create the entry as an EDIT-capable engineer first, then attempt update as VIEW-only role.
    engineer_client, _, project, _ = await _setup_role_with_assignment(db, client, "ENGINEER")
    create_resp = await engineer_client.post(BASE_URL, json={
        "project_id": str(project.id),
        "log_date": str(date.today()),
        "hours": 4.0,
    })
    wl_id = create_resp.json()["data"]["id"]

    user = await create_test_user(db, role_code, name=f"{role_code} Updater")
    await db.commit()
    resp = await client.post("/api/v1/auth/login", json={"email": user.email, "password": "TestPass123"})
    assert resp.status_code == 200

    resp = await client.put(f"{BASE_URL}/{wl_id}", json={"hours": 6.0})
    assert resp.status_code == 403


@pytest.mark.parametrize("role_code", VIEW_ONLY_ROLES)
@pytest.mark.asyncio
async def test_delete_worklog_forbidden_for_view_only_role(client: AsyncClient, db: AsyncSession, role_code: str):
    engineer_client, _, project, _ = await _setup_role_with_assignment(db, client, "ENGINEER")
    create_resp = await engineer_client.post(BASE_URL, json={
        "project_id": str(project.id),
        "log_date": str(date.today()),
        "hours": 4.0,
    })
    wl_id = create_resp.json()["data"]["id"]

    user = await create_test_user(db, role_code, name=f"{role_code} Deleter")
    await db.commit()
    resp = await client.post("/api/v1/auth/login", json={"email": user.email, "password": "TestPass123"})
    assert resp.status_code == 200

    resp = await client.delete(f"{BASE_URL}/{wl_id}")
    assert resp.status_code == 403
