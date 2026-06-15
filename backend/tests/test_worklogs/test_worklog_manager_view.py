"""Tests for Worklog manager view endpoints — See VRIP-73 AC."""

import uuid
from datetime import date, timedelta

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.allocations.models import Assignment
from app.modules.clients.models import Client
from app.modules.projects.models import Project
from app.modules.resources.models import Resource
from app.modules.worklogs.models import Worklog
from tests.conftest import create_test_user, login_as, login_as_role


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
        allocation_pct=100,
        billability_pct=100,
        start_date=date.today() - timedelta(days=60),
        end_date=kwargs.get("end_date"),
        status="ACTIVE",
    )
    db.add(a)
    await db.flush()
    return a


async def _seed_worklog(db: AsyncSession, resource_id, project_id, days_ago=1, hours=4.0) -> Worklog:
    w = Worklog(
        id=uuid.uuid4(),
        resource_id=resource_id,
        project_id=project_id,
        log_date=date.today() - timedelta(days=days_ago),
        hours=hours,
        note=f"Work on day -{days_ago}",
    )
    db.add(w)
    await db.flush()
    return w


async def _setup_portfolio(db: AsyncSession, client_http: AsyncClient):
    """Create DM with resource, project, engineer with assignment and worklogs."""
    dm_res = await _seed_resource(db, "DM Manager")
    pm_res = await _seed_resource(db, "PM Manager")
    engineer_res = await _seed_resource(db, "Engineer A")
    cl = await _seed_client(db)
    project = await _seed_project(db, cl.id, dm_res.id, pm_res.id, name="Portfolio Proj")
    await _seed_assignment(db, project.id, engineer_res.id)
    await _seed_worklog(db, engineer_res.id, project.id, days_ago=1)
    await _seed_worklog(db, engineer_res.id, project.id, days_ago=2)
    await _seed_worklog(db, engineer_res.id, project.id, days_ago=3)
    await db.commit()
    return dm_res, pm_res, engineer_res, project


# ──────────────────────────────────────────────
# GET /api/v1/projects/:projectId/worklogs
# ──────────────────────────────────────────────


@pytest.mark.asyncio
async def test_project_worklogs_ceo_access(client: AsyncClient, db: AsyncSession):
    dm_res, _, eng_res, project = await _setup_portfolio(db, client)
    await login_as(client)
    resp = await client.get(f"/api/v1/projects/{project.id}/worklogs")
    assert resp.status_code == 200
    body = resp.json()
    assert body["total"] == 3
    assert len(body["data"]) == 3
    assert body["data"][0]["resource"]["name"] == "Engineer A"
    assert body["data"][0]["project"]["name"] == "Portfolio Proj"


@pytest.mark.asyncio
async def test_project_worklogs_cto_access(client: AsyncClient, db: AsyncSession):
    _, _, _, project = await _setup_portfolio(db, client)
    client, _ = await login_as_role(client, db, "CTO")
    resp = await client.get(f"/api/v1/projects/{project.id}/worklogs")
    assert resp.status_code == 200
    assert resp.json()["total"] == 3


@pytest.mark.asyncio
async def test_project_worklogs_dm_own_portfolio(client: AsyncClient, db: AsyncSession):
    dm_res, _, _, project = await _setup_portfolio(db, client)
    dm_user = await create_test_user(db, "DM", name="DM User")
    dm_user.resource_id = dm_res.id
    await db.commit()
    await client.post("/api/v1/auth/login", json={"email": dm_user.email, "password": "TestPass123"})

    resp = await client.get(f"/api/v1/projects/{project.id}/worklogs")
    assert resp.status_code == 200
    assert resp.json()["total"] == 3


@pytest.mark.asyncio
async def test_project_worklogs_pm_own_portfolio(client: AsyncClient, db: AsyncSession):
    _, pm_res, _, project = await _setup_portfolio(db, client)
    pm_user = await create_test_user(db, "PM", name="PM User")
    pm_user.resource_id = pm_res.id
    await db.commit()
    await client.post("/api/v1/auth/login", json={"email": pm_user.email, "password": "TestPass123"})

    resp = await client.get(f"/api/v1/projects/{project.id}/worklogs")
    assert resp.status_code == 200
    assert resp.json()["total"] == 3


@pytest.mark.asyncio
async def test_project_worklogs_dm_other_portfolio_forbidden(client: AsyncClient, db: AsyncSession):
    """DM cannot view worklogs for project they don't manage."""
    _, _, _, project = await _setup_portfolio(db, client)
    other_dm_res = await _seed_resource(db, "Other DM")
    await db.commit()
    dm_user = await create_test_user(db, "DM", name="Other DM User")
    dm_user.resource_id = other_dm_res.id
    await db.commit()
    await client.post("/api/v1/auth/login", json={"email": dm_user.email, "password": "TestPass123"})

    resp = await client.get(f"/api/v1/projects/{project.id}/worklogs")
    assert resp.status_code == 403


@pytest.mark.asyncio
async def test_project_worklogs_engineer_forbidden(client: AsyncClient, db: AsyncSession):
    """Engineer with SELF_ONLY scope cannot view project-level worklogs."""
    _, _, eng_res, project = await _setup_portfolio(db, client)
    eng_user = await create_test_user(db, "ENGINEER", name="Eng User")
    eng_user.resource_id = eng_res.id
    await db.commit()
    await client.post("/api/v1/auth/login", json={"email": eng_user.email, "password": "TestPass123"})

    # SELF_ONLY scope — project worklogs endpoint should check: is the resource looking at their own?
    # Actually per seed, ENGINEER has EDIT+SELF_ONLY — they can't view project worklogs unless it's their own resource
    # The project worklogs endpoint doesn't filter by SELF_ONLY resource — it shows ALL resource entries for the project
    # So SELF_ONLY users shouldn't access this endpoint for arbitrary projects
    # Let's verify: engineer trying to view project worklogs
    resp = await client.get(f"/api/v1/projects/{project.id}/worklogs")
    # SELF_ONLY scope on project worklogs is ambiguous — but the endpoint checks OWN_PORTFOLIO
    # ENGINEER scope is SELF_ONLY which is neither ALL nor OWN_PORTFOLIO
    # The endpoint should handle this: SELF_ONLY users shouldn't see all project worklogs
    # check_access will pass (EDIT access), but the scope is SELF_ONLY
    # We need to ensure SELF_ONLY users can't view project-level worklogs
    # Since is_own_portfolio is False and is_all is False, we should add a check
    assert resp.status_code == 403


@pytest.mark.asyncio
async def test_project_worklogs_finance_forbidden(client: AsyncClient, db: AsyncSession):
    _, _, _, project = await _setup_portfolio(db, client)
    client, _ = await login_as_role(client, db, "FINANCE")
    resp = await client.get(f"/api/v1/projects/{project.id}/worklogs")
    assert resp.status_code == 403


@pytest.mark.asyncio
async def test_project_worklogs_hr_forbidden(client: AsyncClient, db: AsyncSession):
    _, _, _, project = await _setup_portfolio(db, client)
    client, _ = await login_as_role(client, db, "HR")
    resp = await client.get(f"/api/v1/projects/{project.id}/worklogs")
    assert resp.status_code == 403


@pytest.mark.asyncio
async def test_project_worklogs_unauthenticated(client: AsyncClient, db: AsyncSession):
    _, _, _, project = await _setup_portfolio(db, client)
    resp = await client.get(f"/api/v1/projects/{project.id}/worklogs")
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_project_worklogs_not_found(client: AsyncClient, db: AsyncSession):
    await login_as(client)
    resp = await client.get(f"/api/v1/projects/{uuid.uuid4()}/worklogs")
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_project_worklogs_filter_by_resource(client: AsyncClient, db: AsyncSession):
    dm_res, pm_res, eng_res, project = await _setup_portfolio(db, client)
    # Add second engineer with worklogs
    eng2 = await _seed_resource(db, "Engineer B")
    await _seed_assignment(db, project.id, eng2.id)
    await _seed_worklog(db, eng2.id, project.id, days_ago=1, hours=3.0)
    await db.commit()

    await login_as(client)
    resp = await client.get(f"/api/v1/projects/{project.id}/worklogs?resource_id={eng_res.id}")
    assert resp.status_code == 200
    assert resp.json()["total"] == 3  # Only Engineer A's worklogs

    resp2 = await client.get(f"/api/v1/projects/{project.id}/worklogs?resource_id={eng2.id}")
    assert resp2.json()["total"] == 1  # Only Engineer B


@pytest.mark.asyncio
async def test_project_worklogs_filter_by_date(client: AsyncClient, db: AsyncSession):
    _, _, _, project = await _setup_portfolio(db, client)
    await login_as(client)

    start = str(date.today() - timedelta(days=2))
    end = str(date.today() - timedelta(days=1))
    resp = await client.get(f"/api/v1/projects/{project.id}/worklogs?start_date={start}&end_date={end}")
    assert resp.status_code == 200
    assert resp.json()["total"] == 2


@pytest.mark.asyncio
async def test_project_worklogs_pagination(client: AsyncClient, db: AsyncSession):
    _, _, _, project = await _setup_portfolio(db, client)
    await login_as(client)
    resp = await client.get(f"/api/v1/projects/{project.id}/worklogs?page=1&limit=2")
    assert resp.status_code == 200
    body = resp.json()
    assert body["total"] == 3
    assert len(body["data"]) == 2


# ──────────────────────────────────────────────
# GET /api/v1/resources/:resourceId/worklogs
# ──────────────────────────────────────────────


@pytest.mark.asyncio
async def test_resource_worklogs_ceo_access(client: AsyncClient, db: AsyncSession):
    _, _, eng_res, _ = await _setup_portfolio(db, client)
    await login_as(client)
    resp = await client.get(f"/api/v1/resources/{eng_res.id}/worklogs")
    assert resp.status_code == 200
    assert resp.json()["total"] == 3


@pytest.mark.asyncio
async def test_resource_worklogs_cto_access(client: AsyncClient, db: AsyncSession):
    _, _, eng_res, _ = await _setup_portfolio(db, client)
    client, _ = await login_as_role(client, db, "CTO")
    resp = await client.get(f"/api/v1/resources/{eng_res.id}/worklogs")
    assert resp.status_code == 200


@pytest.mark.asyncio
async def test_resource_worklogs_dm_own_portfolio(client: AsyncClient, db: AsyncSession):
    dm_res, _, eng_res, _ = await _setup_portfolio(db, client)
    dm_user = await create_test_user(db, "DM", name="DM Res View")
    dm_user.resource_id = dm_res.id
    await db.commit()
    await client.post("/api/v1/auth/login", json={"email": dm_user.email, "password": "TestPass123"})

    resp = await client.get(f"/api/v1/resources/{eng_res.id}/worklogs")
    assert resp.status_code == 200
    assert resp.json()["total"] == 3


@pytest.mark.asyncio
async def test_resource_worklogs_dm_other_portfolio_forbidden(client: AsyncClient, db: AsyncSession):
    _, _, eng_res, _ = await _setup_portfolio(db, client)
    other_dm = await _seed_resource(db, "Unrelated DM")
    await db.commit()
    dm_user = await create_test_user(db, "DM", name="Unrelated DM User")
    dm_user.resource_id = other_dm.id
    await db.commit()
    await client.post("/api/v1/auth/login", json={"email": dm_user.email, "password": "TestPass123"})

    resp = await client.get(f"/api/v1/resources/{eng_res.id}/worklogs")
    assert resp.status_code == 403


@pytest.mark.asyncio
async def test_resource_worklogs_engineer_own(client: AsyncClient, db: AsyncSession):
    """Engineer can view their own worklogs via resource endpoint."""
    _, _, eng_res, _ = await _setup_portfolio(db, client)
    eng_user = await create_test_user(db, "ENGINEER", name="Self Eng")
    eng_user.resource_id = eng_res.id
    await db.commit()
    await client.post("/api/v1/auth/login", json={"email": eng_user.email, "password": "TestPass123"})

    resp = await client.get(f"/api/v1/resources/{eng_res.id}/worklogs")
    assert resp.status_code == 200
    assert resp.json()["total"] == 3


@pytest.mark.asyncio
async def test_resource_worklogs_engineer_other_forbidden(client: AsyncClient, db: AsyncSession):
    """Engineer cannot view another engineer's worklogs."""
    _, _, eng_res, _ = await _setup_portfolio(db, client)
    other_eng = await _seed_resource(db, "Other Eng")
    await db.commit()
    eng_user = await create_test_user(db, "ENGINEER", name="Nosy Eng")
    eng_user.resource_id = other_eng.id
    await db.commit()
    await client.post("/api/v1/auth/login", json={"email": eng_user.email, "password": "TestPass123"})

    resp = await client.get(f"/api/v1/resources/{eng_res.id}/worklogs")
    assert resp.status_code == 403


@pytest.mark.asyncio
async def test_resource_worklogs_finance_forbidden(client: AsyncClient, db: AsyncSession):
    _, _, eng_res, _ = await _setup_portfolio(db, client)
    client, _ = await login_as_role(client, db, "FINANCE")
    resp = await client.get(f"/api/v1/resources/{eng_res.id}/worklogs")
    assert resp.status_code == 403


@pytest.mark.asyncio
async def test_resource_worklogs_not_found(client: AsyncClient, db: AsyncSession):
    await login_as(client)
    resp = await client.get(f"/api/v1/resources/{uuid.uuid4()}/worklogs")
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_resource_worklogs_filter_by_project(client: AsyncClient, db: AsyncSession):
    _, _, eng_res, project = await _setup_portfolio(db, client)
    await login_as(client)
    resp = await client.get(f"/api/v1/resources/{eng_res.id}/worklogs?project_id={project.id}")
    assert resp.status_code == 200
    assert resp.json()["total"] == 3

    resp2 = await client.get(f"/api/v1/resources/{eng_res.id}/worklogs?project_id={uuid.uuid4()}")
    assert resp2.json()["total"] == 0


@pytest.mark.asyncio
async def test_resource_worklogs_includes_names(client: AsyncClient, db: AsyncSession):
    """Response includes resource and project name refs."""
    _, _, eng_res, project = await _setup_portfolio(db, client)
    await login_as(client)
    resp = await client.get(f"/api/v1/resources/{eng_res.id}/worklogs")
    entry = resp.json()["data"][0]
    assert entry["resource"]["name"] == "Engineer A"
    assert entry["project"]["name"] == "Portfolio Proj"
