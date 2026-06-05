# Module 02: Client Management — API Endpoints

## Endpoints

### GET /api/clients
**Description:** List all clients with basic stats.
**Auth:** CEO, CTO (EDIT ALL); DM, PM (VIEW OWN_PORTFOLIO); Finance, HR (VIEW ALL). Reference `shared/ACCESS-MATRIX.md`.
**Scope:** ALL for CEO/CTO/Finance/HR; OWN_PORTFOLIO for DM/PM
**Response:** Paginated. Each item: `{ id, name, industry, engagement_start_date, active_project_count, is_active }`
**Notes:** `?page=1&limit=20&status=ACTIVE&search=<name>`

---

### POST /api/clients
**Description:** Create a new client.
**Auth:** CEO, CTO (EDIT)
**Scope:** ALL
**Request Body:**
```json
{
  "name": "string*",
  "industry": "string",
  "contact_name": "string",
  "contact_email": "string",
  "contact_phone": "string",
  "engagement_start_date": "date",
  "notes": "string"
}
```
**Response:** Created client object.
**Validations:** Name required; name must be unique.
**Notes:** Audit log CREATE entry.

---

### GET /api/clients/:id
**Description:** Get client detail with project list.
**Auth:** CEO, CTO; DM (own portfolio); Finance, HR
**Scope:** As above
**Response:**
```json
{
  "id", "name", "industry", "contact_name", "contact_email", "contact_phone",
  "engagement_start_date", "notes", "is_active", "created_at",
  "projects": [{ "id", "name", "type", "status", "dm_id", "pm_id" }],
  "dashboard": { "active_resource_count": int, "active_project_count": int }
}
```

---

### PUT /api/clients/:id
**Description:** Update client fields.
**Auth:** CEO, CTO (EDIT)
**Scope:** ALL
**Request Body:** Any subset of client fields.
**Validations:** Name unique if changed. Deactivation blocked if active projects exist.
**Notes:** Audit log UPDATE entry per changed field.

---

### DELETE /api/clients/:id
**Description:** Soft-delete (deactivate) a client.
**Auth:** CEO, CTO only
**Scope:** ALL
**Validations:** Block if any project with `status = ACTIVE` exists for this client.
**Response:** `{ "success": true }` or error.
**Notes:** Sets `is_active = false`. Audit logged.

---

### GET /api/clients/:id/dashboard
**Description:** Aggregated metrics for the client.
**Auth:** Same as GET /api/clients/:id
**Scope:** Same
**Response:**
```json
{
  "active_resource_count": int,
  "active_project_count": int,
  "total_monthly_billing_inr": decimal,   // Phase 2 — null in Phase 1
  "total_cost_inr": decimal,              // Phase 2 — null in Phase 1
  "aggregate_margin_inr": decimal,        // Phase 2 — null in Phase 1
  "project_count_by_type": { "FIXED_PRICE": int, "TIME_AND_MATERIAL": int, "CLIENT_ONBOARDING": int }
}
```
