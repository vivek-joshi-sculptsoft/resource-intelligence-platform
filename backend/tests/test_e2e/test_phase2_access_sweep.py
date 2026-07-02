"""Access control sweep — VRIP-109.

All 7 roles against every financial endpoint. Expectations come straight from
shared/ACCESS-MATRIX.md: 403 where access_level is NONE, 200 with null masking
where a role can see the endpoint but not sensitive fields, and write access
(invoice POST) restricted to FINANCE (invoicing EDIT).
"""

import uuid
from datetime import date, timedelta

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from tests.conftest import create_test_user, login_as, login_as_role


def _f(value):
    return None if value is None else float(value)


async def _post(client: AsyncClient, url: str, payload: dict, expect: int) -> dict:
    resp = await client.post(url, json=payload)
    assert resp.status_code == expect, f"POST {url}: {resp.status_code} != {expect}: {resp.text}"
    return resp.json().get("data", {}) if resp.status_code < 300 else {}


async def _build_scenario(client: AsyncClient, db: AsyncSession) -> dict:
    """FIXED_PRICE project with billing rate, loaded cost, non-human cost,
    APPROVED milestone and APPROVED invoice, plus one bench resource."""
    await login_as(client)

    cl = await _post(client, "/api/v1/clients", {"name": f"Client-{uuid.uuid4().hex[:6]}"}, 201)

    def resource_payload(name: str, **overrides) -> dict:
        return {
            "employee_id": f"EMP-{uuid.uuid4().hex[:6]}",
            "name": name,
            "designation": "Senior Developer",
            **overrides,
        }

    dm = await _post(client, "/api/v1/resources", resource_payload("Sweep DM"), 201)
    pm = await _post(client, "/api/v1/resources", resource_payload("Sweep PM"), 201)
    dev = await _post(
        client, "/api/v1/resources", resource_payload("Sweep Dev", loaded_cost_monthly=20000), 201
    )
    bench = await _post(
        client,
        "/api/v1/resources",
        resource_payload(
            "Sweep Bench",
            loaded_cost_monthly=66000,
            date_of_joining=(date.today() - timedelta(days=10)).isoformat(),
        ),
        201,
    )

    proj = await _post(
        client,
        "/api/v1/projects",
        {
            "name": f"Sweep-{uuid.uuid4().hex[:6]}",
            "client_id": cl["id"],
            "type": "FIXED_PRICE",
            "dm_id": dm["id"],
            "pm_id": pm["id"],
            "contract_end_date": (date.today() + timedelta(days=365)).isoformat(),
        },
        201,
    )
    await _post(
        client,
        f"/api/v1/projects/{proj['id']}/assignments",
        {
            "resource_id": dev["id"],
            "allocation_pct": 100,
            "billability_pct": 100,
            "is_shadow": False,
            "start_date": date.today().isoformat(),
            "billing_rate": 500,
        },
        201,
    )
    await _post(
        client,
        f"/api/v1/projects/{proj['id']}/costs",
        {
            "description": "Sweep hosting",
            "category": "CLOUD_INFRA",
            "amount": 4000.00,
            "currency": "INR",
            "cost_date": date.today().isoformat(),
        },
        201,
    )

    ms = await _post(
        client,
        f"/api/v1/projects/{proj['id']}/milestones",
        {"name": "Sweep milestone", "amount": 88000.0},
        201,
    )
    for status in ("DELIVERED", "APPROVED"):
        resp = await client.put(
            f"/api/v1/projects/{proj['id']}/milestones/{ms['id']}/status",
            json={"status": status},
        )
        assert resp.status_code == 200, resp.text

    # Second APPROVED milestone stays un-invoiced — used by the invoice write check
    ms2 = await _post(
        client,
        f"/api/v1/projects/{proj['id']}/milestones",
        {"name": "Sweep milestone 2", "amount": 1000.0},
        201,
    )
    for status in ("DELIVERED", "APPROVED"):
        resp = await client.put(
            f"/api/v1/projects/{proj['id']}/milestones/{ms2['id']}/status",
            json={"status": status},
        )
        assert resp.status_code == 200, resp.text

    fin_client, _ = await login_as_role(client, db, "FINANCE")
    inv = await _post(
        fin_client,
        f"/api/v1/projects/{proj['id']}/invoices",
        {
            "invoice_date": date.today().isoformat(),
            "amount": 88000.0,
            "currency": "INR",
            "exchange_rate": 1.0,
            "milestone_id": ms["id"],
        },
        201,
    )
    for status in ("SUBMITTED", "APPROVED"):
        resp = await fin_client.put(
            f"/api/v1/projects/{proj['id']}/invoices/{inv['id']}/status",
            json={"status": status},
        )
        assert resp.status_code == 200, resp.text

    return {
        "client": cl,
        "project": proj,
        "dm": dm,
        "pm": pm,
        "bench": bench,
        "milestone": ms,
        "milestone2": ms2,
    }


async def _login_role(
    client: AsyncClient, db: AsyncSession, role: str, ctx: dict
) -> None:
    """Log in as the given role. CEO uses the seeded admin; DM/PM get linked to
    the scenario project so OWN_PORTFOLIO scope resolves to it."""
    if role == "CEO":
        await login_as(client)
        return
    user = await create_test_user(db, role, email=f"{role.lower()}-{uuid.uuid4().hex[:6]}@test.com")
    if role == "DM":
        user.resource_id = uuid.UUID(ctx["dm"]["id"])
    elif role == "PM":
        user.resource_id = uuid.UUID(ctx["pm"]["id"])
    await db.commit()
    resp = await client.post(
        "/api/v1/auth/login", json={"email": user.email, "password": "TestPass123"}
    )
    assert resp.status_code == 200


# One row per role: expected status per endpoint (see ACCESS-MATRIX.md).
#   proj_fin/client_fin/dash_fin gate on project_margin
#   bench gates on bench_data (cost fields masked by ctc_loaded_cost)
#   invoices/receivables gate on invoicing; POST needs EDIT (FINANCE only)
#   costs gates on non_human_costs; milestones on project_details
SWEEP = {
    #        proj  client dash  bench invGET recv  invPOST costs  miles
    "CEO":      (200, 200, 200, 200, 200, 200, 403, 200, 200),
    "CTO":      (200, 200, 200, 200, 200, 200, 403, 200, 200),
    "FINANCE":  (200, 200, 200, 200, 200, 200, 201, 200, 200),
    "DM":       (200, 200, 200, 200, 403, 403, 403, 200, 200),
    "PM":       (403, 403, 403, 403, 403, 403, 403, 200, 200),
    "HR":       (403, 403, 403, 200, 403, 403, 403, 403, 403),
    "ENGINEER": (403, 403, 403, 200, 403, 403, 403, 403, 403),
}

# Roles allowed to see loaded-cost-derived figures (ctc_loaded_cost VIEW).
COST_VISIBLE_ROLES = {"CEO", "CTO", "FINANCE"}


@pytest.mark.asyncio
@pytest.mark.parametrize("role", list(SWEEP.keys()))
async def test_role_sweep_financial_endpoints(role: str, client: AsyncClient, db: AsyncSession):
    ctx = await _build_scenario(client, db)
    proj_id = ctx["project"]["id"]
    (
        exp_proj,
        exp_client,
        exp_dash,
        exp_bench,
        exp_inv_get,
        exp_recv,
        exp_inv_post,
        exp_costs,
        exp_miles,
    ) = SWEEP[role]

    await _login_role(client, db, role, ctx)

    # Project financials
    resp = await client.get(f"/api/v1/projects/{proj_id}/financials")
    assert resp.status_code == exp_proj, f"{role} proj fin: {resp.status_code}: {resp.text}"
    if exp_proj == 200:
        data = resp.json()["data"]
        if role in COST_VISIBLE_ROLES:
            assert _f(data["resource_cost_inr"]) == 20000.0
            assert _f(data["actual_revenue_inr"]) == 88000.0
        else:  # DM — costs and invoicing masked to null, never omitted
            assert "resource_cost_inr" in data
            assert data["resource_cost_inr"] is None
            assert data["total_cost_inr"] is None
            assert data["actual_revenue_inr"] is None
            assert _f(data["projected_revenue_inr"]) == 88000.0  # billing_rates VIEW

    # Client financials
    resp = await client.get(f"/api/v1/clients/{ctx['client']['id']}/financials")
    assert resp.status_code == exp_client, f"{role} client fin: {resp.status_code}"
    if exp_client == 200 and role not in COST_VISIBLE_ROLES:
        data = resp.json()["data"]
        assert data["total_cost_inr"] is None
        assert data["total_actual_revenue_inr"] is None

    # Company dashboard financials
    resp = await client.get("/api/v1/dashboard/financials")
    assert resp.status_code == exp_dash, f"{role} dash fin: {resp.status_code}"

    # Bench cost — HR/ENGINEER/DM may see bench data but never cost figures
    resp = await client.get(f"/api/v1/resources/{ctx['bench']['id']}/bench-cost")
    assert resp.status_code == exp_bench, f"{role} bench: {resp.status_code}: {resp.text}"
    if exp_bench == 200:
        data = resp.json()["data"]
        assert data["days_on_bench"] == 10
        if role in COST_VISIBLE_ROLES:
            assert _f(data["daily_bench_cost_inr"]) == 3000.0  # 66000 / 22
        else:
            assert data["daily_bench_cost_inr"] is None
            assert data["total_bench_cost_inr"] is None

    # Invoices list + receivables
    resp = await client.get(f"/api/v1/projects/{proj_id}/invoices")
    assert resp.status_code == exp_inv_get, f"{role} invoices: {resp.status_code}"
    resp = await client.get("/api/v1/invoices/receivables")
    assert resp.status_code == exp_recv, f"{role} receivables: {resp.status_code}"

    # Invoice create (write) — FINANCE only
    resp = await client.post(
        f"/api/v1/projects/{proj_id}/invoices",
        json={
            "invoice_date": date.today().isoformat(),
            "amount": 1000.0,
            "currency": "INR",
            "exchange_rate": 1.0,
            "milestone_id": ctx["milestone2"]["id"],
        },
    )
    assert resp.status_code == exp_inv_post, f"{role} invoice POST: {resp.status_code}: {resp.text}"

    # Non-human costs
    resp = await client.get(f"/api/v1/projects/{proj_id}/costs")
    assert resp.status_code == exp_costs, f"{role} costs: {resp.status_code}"

    # Milestones
    resp = await client.get(f"/api/v1/projects/{proj_id}/milestones")
    assert resp.status_code == exp_miles, f"{role} milestones: {resp.status_code}"
