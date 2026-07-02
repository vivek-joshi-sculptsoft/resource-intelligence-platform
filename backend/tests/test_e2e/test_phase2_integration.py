"""Phase 2 integration testing and hardening — VRIP-109.

Cross-module flows through the full financial pipeline:
project → assignments (billing rates) → non-human costs → invoices →
project financials → client/dashboard aggregation.

All expected values follow shared/BUSINESS-RULES.md §7 exactly.
"""

import uuid
from datetime import date, timedelta

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from tests.conftest import create_test_user, login_as, login_as_role


def _f(value):
    """Decimal fields serialize as strings in JSON."""
    return None if value is None else float(value)


# ── Shared builders (API-level, same conventions as test_financial/) ──


async def _create_resource(client: AsyncClient, name: str = "Dev", **overrides) -> dict:
    payload = {
        "employee_id": f"EMP-{uuid.uuid4().hex[:6]}",
        "name": name,
        "designation": "Senior Developer",
        **overrides,
    }
    resp = await client.post("/api/v1/resources", json=payload)
    assert resp.status_code == 201, resp.text
    return resp.json()["data"]


async def _create_client_entity(client: AsyncClient, name: str | None = None) -> dict:
    resp = await client.post(
        "/api/v1/clients", json={"name": name or f"Client-{uuid.uuid4().hex[:6]}"}
    )
    assert resp.status_code == 201, resp.text
    return resp.json()["data"]


async def _create_project(
    client: AsyncClient, client_id: str, dm_id: str, pm_id: str, **overrides
) -> dict:
    payload = {
        "name": f"Project-{uuid.uuid4().hex[:6]}",
        "client_id": client_id,
        "type": "TIME_AND_MATERIAL",
        "dm_id": dm_id,
        "pm_id": pm_id,
        "contract_end_date": (date.today() + timedelta(days=365)).isoformat(),
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


async def _transition_invoice(
    client: AsyncClient, project_id: str, invoice_id: str, status: str
) -> dict:
    resp = await client.put(
        f"/api/v1/projects/{project_id}/invoices/{invoice_id}/status",
        json={"status": status},
    )
    assert resp.status_code == 200, resp.text
    return resp.json()["data"]


async def _transition_milestone(
    client: AsyncClient, project_id: str, milestone_id: str, status: str
) -> dict:
    resp = await client.put(
        f"/api/v1/projects/{project_id}/milestones/{milestone_id}/status",
        json={"status": status},
    )
    assert resp.status_code == 200, resp.text
    return resp.json()["data"]


async def _get_milestone(client: AsyncClient, project_id: str, milestone_id: str) -> dict:
    resp = await client.get(f"/api/v1/projects/{project_id}/milestones/{milestone_id}")
    assert resp.status_code == 200, resp.text
    return resp.json()["data"]


async def _login_linked_user(
    client: AsyncClient, db: AsyncSession, role_code: str, resource_id: str
) -> None:
    """Create a user of the given role linked to a resource, then log in as them."""
    user = await create_test_user(
        db, role_code, email=f"{role_code.lower()}-{uuid.uuid4().hex[:6]}@test.com"
    )
    user.resource_id = uuid.UUID(resource_id)
    await db.commit()
    resp = await client.post(
        "/api/v1/auth/login", json={"email": user.email, "password": "TestPass123"}
    )
    assert resp.status_code == 200


# ── AC 1: Cross-module flow ──────────────────────────────────────────────


@pytest.mark.asyncio
async def test_full_financial_pipeline_cross_module(client: AsyncClient, db: AsyncSession):
    """create project → assignments with billing rates → non-human costs →
    invoices → project financials → client + dashboard aggregation.

    Numbers (BUSINESS-RULES §7.2/§7.3/§7.4/§7.5):
      Billable dev: loaded_cost=30000, alloc=50% -> cost 15000
                    billability=50%, rate=500 -> revenue = 0.5*22*8*500 = 44000
      Shadow dev:   loaded_cost=10000, alloc=100% -> cost 10000, no revenue
      Non-human:    3000 + 2000 = 5000
      total_cost = 30000; projected_revenue = 44000; projected_margin = 14000
      APPROVED invoice 40000 -> actual_revenue = 40000; actual_margin = 10000
    """
    await login_as(client)
    cl = await _create_client_entity(client)
    dm = await _create_resource(client, "DM Person")
    pm = await _create_resource(client, "PM Person")
    proj = await _create_project(client, cl["id"], dm["id"], pm["id"])

    dev = await _create_resource(client, "Billable Dev", loaded_cost_monthly=30000)
    shadow = await _create_resource(client, "Shadow Dev", loaded_cost_monthly=10000)
    await _create_assignment(
        client, proj["id"], dev["id"], allocation_pct=50, billability_pct=50, billing_rate=500
    )
    await _create_assignment(
        client, proj["id"], shadow["id"], is_shadow=True, billability_pct=0
    )
    await _create_cost(client, proj["id"], amount=3000.00, description="AWS")
    await _create_cost(client, proj["id"], amount=2000.00, description="License")

    client, _ = await login_as_role(client, db, "FINANCE")
    inv = await _create_invoice(client, proj["id"], amount=40000.00)
    await _transition_invoice(client, proj["id"], inv["id"], "SUBMITTED")
    await _transition_invoice(client, proj["id"], inv["id"], "APPROVED")

    # Project-level financials
    await login_as(client)
    resp = await client.get(f"/api/v1/projects/{proj['id']}/financials")
    assert resp.status_code == 200, resp.text
    data = resp.json()["data"]
    assert _f(data["resource_cost_inr"]) == 25000.0  # 15000 + 10000 (shadow costs count)
    assert _f(data["non_human_cost_inr"]) == 5000.0
    assert _f(data["total_cost_inr"]) == 30000.0
    assert _f(data["projected_revenue_inr"]) == 44000.0  # shadow excluded from revenue
    assert _f(data["actual_revenue_inr"]) == 40000.0
    assert _f(data["projected_margin_inr"]) == 14000.0
    assert _f(data["actual_margin_inr"]) == 10000.0
    assert data["missing_costs"] == []
    assert data["missing_rates"] == []

    # Client-level aggregation matches the single project
    resp = await client.get(f"/api/v1/clients/{cl['id']}/financials")
    assert resp.status_code == 200, resp.text
    cdata = resp.json()["data"]
    assert _f(cdata["total_cost_inr"]) == 30000.0
    assert _f(cdata["total_projected_revenue_inr"]) == 44000.0
    assert _f(cdata["total_actual_revenue_inr"]) == 40000.0
    assert len(cdata["per_project"]) == 1

    # Company dashboard aggregation
    resp = await client.get("/api/v1/dashboard/financials")
    assert resp.status_code == 200, resp.text
    ddata = resp.json()["data"]
    assert _f(ddata["total_cost_inr"]) == 30000.0
    assert _f(ddata["total_projected_revenue_inr"]) == 44000.0
    assert _f(ddata["total_actual_revenue_inr"]) == 40000.0


# ── AC 2: Multi-currency flow ────────────────────────────────────────────


@pytest.mark.asyncio
async def test_multi_currency_usd_chain(client: AsyncClient, db: AsyncSession):
    """USD project with manual exchange rate — INR conversion through the whole
    chain: invoice.amount_inr, financials exchange_rate_used, projected revenue,
    client and dashboard aggregates (BUSINESS-RULES §7.7)."""
    await login_as(client)
    cl = await _create_client_entity(client)
    dm = await _create_resource(client, "DM Person")
    pm = await _create_resource(client, "PM Person")
    proj = await _create_project(client, cl["id"], dm["id"], pm["id"], billing_currency="USD")

    dev = await _create_resource(client, "USD Dev", loaded_cost_monthly=100000)
    await _create_assignment(client, proj["id"], dev["id"], billing_rate=100)
    # projected revenue (USD) = 100% * 22 * 8 * 100 = 17600

    client, _ = await login_as_role(client, db, "FINANCE")
    inv = await _create_invoice(
        client, proj["id"], amount=2000, currency="USD", exchange_rate=83.0
    )
    assert _f(inv["amount_inr"]) == 2000 * 83.0  # §7.7 amount_inr = amount × rate
    await _transition_invoice(client, proj["id"], inv["id"], "SUBMITTED")
    await _transition_invoice(client, proj["id"], inv["id"], "APPROVED")

    await login_as(client)
    resp = await client.get(f"/api/v1/projects/{proj['id']}/financials")
    assert resp.status_code == 200, resp.text
    data = resp.json()["data"]
    assert _f(data["exchange_rate_used"]) == 83.0
    assert _f(data["projected_revenue_inr"]) == 17600 * 83.0
    assert _f(data["actual_revenue_inr"]) == 166000.0

    resp = await client.get(f"/api/v1/clients/{cl['id']}/financials")
    assert _f(resp.json()["data"]["total_actual_revenue_inr"]) == 166000.0
    assert _f(resp.json()["data"]["total_projected_revenue_inr"]) == 17600 * 83.0

    resp = await client.get("/api/v1/dashboard/financials")
    assert _f(resp.json()["data"]["total_actual_revenue_inr"]) == 166000.0


# ── AC 4: Milestone lifecycle ────────────────────────────────────────────


@pytest.mark.asyncio
async def test_milestone_full_lifecycle(client: AsyncClient, db: AsyncSession):
    """PLANNED → DELIVERED → APPROVED → INVOICED → PAID.
    APPROVED gates invoice creation; INVOICED/PAID arrive via invoice cascade
    (FSD §6.2/§6.3)."""
    await login_as(client)
    cl = await _create_client_entity(client)
    dm = await _create_resource(client, "DM Person")
    pm = await _create_resource(client, "PM Person")
    proj = await _create_project(client, cl["id"], dm["id"], pm["id"], type="FIXED_PRICE")

    resp = await client.post(
        f"/api/v1/projects/{proj['id']}/milestones",
        json={"name": "Phase 1 delivery", "amount": 50000.0},
    )
    assert resp.status_code == 201, resp.text
    ms = resp.json()["data"]
    assert ms["status"] == "PLANNED"

    # Skipping a step (PLANNED → APPROVED) is rejected
    resp = await client.put(
        f"/api/v1/projects/{proj['id']}/milestones/{ms['id']}/status",
        json={"status": "APPROVED"},
    )
    assert resp.status_code == 422

    # Invoice against a non-APPROVED milestone is rejected
    fin_client, _ = await login_as_role(client, db, "FINANCE")
    resp = await fin_client.post(
        f"/api/v1/projects/{proj['id']}/invoices",
        json={
            "invoice_date": date.today().isoformat(),
            "amount": 50000.0,
            "currency": "INR",
            "exchange_rate": 1.0,
            "milestone_id": ms["id"],
        },
    )
    assert resp.status_code in (400, 422), resp.text

    await login_as(client)
    assert (await _transition_milestone(client, proj["id"], ms["id"], "DELIVERED"))[
        "status"
    ] == "DELIVERED"
    assert (await _transition_milestone(client, proj["id"], ms["id"], "APPROVED"))[
        "status"
    ] == "APPROVED"

    # APPROVED milestone → invoice can be created (FINANCE only)
    client, _ = await login_as_role(client, db, "FINANCE")
    inv = await _create_invoice(client, proj["id"], amount=50000.0, milestone_id=ms["id"])

    # Invoice SUBMITTED cascades milestone → INVOICED
    await _transition_invoice(client, proj["id"], inv["id"], "SUBMITTED")
    assert (await _get_milestone(client, proj["id"], ms["id"]))["status"] == "INVOICED"

    # Invoice APPROVED (no milestone change), then PAID cascades milestone → PAID
    await _transition_invoice(client, proj["id"], inv["id"], "APPROVED")
    assert (await _get_milestone(client, proj["id"], ms["id"]))["status"] == "INVOICED"
    await _transition_invoice(client, proj["id"], inv["id"], "PAID")
    assert (await _get_milestone(client, proj["id"], ms["id"]))["status"] == "PAID"


# ── AC 5: Invoice lifecycle → actual revenue ─────────────────────────────


@pytest.mark.asyncio
async def test_invoice_lifecycle_updates_actual_revenue(client: AsyncClient, db: AsyncSession):
    """DRAFT → SUBMITTED → APPROVED → PAID. Actual revenue counts only
    APPROVED/PAID invoices (BUSINESS-RULES §7.4)."""
    await login_as(client)
    cl = await _create_client_entity(client)
    dm = await _create_resource(client, "DM Person")
    pm = await _create_resource(client, "PM Person")
    proj = await _create_project(client, cl["id"], dm["id"], pm["id"])

    async def actual_revenue() -> float:
        await login_as(client)
        resp = await client.get(f"/api/v1/projects/{proj['id']}/financials")
        assert resp.status_code == 200, resp.text
        return _f(resp.json()["data"]["actual_revenue_inr"])

    fin_client, _ = await login_as_role(client, db, "FINANCE")
    inv = await _create_invoice(fin_client, proj["id"], amount=60000.0)
    assert inv["status"] == "DRAFT"
    assert await actual_revenue() == 0.0

    fin_client, _ = await login_as_role(client, db, "FINANCE")
    await _transition_invoice(fin_client, proj["id"], inv["id"], "SUBMITTED")
    assert await actual_revenue() == 0.0

    fin_client, _ = await login_as_role(client, db, "FINANCE")
    await _transition_invoice(fin_client, proj["id"], inv["id"], "APPROVED")
    assert await actual_revenue() == 60000.0

    fin_client, _ = await login_as_role(client, db, "FINANCE")
    await _transition_invoice(fin_client, proj["id"], inv["id"], "PAID")
    assert await actual_revenue() == 60000.0

    # Backward transition is rejected (forward-only, FSD §6.3)
    fin_client, _ = await login_as_role(client, db, "FINANCE")
    resp = await fin_client.put(
        f"/api/v1/projects/{proj['id']}/invoices/{inv['id']}/status",
        json={"status": "DRAFT"},
    )
    assert resp.status_code == 422


# ── AC 6: Recurring cost job through the API chain ───────────────────────


@pytest.mark.asyncio
async def test_recurring_cost_job_api_chain(client: AsyncClient, db: AsyncSession):
    """Create recurring cost via API → trigger job → snapshot visible via API
    and included in project financials."""
    from app.modules.nonhuman_costs.jobs import run_process_recurring_costs

    await login_as(client)
    cl = await _create_client_entity(client)
    dm = await _create_resource(client, "DM Person")
    pm = await _create_resource(client, "PM Person")
    proj = await _create_project(client, cl["id"], dm["id"], pm["id"])

    await _create_cost(
        client,
        proj["id"],
        description="AWS recurring",
        amount=5000.00,
        cost_date=(date.today() - timedelta(days=45)).isoformat(),
        is_recurring=True,
        recurring_end_date=(date.today() + timedelta(days=180)).isoformat(),
    )

    result = await run_process_recurring_costs(db)
    await db.commit()
    assert result["created"] == 1

    resp = await client.get(f"/api/v1/projects/{proj['id']}/costs")
    assert resp.status_code == 200, resp.text
    costs = resp.json()["data"]
    snapshots = [
        c for c in costs if c["description"] == "AWS recurring" and not c["is_recurring"]
    ]
    assert len(snapshots) == 1
    assert snapshots[0]["cost_date"] == date.today().replace(day=1).isoformat()

    # Snapshot + recurring template both count as this month's non-human cost
    resp = await client.get(f"/api/v1/projects/{proj['id']}/financials")
    assert resp.status_code == 200, resp.text
    assert _f(resp.json()["data"]["non_human_cost_inr"]) >= 5000.0


# ── AC 7: Edge cases ─────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_edge_project_with_no_assignments_but_costs(client: AsyncClient, db: AsyncSession):
    """No assignments: resource cost 0, revenue 0, margin goes negative on costs."""
    await login_as(client)
    cl = await _create_client_entity(client)
    dm = await _create_resource(client, "DM Person")
    pm = await _create_resource(client, "PM Person")
    proj = await _create_project(client, cl["id"], dm["id"], pm["id"])
    await _create_cost(client, proj["id"], amount=7000.00)

    resp = await client.get(f"/api/v1/projects/{proj['id']}/financials")
    assert resp.status_code == 200, resp.text
    data = resp.json()["data"]
    assert _f(data["resource_cost_inr"]) == 0.0
    assert _f(data["non_human_cost_inr"]) == 7000.0
    assert _f(data["total_cost_inr"]) == 7000.0
    assert _f(data["projected_revenue_inr"]) == 0.0
    assert _f(data["actual_revenue_inr"]) == 0.0
    assert _f(data["projected_margin_inr"]) == -7000.0


@pytest.mark.asyncio
async def test_edge_zero_billing_rate_revenue_zero_not_missing(
    client: AsyncClient, db: AsyncSession
):
    """billing_rate=0 is a real rate (revenue 0) — not a missing rate."""
    await login_as(client)
    cl = await _create_client_entity(client)
    dm = await _create_resource(client, "DM Person")
    pm = await _create_resource(client, "PM Person")
    proj = await _create_project(client, cl["id"], dm["id"], pm["id"])

    dev = await _create_resource(client, "Free Dev", loaded_cost_monthly=10000)
    await _create_assignment(client, proj["id"], dev["id"], billing_rate=0)

    resp = await client.get(f"/api/v1/projects/{proj['id']}/financials")
    assert resp.status_code == 200, resp.text
    data = resp.json()["data"]
    assert _f(data["projected_revenue_inr"]) == 0.0
    assert data["missing_rates"] == []
    assert _f(data["resource_cost_inr"]) == 10000.0


@pytest.mark.asyncio
async def test_edge_null_loaded_cost_flags_missing_cost(client: AsyncClient, db: AsyncSession):
    """Null loaded_cost nulls the cost totals and reports the resource by name."""
    await login_as(client)
    cl = await _create_client_entity(client)
    dm = await _create_resource(client, "DM Person")
    pm = await _create_resource(client, "PM Person")
    proj = await _create_project(client, cl["id"], dm["id"], pm["id"])

    dev = await _create_resource(client, "No CTC Dev")  # loaded_cost_monthly=None
    await _create_assignment(client, proj["id"], dev["id"], billing_rate=500)

    resp = await client.get(f"/api/v1/projects/{proj['id']}/financials")
    assert resp.status_code == 200, resp.text
    data = resp.json()["data"]
    assert data["resource_cost_inr"] is None
    assert data["total_cost_inr"] is None
    assert data["projected_margin_inr"] is None  # margin needs cost
    assert "No CTC Dev" in data["missing_costs"]
    assert _f(data["projected_revenue_inr"]) == 88000.0  # revenue side unaffected


@pytest.mark.asyncio
async def test_edge_no_invoices_actual_revenue_zero_everywhere(
    client: AsyncClient, db: AsyncSession
):
    """No invoices: actual revenue is 0.0 (not null) at project, client, company level."""
    await login_as(client)
    cl = await _create_client_entity(client)
    dm = await _create_resource(client, "DM Person")
    pm = await _create_resource(client, "PM Person")
    proj = await _create_project(client, cl["id"], dm["id"], pm["id"])

    dev = await _create_resource(client, "Dev", loaded_cost_monthly=20000)
    await _create_assignment(client, proj["id"], dev["id"], billing_rate=500)

    for url in (
        f"/api/v1/projects/{proj['id']}/financials",
        f"/api/v1/clients/{cl['id']}/financials",
    ):
        resp = await client.get(url)
        assert resp.status_code == 200, resp.text
    proj_data = (await client.get(f"/api/v1/projects/{proj['id']}/financials")).json()["data"]
    assert _f(proj_data["actual_revenue_inr"]) == 0.0
    assert _f(proj_data["actual_margin_inr"]) == -20000.0  # 0 − 20000 resource cost
