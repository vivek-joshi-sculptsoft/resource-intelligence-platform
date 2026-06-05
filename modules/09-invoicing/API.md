# Module 09: Invoicing — API Endpoints

## Milestone Endpoints (Fixed Price Projects Only)

### GET /api/projects/:projectId/milestones
**Description:** List milestones for an FP project ordered by sort_order.
**Auth:** CEO, CTO; DM (own portfolio); PM (own portfolio); Finance. Reference `shared/ACCESS-MATRIX.md`.
**Scope:** OWN_PORTFOLIO for DM/PM
**Response:** Array: `[{ id, name, amount, planned_delivery_date, actual_delivery_date, status, sort_order }]`

---

### POST /api/projects/:projectId/milestones
**Description:** Create a milestone.
**Auth:** PM (own portfolio), DM (own portfolio), CEO, CTO
**Request Body:**
```json
{
  "name": "string*",
  "amount": "decimal* > 0",
  "planned_delivery_date": "date",
  "sort_order": "integer"
}
```
**Validations:** Project must be FIXED_PRICE.
**Notes:** Audit logged.

---

### PUT /api/projects/:projectId/milestones/:id
**Description:** Update a milestone.
**Auth:** PM (own portfolio), DM (own portfolio), CEO, CTO
**Request Body:** Any subset of milestone fields.
**Validations:** Only editable in PLANNED status (name, amount, dates). Status changes via separate endpoint.
**Notes:** Audit logged per changed field.

---

### PUT /api/projects/:projectId/milestones/:id/status
**Description:** Transition milestone status.
**Auth:** PM/DM (PLANNED→DELIVERED, DELIVERED→APPROVED); Finance (APPROVED→INVOICED creates Invoice, INVOICED→PAID); PM/DM for backward transitions.
**Request Body:** `{ "status": "DELIVERED|APPROVED|PLANNED|DELIVERED (backward)" }`
**Validations:** FSD §6.2 allowed transitions only.
**Notes:** PLANNED→DELIVERED sets `actual_delivery_date`. Flags delivery delay if > planned. Audit logged.

---

## Invoice Endpoints

### GET /api/projects/:projectId/invoices
**Description:** List invoices for a project.
**Auth:** CEO, CTO, Finance (EDIT ALL); DM/PM have NONE for invoicing. Reference `shared/ACCESS-MATRIX.md` (`invoicing`).
**Scope:** ALL for CEO/CTO/Finance
**Response:** Array: `[{ id, invoice_date, amount, currency, exchange_rate, amount_inr, status, milestone_id, billing_period_start, billing_period_end, notes }]`

---

### POST /api/projects/:projectId/invoices
**Description:** Create an invoice.
**Auth:** Finance (EDIT)
**Scope:** ALL
**Request Body:**
```json
{
  "invoice_date": "date*",
  "amount": "decimal* > 0",
  "currency": "string* (copied from project)",
  "exchange_rate": "decimal > 0 (auto 1.0 for INR)",
  "milestone_id": "uuid (required for FP)",
  "billing_period_start": "date (T&M/Onboarding)",
  "billing_period_end": "date (T&M/Onboarding)",
  "notes": "string"
}
```
**Validations:** All 5 FSD §11 invoice validations.
**Notes:** `amount_inr` computed server-side. Audit logged.

---

### PUT /api/projects/:projectId/invoices/:id
**Description:** Update invoice fields (while in DRAFT status only).
**Auth:** Finance
**Request Body:** Any subset of invoice fields.
**Notes:** Audit logged per changed field.

---

### PUT /api/projects/:projectId/invoices/:id/status
**Description:** Transition invoice status.
**Auth:** Finance
**Request Body:** `{ "status": "SUBMITTED|APPROVED|PAID" }`
**Validations:** FSD §6.3 forward-only transitions.
**Notes:** Audit logged.

---

### GET /api/invoices/receivables
**Description:** Outstanding receivables — all invoices not yet PAID.
**Auth:** Finance, CEO, CTO
**Scope:** ALL
**Response:** Grouped by client and project, showing amount (original) and amount_inr.
**Notes:** `?status=SUBMITTED,APPROVED` to filter by specific statuses.
