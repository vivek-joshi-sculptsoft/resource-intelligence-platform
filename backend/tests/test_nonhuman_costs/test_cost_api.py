"""Tests for NonHumanCost CRUD API — VRIP-90."""

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
        "technical_expertise": "Python",
        **overrides,
    }
    resp = await client.post("/api/v1/resources", json=payload)
    assert resp.status_code == 201, resp.text
    return resp.json()["data"]


async def _create_client(client: AsyncClient, name: str = "Test Client") -> dict:
    resp = await client.post("/api/v1/clients", json={"name": name})
    assert resp.status_code == 201, resp.text
    return resp.json()["data"]


async def _create_project(client: AsyncClient, client_id: str, dm_id: str, pm_id: str, **overrides) -> dict:
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


async def _setup_project(client: AsyncClient) -> dict:
    """Create client + resources + project. Returns project dict."""
    cl = await _create_client(client)
    r1 = await _create_resource(client, name="DM Resource")
    r2 = await _create_resource(client, name="PM Resource")
    return await _create_project(client, cl["id"], r1["id"], r2["id"])


def _cost_payload(**overrides) -> dict:
    return {
        "description": "AWS EC2 instance",
        "category": "CLOUD_INFRA",
        "amount": 5000.00,
        "currency": "INR",
        "cost_date": date.today().isoformat(),
        **overrides,
    }


# ── Happy Path: Create ──


@pytest.mark.asyncio
async def test_create_cost_inr(client: AsyncClient, db: AsyncSession):
    await login_as(client)
    proj = await _setup_project(client)

    resp = await client.post(f"/api/v1/projects/{proj['id']}/costs", json=_cost_payload())
    assert resp.status_code == 201
    data = resp.json()["data"]
    assert data["description"] == "AWS EC2 instance"
    assert data["category"] == "CLOUD_INFRA"
    assert data["amount"] == 5000.0
    assert data["currency"] == "INR"
    assert data["exchange_rate"] == 1.0
    assert data["amount_inr"] == 5000.0
    assert data["is_recurring"] is False
    assert data["recurring_end_date"] is None
    assert data["created_by"] is not None
    assert data["created_by"]["name"] == "System Admin"


@pytest.mark.asyncio
async def test_create_cost_multi_currency(client: AsyncClient, db: AsyncSession):
    """See BUSINESS-RULES §7.7 — amount_inr = amount × exchange_rate."""
    await login_as(client)
    proj = await _setup_project(client)

    payload = _cost_payload(
        description="GitHub Copilot",
        category="AI_TOOLS",
        amount=19.0,
        currency="USD",
        exchange_rate=83.5,
    )
    resp = await client.post(f"/api/v1/projects/{proj['id']}/costs", json=payload)
    assert resp.status_code == 201
    data = resp.json()["data"]
    assert data["currency"] == "USD"
    assert data["exchange_rate"] == 83.5
    assert data["amount_inr"] == pytest.approx(19.0 * 83.5, rel=1e-2)


@pytest.mark.asyncio
async def test_create_cost_inr_auto_rate(client: AsyncClient, db: AsyncSession):
    """See FSD §11 — INR auto-rate: exchange_rate forced to 1.0."""
    await login_as(client)
    proj = await _setup_project(client)

    payload = _cost_payload(exchange_rate=5.0)  # should be overridden to 1.0
    resp = await client.post(f"/api/v1/projects/{proj['id']}/costs", json=payload)
    assert resp.status_code == 201
    data = resp.json()["data"]
    assert data["exchange_rate"] == 1.0
    assert data["amount_inr"] == 5000.0


@pytest.mark.asyncio
async def test_create_recurring_cost(client: AsyncClient, db: AsyncSession):
    await login_as(client)
    proj = await _setup_project(client)

    end = (date.today() + timedelta(days=90)).isoformat()
    payload = _cost_payload(is_recurring=True, recurring_end_date=end)
    resp = await client.post(f"/api/v1/projects/{proj['id']}/costs", json=payload)
    assert resp.status_code == 201
    data = resp.json()["data"]
    assert data["is_recurring"] is True
    assert data["recurring_end_date"] == end


# ── Happy Path: Read ──


@pytest.mark.asyncio
async def test_get_cost_detail(client: AsyncClient, db: AsyncSession):
    await login_as(client)
    proj = await _setup_project(client)

    create_resp = await client.post(f"/api/v1/projects/{proj['id']}/costs", json=_cost_payload())
    cost_id = create_resp.json()["data"]["id"]

    resp = await client.get(f"/api/v1/projects/{proj['id']}/costs/{cost_id}")
    assert resp.status_code == 200
    assert resp.json()["data"]["id"] == cost_id


@pytest.mark.asyncio
async def test_list_costs_paginated(client: AsyncClient, db: AsyncSession):
    await login_as(client)
    proj = await _setup_project(client)

    for i in range(5):
        await client.post(
            f"/api/v1/projects/{proj['id']}/costs",
            json=_cost_payload(description=f"Cost {i}"),
        )

    resp = await client.get(f"/api/v1/projects/{proj['id']}/costs?page=1&limit=3")
    assert resp.status_code == 200
    body = resp.json()
    assert len(body["data"]) == 3
    assert body["total"] == 5
    assert body["page"] == 1
    assert body["limit"] == 3


@pytest.mark.asyncio
async def test_list_costs_filter_category(client: AsyncClient, db: AsyncSession):
    await login_as(client)
    proj = await _setup_project(client)

    await client.post(f"/api/v1/projects/{proj['id']}/costs", json=_cost_payload(category="AI_TOOLS"))
    await client.post(f"/api/v1/projects/{proj['id']}/costs", json=_cost_payload(category="CLOUD_INFRA"))
    await client.post(f"/api/v1/projects/{proj['id']}/costs", json=_cost_payload(category="AI_TOOLS"))

    resp = await client.get(f"/api/v1/projects/{proj['id']}/costs?category=AI_TOOLS")
    assert resp.status_code == 200
    assert len(resp.json()["data"]) == 2


@pytest.mark.asyncio
async def test_list_costs_filter_recurring(client: AsyncClient, db: AsyncSession):
    await login_as(client)
    proj = await _setup_project(client)

    end = (date.today() + timedelta(days=30)).isoformat()
    await client.post(f"/api/v1/projects/{proj['id']}/costs", json=_cost_payload(is_recurring=True, recurring_end_date=end))
    await client.post(f"/api/v1/projects/{proj['id']}/costs", json=_cost_payload(is_recurring=False))

    resp = await client.get(f"/api/v1/projects/{proj['id']}/costs?is_recurring=true")
    assert resp.status_code == 200
    assert len(resp.json()["data"]) == 1
    assert resp.json()["data"][0]["is_recurring"] is True


@pytest.mark.asyncio
async def test_list_costs_filter_date_range(client: AsyncClient, db: AsyncSession):
    await login_as(client)
    proj = await _setup_project(client)

    today = date.today()
    await client.post(f"/api/v1/projects/{proj['id']}/costs", json=_cost_payload(cost_date=today.isoformat()))
    await client.post(
        f"/api/v1/projects/{proj['id']}/costs",
        json=_cost_payload(cost_date=(today - timedelta(days=30)).isoformat()),
    )

    resp = await client.get(
        f"/api/v1/projects/{proj['id']}/costs"
        f"?date_from={(today - timedelta(days=5)).isoformat()}"
        f"&date_to={today.isoformat()}"
    )
    assert resp.status_code == 200
    assert len(resp.json()["data"]) == 1


# ── Happy Path: Update ──


@pytest.mark.asyncio
async def test_update_cost(client: AsyncClient, db: AsyncSession):
    await login_as(client)
    proj = await _setup_project(client)

    create_resp = await client.post(f"/api/v1/projects/{proj['id']}/costs", json=_cost_payload())
    cost_id = create_resp.json()["data"]["id"]

    resp = await client.put(
        f"/api/v1/projects/{proj['id']}/costs/{cost_id}",
        json={"description": "Updated desc", "amount": 8000.0},
    )
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert data["description"] == "Updated desc"
    assert data["amount"] == 8000.0
    assert data["amount_inr"] == 8000.0  # recomputed


@pytest.mark.asyncio
async def test_update_cost_currency_recomputes_inr(client: AsyncClient, db: AsyncSession):
    """See BUSINESS-RULES §7.7 — amount_inr recomputed on save."""
    await login_as(client)
    proj = await _setup_project(client)

    create_resp = await client.post(
        f"/api/v1/projects/{proj['id']}/costs",
        json=_cost_payload(amount=100, currency="USD", exchange_rate=80.0),
    )
    cost_id = create_resp.json()["data"]["id"]
    assert create_resp.json()["data"]["amount_inr"] == pytest.approx(8000.0, rel=1e-2)

    resp = await client.put(
        f"/api/v1/projects/{proj['id']}/costs/{cost_id}",
        json={"exchange_rate": 85.0},
    )
    assert resp.status_code == 200
    assert resp.json()["data"]["amount_inr"] == pytest.approx(8500.0, rel=1e-2)


# ── Happy Path: Delete ──


@pytest.mark.asyncio
async def test_delete_cost_soft(client: AsyncClient, db: AsyncSession):
    await login_as(client)
    proj = await _setup_project(client)

    create_resp = await client.post(f"/api/v1/projects/{proj['id']}/costs", json=_cost_payload())
    cost_id = create_resp.json()["data"]["id"]

    resp = await client.delete(f"/api/v1/projects/{proj['id']}/costs/{cost_id}")
    assert resp.status_code == 200
    assert resp.json()["success"] is True

    # Should be gone from list
    list_resp = await client.get(f"/api/v1/projects/{proj['id']}/costs")
    ids = [c["id"] for c in list_resp.json()["data"]]
    assert cost_id not in ids

    # Should 404 on direct get
    get_resp = await client.get(f"/api/v1/projects/{proj['id']}/costs/{cost_id}")
    assert get_resp.status_code == 404


# ── Summary ──


@pytest.mark.asyncio
async def test_cost_summary(client: AsyncClient, db: AsyncSession):
    await login_as(client)
    proj = await _setup_project(client)

    end = (date.today() + timedelta(days=60)).isoformat()
    await client.post(f"/api/v1/projects/{proj['id']}/costs", json=_cost_payload(
        category="AI_TOOLS", amount=1000.0, is_recurring=True, recurring_end_date=end,
    ))
    await client.post(f"/api/v1/projects/{proj['id']}/costs", json=_cost_payload(
        category="AI_TOOLS", amount=500.0, is_recurring=False,
    ))
    await client.post(f"/api/v1/projects/{proj['id']}/costs", json=_cost_payload(
        category="CLOUD_INFRA", amount=2000.0, is_recurring=False,
    ))

    resp = await client.get(f"/api/v1/projects/{proj['id']}/costs/summary")
    assert resp.status_code == 200
    body = resp.json()
    assert body["total_inr"] == pytest.approx(3500.0, rel=1e-2)
    assert body["by_category"]["AI_TOOLS"] == pytest.approx(1500.0, rel=1e-2)
    assert body["by_category"]["CLOUD_INFRA"] == pytest.approx(2000.0, rel=1e-2)
    assert body["one_time_inr"] == pytest.approx(2500.0, rel=1e-2)
    assert body["recurring_monthly_inr"] == pytest.approx(1000.0, rel=1e-2)


@pytest.mark.asyncio
async def test_cost_summary_empty(client: AsyncClient, db: AsyncSession):
    await login_as(client)
    proj = await _setup_project(client)

    resp = await client.get(f"/api/v1/projects/{proj['id']}/costs/summary")
    assert resp.status_code == 200
    body = resp.json()
    assert body["total_inr"] == 0.0
    assert body["by_category"] == {}
    assert body["one_time_inr"] == 0.0
    assert body["recurring_monthly_inr"] == 0.0


# ── Validation Errors ──


@pytest.mark.asyncio
async def test_create_cost_amount_zero(client: AsyncClient, db: AsyncSession):
    await login_as(client)
    proj = await _setup_project(client)

    resp = await client.post(
        f"/api/v1/projects/{proj['id']}/costs",
        json=_cost_payload(amount=0),
    )
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_create_cost_negative_amount(client: AsyncClient, db: AsyncSession):
    await login_as(client)
    proj = await _setup_project(client)

    resp = await client.post(
        f"/api/v1/projects/{proj['id']}/costs",
        json=_cost_payload(amount=-100),
    )
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_create_cost_negative_exchange_rate(client: AsyncClient, db: AsyncSession):
    await login_as(client)
    proj = await _setup_project(client)

    resp = await client.post(
        f"/api/v1/projects/{proj['id']}/costs",
        json=_cost_payload(currency="USD", exchange_rate=-1.0),
    )
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_create_recurring_without_end_date(client: AsyncClient, db: AsyncSession):
    """See FSD §11 — recurring costs must have an end date."""
    await login_as(client)
    proj = await _setup_project(client)

    resp = await client.post(
        f"/api/v1/projects/{proj['id']}/costs",
        json=_cost_payload(is_recurring=True),
    )
    assert resp.status_code == 422
    assert "end date" in resp.json()["message"].lower()


@pytest.mark.asyncio
async def test_create_recurring_end_before_start(client: AsyncClient, db: AsyncSession):
    """See FSD §11 — recurring end date must be after cost date."""
    await login_as(client)
    proj = await _setup_project(client)

    resp = await client.post(
        f"/api/v1/projects/{proj['id']}/costs",
        json=_cost_payload(
            is_recurring=True,
            recurring_end_date=(date.today() - timedelta(days=1)).isoformat(),
        ),
    )
    assert resp.status_code == 422
    assert "after cost date" in resp.json()["message"].lower()


@pytest.mark.asyncio
async def test_create_cost_invalid_category(client: AsyncClient, db: AsyncSession):
    await login_as(client)
    proj = await _setup_project(client)

    resp = await client.post(
        f"/api/v1/projects/{proj['id']}/costs",
        json=_cost_payload(category="INVALID"),
    )
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_create_cost_missing_description(client: AsyncClient, db: AsyncSession):
    await login_as(client)
    proj = await _setup_project(client)

    payload = _cost_payload()
    del payload["description"]
    resp = await client.post(f"/api/v1/projects/{proj['id']}/costs", json=payload)
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_create_cost_nonexistent_project(client: AsyncClient, db: AsyncSession):
    await login_as(client)
    fake_id = str(uuid.uuid4())

    resp = await client.post(f"/api/v1/projects/{fake_id}/costs", json=_cost_payload())
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_get_cost_not_found(client: AsyncClient, db: AsyncSession):
    await login_as(client)
    proj = await _setup_project(client)
    fake_id = str(uuid.uuid4())

    resp = await client.get(f"/api/v1/projects/{proj['id']}/costs/{fake_id}")
    assert resp.status_code == 404


# ── Access Control ──


@pytest.mark.asyncio
async def test_ceo_can_crud_costs(client: AsyncClient, db: AsyncSession):
    await login_as(client)  # admin = CEO
    proj = await _setup_project(client)

    resp = await client.post(f"/api/v1/projects/{proj['id']}/costs", json=_cost_payload())
    assert resp.status_code == 201


@pytest.mark.asyncio
async def test_finance_can_crud_costs(client: AsyncClient, db: AsyncSession):
    await login_as(client)
    proj = await _setup_project(client)

    client_fin, user_fin = await login_as_role(client, db, "FINANCE")

    resp = await client_fin.post(f"/api/v1/projects/{proj['id']}/costs", json=_cost_payload())
    assert resp.status_code == 201


@pytest.mark.asyncio
async def test_hr_cannot_access_costs(client: AsyncClient, db: AsyncSession):
    """See ACCESS-MATRIX — HR: non_human_costs = NONE."""
    await login_as(client)
    proj = await _setup_project(client)

    client_hr, _ = await login_as_role(client, db, "HR")

    resp = await client_hr.get(f"/api/v1/projects/{proj['id']}/costs")
    assert resp.status_code == 403

    resp = await client_hr.post(f"/api/v1/projects/{proj['id']}/costs", json=_cost_payload())
    assert resp.status_code == 403


@pytest.mark.asyncio
async def test_engineer_cannot_access_costs(client: AsyncClient, db: AsyncSession):
    """See ACCESS-MATRIX — ENGINEER: non_human_costs = NONE."""
    await login_as(client)
    proj = await _setup_project(client)

    client_eng, _ = await login_as_role(client, db, "ENGINEER")

    resp = await client_eng.get(f"/api/v1/projects/{proj['id']}/costs")
    assert resp.status_code == 403


@pytest.mark.asyncio
async def test_pm_own_portfolio_can_create(client: AsyncClient, db: AsyncSession):
    """See ACCESS-MATRIX — PM: non_human_costs = EDIT OWN_PORTFOLIO."""
    await login_as(client)
    cl = await _create_client(client)
    dm_res = await _create_resource(client, name="DM Res")

    # Create PM user with linked resource
    pm_res = await _create_resource(client, name="PM Res")
    pm_user = await create_test_user(db, "PM", email="pm-cost-test@test.com", name="PM Test")
    # Link PM user to resource
    from sqlalchemy import update
    from app.modules.auth.models import User as UserModel
    async with db.begin():
        await db.execute(
            update(UserModel).where(UserModel.id == pm_user.id).values(resource_id=uuid.UUID(pm_res["id"]))
        )

    proj = await _create_project(client, cl["id"], dm_res["id"], pm_res["id"])

    # Login as PM
    pm_client, _ = await login_as_role(client, db, "PM")
    # Need to create a new PM with the right resource_id
    # Actually, let me re-login as the PM user we created
    resp = await client.post("/api/v1/auth/login", json={"email": "pm-cost-test@test.com", "password": "TestPass123"})
    assert resp.status_code == 200

    resp = await client.post(f"/api/v1/projects/{proj['id']}/costs", json=_cost_payload())
    assert resp.status_code == 201


@pytest.mark.asyncio
async def test_pm_other_portfolio_forbidden(client: AsyncClient, db: AsyncSession):
    """PM cannot create costs on projects they don't own."""
    await login_as(client)
    cl = await _create_client(client)
    dm_res = await _create_resource(client, name="DM Res 2")
    other_pm_res = await _create_resource(client, name="Other PM Res")
    proj = await _create_project(client, cl["id"], dm_res["id"], other_pm_res["id"])

    # Login as a different PM (no resource linkage to this project)
    client_pm, _ = await login_as_role(client, db, "PM")

    resp = await client_pm.post(f"/api/v1/projects/{proj['id']}/costs", json=_cost_payload())
    assert resp.status_code == 403


@pytest.mark.asyncio
async def test_dm_own_portfolio_can_create(client: AsyncClient, db: AsyncSession):
    """See ACCESS-MATRIX — DM: non_human_costs = EDIT OWN_PORTFOLIO."""
    await login_as(client)
    cl = await _create_client(client)
    dm_res = await _create_resource(client, name="DM Res for Cost")
    pm_res = await _create_resource(client, name="PM Res for Cost")

    dm_user = await create_test_user(db, "DM", email="dm-cost-test@test.com", name="DM Test")
    from sqlalchemy import update
    from app.modules.auth.models import User as UserModel
    async with db.begin():
        await db.execute(
            update(UserModel).where(UserModel.id == dm_user.id).values(resource_id=uuid.UUID(dm_res["id"]))
        )

    proj = await _create_project(client, cl["id"], dm_res["id"], pm_res["id"])

    resp = await client.post("/api/v1/auth/login", json={"email": "dm-cost-test@test.com", "password": "TestPass123"})
    assert resp.status_code == 200

    resp = await client.post(f"/api/v1/projects/{proj['id']}/costs", json=_cost_payload())
    assert resp.status_code == 201


# ── Audit Logging ──


@pytest.mark.asyncio
async def test_audit_log_on_create(client: AsyncClient, db: AsyncSession):
    await login_as(client)
    proj = await _setup_project(client)

    resp = await client.post(f"/api/v1/projects/{proj['id']}/costs", json=_cost_payload())
    assert resp.status_code == 201
    cost_id = resp.json()["data"]["id"]

    from sqlalchemy import select
    from app.modules.audit.models import AuditLog, AuditAction
    result = await db.execute(
        select(AuditLog).where(
            AuditLog.entity_type == "NonHumanCost",
            AuditLog.entity_id == uuid.UUID(cost_id),
            AuditLog.action == AuditAction.CREATE,
        )
    )
    logs = result.scalars().all()
    assert len(logs) == 1


@pytest.mark.asyncio
async def test_audit_log_on_update(client: AsyncClient, db: AsyncSession):
    await login_as(client)
    proj = await _setup_project(client)

    resp = await client.post(f"/api/v1/projects/{proj['id']}/costs", json=_cost_payload())
    cost_id = resp.json()["data"]["id"]

    await client.put(
        f"/api/v1/projects/{proj['id']}/costs/{cost_id}",
        json={"amount": 9999.0},
    )

    from sqlalchemy import select
    from app.modules.audit.models import AuditLog, AuditAction
    result = await db.execute(
        select(AuditLog).where(
            AuditLog.entity_type == "NonHumanCost",
            AuditLog.entity_id == uuid.UUID(cost_id),
            AuditLog.action == AuditAction.UPDATE,
        )
    )
    logs = result.scalars().all()
    assert len(logs) >= 1
    field_names = [l.field_name for l in logs]
    assert "amount" in field_names


@pytest.mark.asyncio
async def test_audit_log_on_delete(client: AsyncClient, db: AsyncSession):
    await login_as(client)
    proj = await _setup_project(client)

    resp = await client.post(f"/api/v1/projects/{proj['id']}/costs", json=_cost_payload())
    cost_id = resp.json()["data"]["id"]

    await client.delete(f"/api/v1/projects/{proj['id']}/costs/{cost_id}")

    from sqlalchemy import select
    from app.modules.audit.models import AuditLog, AuditAction
    result = await db.execute(
        select(AuditLog).where(
            AuditLog.entity_type == "NonHumanCost",
            AuditLog.entity_id == uuid.UUID(cost_id),
            AuditLog.action == AuditAction.DELETE,
        )
    )
    logs = result.scalars().all()
    assert len(logs) == 1


# ── All Five Categories ──


@pytest.mark.asyncio
async def test_all_categories_accepted(client: AsyncClient, db: AsyncSession):
    await login_as(client)
    proj = await _setup_project(client)

    for cat in ["AI_TOOLS", "CLOUD_INFRA", "DEVICES", "THIRD_PARTY_LICENSE", "OTHER"]:
        resp = await client.post(
            f"/api/v1/projects/{proj['id']}/costs",
            json=_cost_payload(category=cat, description=f"Test {cat}"),
        )
        assert resp.status_code == 201, f"Failed for category {cat}: {resp.text}"
        assert resp.json()["data"]["category"] == cat


# ── Edge Cases ──


@pytest.mark.asyncio
async def test_list_empty(client: AsyncClient, db: AsyncSession):
    await login_as(client)
    proj = await _setup_project(client)

    resp = await client.get(f"/api/v1/projects/{proj['id']}/costs")
    assert resp.status_code == 200
    assert resp.json()["data"] == []
    assert resp.json()["total"] == 0


@pytest.mark.asyncio
async def test_update_nonexistent_cost(client: AsyncClient, db: AsyncSession):
    await login_as(client)
    proj = await _setup_project(client)

    resp = await client.put(
        f"/api/v1/projects/{proj['id']}/costs/{uuid.uuid4()}",
        json={"amount": 100},
    )
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_delete_nonexistent_cost(client: AsyncClient, db: AsyncSession):
    await login_as(client)
    proj = await _setup_project(client)

    resp = await client.delete(f"/api/v1/projects/{proj['id']}/costs/{uuid.uuid4()}")
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_deleted_cost_excluded_from_summary(client: AsyncClient, db: AsyncSession):
    await login_as(client)
    proj = await _setup_project(client)

    resp1 = await client.post(f"/api/v1/projects/{proj['id']}/costs", json=_cost_payload(amount=1000))
    resp2 = await client.post(f"/api/v1/projects/{proj['id']}/costs", json=_cost_payload(amount=2000))
    cost1_id = resp1.json()["data"]["id"]

    await client.delete(f"/api/v1/projects/{proj['id']}/costs/{cost1_id}")

    summary = await client.get(f"/api/v1/projects/{proj['id']}/costs/summary")
    assert summary.json()["total_inr"] == pytest.approx(2000.0, rel=1e-2)


@pytest.mark.asyncio
async def test_update_to_recurring_requires_end_date(client: AsyncClient, db: AsyncSession):
    """Updating is_recurring=true without providing recurring_end_date should fail."""
    await login_as(client)
    proj = await _setup_project(client)

    resp = await client.post(f"/api/v1/projects/{proj['id']}/costs", json=_cost_payload())
    cost_id = resp.json()["data"]["id"]

    resp = await client.put(
        f"/api/v1/projects/{proj['id']}/costs/{cost_id}",
        json={"is_recurring": True},
    )
    assert resp.status_code == 422
    assert "end date" in resp.json()["message"].lower()
