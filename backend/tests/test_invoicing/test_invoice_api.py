"""Tests for Invoice CRUD API + lifecycle transitions + multi-currency — VRIP-95."""

import uuid
from datetime import date, timedelta

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from tests.conftest import login_as, login_as_role


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
        "billing_currency": "USD",
        "contract_end_date": (date.today() + timedelta(days=365)).isoformat(),
        **overrides,
    }
    resp = await client.post("/api/v1/projects", json=payload)
    assert resp.status_code == 201, resp.text
    return resp.json()["data"]


async def _setup_project(client: AsyncClient, **project_overrides) -> tuple[dict, dict, dict]:
    cl = await _create_client_entity(client)
    dm = await _create_resource(client, name="DM Resource")
    pm = await _create_resource(client, name="PM Resource")
    proj = await _create_project(client, cl["id"], dm["id"], pm["id"], **project_overrides)
    return proj, dm, pm


async def _create_approved_milestone(client: AsyncClient, project_id: str) -> dict:
    """Create a milestone and advance it to APPROVED status."""
    resp = await client.post(
        f"/api/v1/projects/{project_id}/milestones",
        json={"name": "MS-1", "amount": 100000.00, "planned_delivery_date": date.today().isoformat()},
    )
    assert resp.status_code == 201
    ms = resp.json()["data"]
    # PLANNED → DELIVERED
    resp = await client.put(
        f"/api/v1/projects/{project_id}/milestones/{ms['id']}/status",
        json={"status": "DELIVERED"},
    )
    assert resp.status_code == 200
    # DELIVERED → APPROVED
    resp = await client.put(
        f"/api/v1/projects/{project_id}/milestones/{ms['id']}/status",
        json={"status": "APPROVED"},
    )
    assert resp.status_code == 200
    return resp.json()["data"]


def _invoice_payload(**overrides) -> dict:
    return {
        "invoice_date": date.today().isoformat(),
        "amount": 50000.00,
        "currency": "USD",
        "exchange_rate": 83.50,
        **overrides,
    }


# ── Happy Path: Create / List ──


@pytest.mark.asyncio
async def test_create_invoice_for_fp_project(client: AsyncClient, db: AsyncSession):
    """FP project: create invoice linked to an approved milestone."""
    await login_as(client)
    proj, _, _ = await _setup_project(client)

    # Need Finance role to create invoices
    client, _ = await login_as_role(client, db, "FINANCE")
    ms = await _create_approved_milestone(client, proj["id"])

    resp = await client.post(
        f"/api/v1/projects/{proj['id']}/invoices",
        json=_invoice_payload(milestone_id=ms["id"]),
    )
    assert resp.status_code == 201, resp.text
    data = resp.json()["data"]
    assert data["amount"] == 50000.00
    assert data["currency"] == "USD"
    assert data["exchange_rate"] == 83.50
    assert data["amount_inr"] == 4175000.00  # 50000 × 83.50
    assert data["status"] == "DRAFT"
    assert data["milestone_id"] == ms["id"]
    assert data["milestone"] is not None


@pytest.mark.asyncio
async def test_invoice_submission_cascades_milestone_status(client: AsyncClient, db: AsyncSession):
    """See FSD §6.3 — invoice SUBMITTED/PAID auto-transitions linked milestone."""
    await login_as(client)
    proj, _, _ = await _setup_project(client)
    client, _ = await login_as_role(client, db, "FINANCE")
    ms = await _create_approved_milestone(client, proj["id"])

    resp = await client.post(
        f"/api/v1/projects/{proj['id']}/invoices",
        json=_invoice_payload(milestone_id=ms["id"]),
    )
    inv = resp.json()["data"]

    # Invoice DRAFT → SUBMITTED cascades milestone APPROVED → INVOICED
    resp = await client.put(
        f"/api/v1/projects/{proj['id']}/invoices/{inv['id']}/status",
        json={"status": "SUBMITTED"},
    )
    assert resp.status_code == 200
    resp = await client.get(f"/api/v1/projects/{proj['id']}/milestones/{ms['id']}")
    assert resp.json()["data"]["status"] == "INVOICED"

    # Invoice SUBMITTED → APPROVED → PAID cascades milestone INVOICED → PAID
    resp = await client.put(
        f"/api/v1/projects/{proj['id']}/invoices/{inv['id']}/status",
        json={"status": "APPROVED"},
    )
    assert resp.status_code == 200
    resp = await client.put(
        f"/api/v1/projects/{proj['id']}/invoices/{inv['id']}/status",
        json={"status": "PAID"},
    )
    assert resp.status_code == 200
    resp = await client.get(f"/api/v1/projects/{proj['id']}/milestones/{ms['id']}")
    assert resp.json()["data"]["status"] == "PAID"


@pytest.mark.asyncio
async def test_create_invoice_for_tm_project(client: AsyncClient, db: AsyncSession):
    """T&M project: no milestone needed, uses billing period."""
    await login_as(client)
    proj, _, _ = await _setup_project(client, type="TIME_AND_MATERIAL")

    client, _ = await login_as_role(client, db, "FINANCE")

    today = date.today()
    resp = await client.post(
        f"/api/v1/projects/{proj['id']}/invoices",
        json=_invoice_payload(
            billing_period_start=today.isoformat(),
            billing_period_end=(today + timedelta(days=30)).isoformat(),
            notes="Monthly billing",
        ),
    )
    assert resp.status_code == 201, resp.text
    data = resp.json()["data"]
    assert data["billing_period_start"] == today.isoformat()
    assert data["billing_period_end"] == (today + timedelta(days=30)).isoformat()
    assert data["notes"] == "Monthly billing"
    assert data["milestone_id"] is None


@pytest.mark.asyncio
async def test_create_invoice_inr_auto_exchange_rate(client: AsyncClient, db: AsyncSession):
    """INR currency auto-sets exchange_rate=1.0. See BUSINESS-RULES.md §7.7."""
    await login_as(client)
    proj, _, _ = await _setup_project(client, type="TIME_AND_MATERIAL", billing_currency="INR")

    client, _ = await login_as_role(client, db, "FINANCE")

    resp = await client.post(
        f"/api/v1/projects/{proj['id']}/invoices",
        json={"invoice_date": date.today().isoformat(), "amount": 100000.00, "currency": "INR"},
    )
    assert resp.status_code == 201, resp.text
    data = resp.json()["data"]
    assert data["exchange_rate"] == 1.0
    assert data["amount_inr"] == 100000.00


@pytest.mark.asyncio
async def test_list_invoices_with_pagination(client: AsyncClient, db: AsyncSession):
    await login_as(client)
    proj, _, _ = await _setup_project(client, type="TIME_AND_MATERIAL")

    client, _ = await login_as_role(client, db, "FINANCE")

    for i in range(3):
        resp = await client.post(
            f"/api/v1/projects/{proj['id']}/invoices",
            json=_invoice_payload(amount=10000.00 + i),
        )
        assert resp.status_code == 201

    resp = await client.get(f"/api/v1/projects/{proj['id']}/invoices?page=1&limit=2")
    assert resp.status_code == 200
    body = resp.json()
    assert len(body["data"]) == 2
    assert body["total"] == 3
    assert body["page"] == 1


@pytest.mark.asyncio
async def test_list_invoices_filter_by_status(client: AsyncClient, db: AsyncSession):
    await login_as(client)
    proj, _, _ = await _setup_project(client, type="TIME_AND_MATERIAL")

    client, _ = await login_as_role(client, db, "FINANCE")

    # Create 2 invoices, submit one
    resp1 = await client.post(
        f"/api/v1/projects/{proj['id']}/invoices",
        json=_invoice_payload(amount=10000.00),
    )
    inv1 = resp1.json()["data"]
    await client.post(
        f"/api/v1/projects/{proj['id']}/invoices",
        json=_invoice_payload(amount=20000.00),
    )

    await client.put(
        f"/api/v1/projects/{proj['id']}/invoices/{inv1['id']}/status",
        json={"status": "SUBMITTED"},
    )

    resp = await client.get(f"/api/v1/projects/{proj['id']}/invoices?status=DRAFT")
    assert resp.status_code == 200
    assert len(resp.json()["data"]) == 1

    resp = await client.get(f"/api/v1/projects/{proj['id']}/invoices?status=SUBMITTED")
    assert resp.status_code == 200
    assert len(resp.json()["data"]) == 1


# ── Validations ──


@pytest.mark.asyncio
async def test_create_invoice_rejects_non_positive_amount(client: AsyncClient, db: AsyncSession):
    await login_as(client)
    proj, _, _ = await _setup_project(client, type="TIME_AND_MATERIAL")
    client, _ = await login_as_role(client, db, "FINANCE")

    resp = await client.post(
        f"/api/v1/projects/{proj['id']}/invoices",
        json=_invoice_payload(amount=-100),
    )
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_create_invoice_rejects_non_positive_exchange_rate(client: AsyncClient, db: AsyncSession):
    await login_as(client)
    proj, _, _ = await _setup_project(client, type="TIME_AND_MATERIAL")
    client, _ = await login_as_role(client, db, "FINANCE")

    resp = await client.post(
        f"/api/v1/projects/{proj['id']}/invoices",
        json=_invoice_payload(exchange_rate=-1),
    )
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_fp_invoice_requires_milestone(client: AsyncClient, db: AsyncSession):
    """See FSD §11 — Fixed price invoices must be linked to a milestone."""
    await login_as(client)
    proj, _, _ = await _setup_project(client)
    client, _ = await login_as_role(client, db, "FINANCE")

    resp = await client.post(
        f"/api/v1/projects/{proj['id']}/invoices",
        json=_invoice_payload(),
    )
    assert resp.status_code == 422, resp.text
    assert "milestone" in resp.json()["message"].lower()


@pytest.mark.asyncio
async def test_fp_invoice_rejects_unapproved_milestone(client: AsyncClient, db: AsyncSession):
    """See FSD §11 — Milestone must be approved before invoicing."""
    await login_as(client)
    proj, _, _ = await _setup_project(client)
    client, _ = await login_as_role(client, db, "FINANCE")

    # Create milestone in PLANNED status (not approved)
    resp = await client.post(
        f"/api/v1/projects/{proj['id']}/milestones",
        json={"name": "MS-unapproved", "amount": 50000.00},
    )
    assert resp.status_code == 201
    ms = resp.json()["data"]

    resp = await client.post(
        f"/api/v1/projects/{proj['id']}/invoices",
        json=_invoice_payload(milestone_id=ms["id"]),
    )
    assert resp.status_code == 422, resp.text
    assert "approved" in resp.json()["message"].lower()


@pytest.mark.asyncio
async def test_non_inr_requires_exchange_rate(client: AsyncClient, db: AsyncSession):
    await login_as(client)
    proj, _, _ = await _setup_project(client, type="TIME_AND_MATERIAL")
    client, _ = await login_as_role(client, db, "FINANCE")

    resp = await client.post(
        f"/api/v1/projects/{proj['id']}/invoices",
        json={"invoice_date": date.today().isoformat(), "amount": 5000.00, "currency": "USD"},
    )
    assert resp.status_code == 422, resp.text
    assert "exchange rate" in resp.json()["message"].lower()


# ── Update ──


@pytest.mark.asyncio
async def test_update_invoice_in_draft_status(client: AsyncClient, db: AsyncSession):
    await login_as(client)
    proj, _, _ = await _setup_project(client, type="TIME_AND_MATERIAL")
    client, _ = await login_as_role(client, db, "FINANCE")

    resp = await client.post(
        f"/api/v1/projects/{proj['id']}/invoices",
        json=_invoice_payload(amount=10000.00),
    )
    inv = resp.json()["data"]

    resp = await client.put(
        f"/api/v1/projects/{proj['id']}/invoices/{inv['id']}",
        json={"amount": 25000.00, "notes": "Updated amount"},
    )
    assert resp.status_code == 200, resp.text
    data = resp.json()["data"]
    assert data["amount"] == 25000.00
    assert data["notes"] == "Updated amount"
    assert data["amount_inr"] == 25000.00 * 83.50


@pytest.mark.asyncio
async def test_update_invoice_rejected_outside_draft(client: AsyncClient, db: AsyncSession):
    await login_as(client)
    proj, _, _ = await _setup_project(client, type="TIME_AND_MATERIAL")
    client, _ = await login_as_role(client, db, "FINANCE")

    resp = await client.post(
        f"/api/v1/projects/{proj['id']}/invoices",
        json=_invoice_payload(),
    )
    inv = resp.json()["data"]

    # Transition to SUBMITTED
    await client.put(
        f"/api/v1/projects/{proj['id']}/invoices/{inv['id']}/status",
        json={"status": "SUBMITTED"},
    )

    resp = await client.put(
        f"/api/v1/projects/{proj['id']}/invoices/{inv['id']}",
        json={"amount": 99999.00},
    )
    assert resp.status_code == 422, resp.text
    assert "DRAFT" in resp.json()["message"]


# ── Status Transitions ──


@pytest.mark.asyncio
async def test_full_invoice_lifecycle(client: AsyncClient, db: AsyncSession):
    """See FSD §6.3 — DRAFT → SUBMITTED → APPROVED → PAID."""
    await login_as(client)
    proj, _, _ = await _setup_project(client, type="TIME_AND_MATERIAL")
    client, _ = await login_as_role(client, db, "FINANCE")

    resp = await client.post(
        f"/api/v1/projects/{proj['id']}/invoices",
        json=_invoice_payload(),
    )
    inv = resp.json()["data"]
    assert inv["status"] == "DRAFT"

    # DRAFT → SUBMITTED
    resp = await client.put(
        f"/api/v1/projects/{proj['id']}/invoices/{inv['id']}/status",
        json={"status": "SUBMITTED"},
    )
    assert resp.status_code == 200
    assert resp.json()["data"]["status"] == "SUBMITTED"

    # SUBMITTED → APPROVED
    resp = await client.put(
        f"/api/v1/projects/{proj['id']}/invoices/{inv['id']}/status",
        json={"status": "APPROVED"},
    )
    assert resp.status_code == 200
    assert resp.json()["data"]["status"] == "APPROVED"

    # APPROVED → PAID
    resp = await client.put(
        f"/api/v1/projects/{proj['id']}/invoices/{inv['id']}/status",
        json={"status": "PAID"},
    )
    assert resp.status_code == 200
    assert resp.json()["data"]["status"] == "PAID"


@pytest.mark.asyncio
async def test_invalid_transition_rejected(client: AsyncClient, db: AsyncSession):
    """Forward-only — no backward transitions for invoices."""
    await login_as(client)
    proj, _, _ = await _setup_project(client, type="TIME_AND_MATERIAL")
    client, _ = await login_as_role(client, db, "FINANCE")

    resp = await client.post(
        f"/api/v1/projects/{proj['id']}/invoices",
        json=_invoice_payload(),
    )
    inv = resp.json()["data"]

    # DRAFT → SUBMITTED
    await client.put(
        f"/api/v1/projects/{proj['id']}/invoices/{inv['id']}/status",
        json={"status": "SUBMITTED"},
    )

    # SUBMITTED → DRAFT (backward — should fail)
    resp = await client.put(
        f"/api/v1/projects/{proj['id']}/invoices/{inv['id']}/status",
        json={"status": "DRAFT"},
    )
    assert resp.status_code == 422

    # SUBMITTED → PAID (skip — should fail)
    resp = await client.put(
        f"/api/v1/projects/{proj['id']}/invoices/{inv['id']}/status",
        json={"status": "PAID"},
    )
    assert resp.status_code == 422


# ── Multi-Currency ──


@pytest.mark.asyncio
async def test_multi_currency_amount_inr_computed(client: AsyncClient, db: AsyncSession):
    """See BUSINESS-RULES.md §7.7 — amount_inr = amount × exchange_rate."""
    await login_as(client)
    proj, _, _ = await _setup_project(client, type="TIME_AND_MATERIAL")
    client, _ = await login_as_role(client, db, "FINANCE")

    resp = await client.post(
        f"/api/v1/projects/{proj['id']}/invoices",
        json=_invoice_payload(amount=1000.00, currency="EUR", exchange_rate=90.25),
    )
    assert resp.status_code == 201
    data = resp.json()["data"]
    assert data["amount_inr"] == 90250.00  # 1000 × 90.25


# ── Receivables ──


@pytest.mark.asyncio
async def test_receivables_returns_non_paid_invoices(client: AsyncClient, db: AsyncSession):
    await login_as(client)
    proj, _, _ = await _setup_project(client, type="TIME_AND_MATERIAL")
    client, _ = await login_as_role(client, db, "FINANCE")

    # Create 3 invoices
    ids = []
    for i in range(3):
        resp = await client.post(
            f"/api/v1/projects/{proj['id']}/invoices",
            json=_invoice_payload(amount=10000.00 * (i + 1)),
        )
        ids.append(resp.json()["data"]["id"])

    # Move first to SUBMITTED, second to PAID
    await client.put(
        f"/api/v1/projects/{proj['id']}/invoices/{ids[0]}/status",
        json={"status": "SUBMITTED"},
    )
    await client.put(
        f"/api/v1/projects/{proj['id']}/invoices/{ids[1]}/status",
        json={"status": "SUBMITTED"},
    )
    await client.put(
        f"/api/v1/projects/{proj['id']}/invoices/{ids[1]}/status",
        json={"status": "APPROVED"},
    )
    await client.put(
        f"/api/v1/projects/{proj['id']}/invoices/{ids[1]}/status",
        json={"status": "PAID"},
    )

    resp = await client.get("/api/v1/invoices/receivables")
    assert resp.status_code == 200
    data = resp.json()["data"]
    returned_ids = {d["id"] for d in data}
    assert ids[0] in returned_ids  # SUBMITTED
    assert ids[1] not in returned_ids  # PAID — excluded
    assert ids[2] in returned_ids  # DRAFT


@pytest.mark.asyncio
async def test_receivables_filter_by_status(client: AsyncClient, db: AsyncSession):
    await login_as(client)
    proj, _, _ = await _setup_project(client, type="TIME_AND_MATERIAL")
    client, _ = await login_as_role(client, db, "FINANCE")

    resp = await client.post(
        f"/api/v1/projects/{proj['id']}/invoices",
        json=_invoice_payload(amount=10000.00),
    )
    inv = resp.json()["data"]

    await client.put(
        f"/api/v1/projects/{proj['id']}/invoices/{inv['id']}/status",
        json={"status": "SUBMITTED"},
    )

    resp = await client.get("/api/v1/invoices/receivables?status=SUBMITTED")
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert all(d["status"] == "SUBMITTED" for d in data)


@pytest.mark.asyncio
async def test_receivables_includes_project_name(client: AsyncClient, db: AsyncSession):
    await login_as(client)
    proj, _, _ = await _setup_project(client, type="TIME_AND_MATERIAL")
    client, _ = await login_as_role(client, db, "FINANCE")

    resp = await client.post(
        f"/api/v1/projects/{proj['id']}/invoices",
        json=_invoice_payload(),
    )
    assert resp.status_code == 201

    resp = await client.get("/api/v1/invoices/receivables")
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert len(data) >= 1
    assert data[0]["project_name"] is not None


@pytest.mark.asyncio
async def test_receivables_includes_client_name(client: AsyncClient, db: AsyncSession):
    await login_as(client)
    proj, _, _ = await _setup_project(client, type="TIME_AND_MATERIAL")
    client, _ = await login_as_role(client, db, "FINANCE")

    resp = await client.post(
        f"/api/v1/projects/{proj['id']}/invoices",
        json=_invoice_payload(),
    )
    assert resp.status_code == 201

    resp = await client.get("/api/v1/invoices/receivables")
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert len(data) >= 1
    assert data[0]["client_name"] is not None


# ── Access Control ──


@pytest.mark.asyncio
async def test_ceo_can_view_invoices(client: AsyncClient, db: AsyncSession):
    """CEO has VIEW ALL for invoicing."""
    await login_as(client)
    proj, _, _ = await _setup_project(client, type="TIME_AND_MATERIAL")

    # Create invoice as finance
    client, _ = await login_as_role(client, db, "FINANCE")
    await client.post(
        f"/api/v1/projects/{proj['id']}/invoices",
        json=_invoice_payload(),
    )

    # CEO can view
    await login_as(client)  # admin is CEO
    resp = await client.get(f"/api/v1/projects/{proj['id']}/invoices")
    assert resp.status_code == 200


@pytest.mark.asyncio
async def test_ceo_cannot_create_invoices(client: AsyncClient, db: AsyncSession):
    """CEO has VIEW, not EDIT — cannot create invoices."""
    await login_as(client)
    proj, _, _ = await _setup_project(client, type="TIME_AND_MATERIAL")

    resp = await client.post(
        f"/api/v1/projects/{proj['id']}/invoices",
        json=_invoice_payload(),
    )
    assert resp.status_code == 403


@pytest.mark.asyncio
async def test_dm_has_no_access_to_invoices(client: AsyncClient, db: AsyncSession):
    """DM has NONE for invoicing."""
    await login_as(client)
    proj, dm, _ = await _setup_project(client, type="TIME_AND_MATERIAL")

    client, _ = await login_as_role(client, db, "DM")
    resp = await client.get(f"/api/v1/projects/{proj['id']}/invoices")
    assert resp.status_code == 403


@pytest.mark.asyncio
async def test_pm_has_no_access_to_invoices(client: AsyncClient, db: AsyncSession):
    """PM has NONE for invoicing."""
    await login_as(client)
    proj, _, pm = await _setup_project(client, type="TIME_AND_MATERIAL")

    client, _ = await login_as_role(client, db, "PM")
    resp = await client.get(f"/api/v1/projects/{proj['id']}/invoices")
    assert resp.status_code == 403


@pytest.mark.asyncio
async def test_engineer_has_no_access_to_invoices(client: AsyncClient, db: AsyncSession):
    await login_as(client)
    proj, _, _ = await _setup_project(client, type="TIME_AND_MATERIAL")

    client, _ = await login_as_role(client, db, "ENGINEER")
    resp = await client.get(f"/api/v1/projects/{proj['id']}/invoices")
    assert resp.status_code == 403


@pytest.mark.asyncio
async def test_hr_has_no_access_to_invoices(client: AsyncClient, db: AsyncSession):
    await login_as(client)
    proj, _, _ = await _setup_project(client, type="TIME_AND_MATERIAL")

    client, _ = await login_as_role(client, db, "HR")
    resp = await client.get(f"/api/v1/projects/{proj['id']}/invoices")
    assert resp.status_code == 403


@pytest.mark.asyncio
async def test_engineer_cannot_access_receivables(client: AsyncClient, db: AsyncSession):
    await login_as(client)
    client, _ = await login_as_role(client, db, "ENGINEER")
    resp = await client.get("/api/v1/invoices/receivables")
    assert resp.status_code == 403


# ── Audit Logging ──


@pytest.mark.asyncio
async def test_create_invoice_creates_audit_log(client: AsyncClient, db: AsyncSession):
    await login_as(client)
    proj, _, _ = await _setup_project(client, type="TIME_AND_MATERIAL")
    client, _ = await login_as_role(client, db, "FINANCE")

    resp = await client.post(
        f"/api/v1/projects/{proj['id']}/invoices",
        json=_invoice_payload(),
    )
    assert resp.status_code == 201

    from sqlalchemy import select
    from app.modules.audit.models import AuditLog
    result = await db.execute(
        select(AuditLog).where(
            AuditLog.entity_type == "Invoice",
            AuditLog.action == "CREATE",
        )
    )
    logs = result.scalars().all()
    assert len(logs) >= 1


@pytest.mark.asyncio
async def test_status_transition_creates_audit_log(client: AsyncClient, db: AsyncSession):
    await login_as(client)
    proj, _, _ = await _setup_project(client, type="TIME_AND_MATERIAL")
    client, _ = await login_as_role(client, db, "FINANCE")

    resp = await client.post(
        f"/api/v1/projects/{proj['id']}/invoices",
        json=_invoice_payload(),
    )
    inv = resp.json()["data"]

    await client.put(
        f"/api/v1/projects/{proj['id']}/invoices/{inv['id']}/status",
        json={"status": "SUBMITTED"},
    )

    from sqlalchemy import select
    from app.modules.audit.models import AuditLog
    result = await db.execute(
        select(AuditLog).where(
            AuditLog.entity_type == "Invoice",
            AuditLog.action == "UPDATE",
            AuditLog.field_name == "status",
        )
    )
    logs = result.scalars().all()
    assert len(logs) >= 1
