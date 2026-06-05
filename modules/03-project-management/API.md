# Module 03: Project Management — API Endpoints

## Endpoints

### GET /api/projects
**Description:** List projects with filters.
**Auth:** CEO, CTO (ALL); DM (OWN_PORTFOLIO — dm_id = me); PM (OWN_PORTFOLIO — pm_id = me); Finance, HR (VIEW ALL). Reference `shared/ACCESS-MATRIX.md`.
**Scope:** Per role (see above)
**Response:** Paginated list. Each item: `{ id, name, client_name, type, status, billing_currency, dm_name, pm_name, start_date, contract_end_date }`
**Notes:** `?page=1&limit=20&status=ACTIVE&client_id=<uuid>&type=FIXED_PRICE&dm_id=<uuid>&search=<name>`

---

### POST /api/projects
**Description:** Create a new project.
**Auth:** CEO, CTO, DM (EDIT — creates within their portfolio)
**Scope:** ALL for CEO/CTO; OWN_PORTFOLIO enforced by assigning dm_id = current user for DM
**Request Body:**
```json
{
  "name": "string*",
  "client_id": "uuid*",
  "type": "FIXED_PRICE|TIME_AND_MATERIAL|CLIENT_ONBOARDING *",
  "billing_currency": "string default INR",
  "start_date": "date",
  "contract_end_date": "date (required for T&M/ONBOARDING)",
  "dm_id": "uuid*",
  "pm_id": "uuid*",
  "worklog_enabled": "boolean default false",
  "notes": "string"
}
```
**Validations:** Name, client_id, type, dm_id, pm_id required. contract_end_date required for T&M/ONBOARDING.
**Notes:** Audit log CREATE entry.

---

### GET /api/projects/:id
**Description:** Get full project detail.
**Auth:** CEO, CTO; DM (own portfolio); PM (own portfolio); Finance, HR
**Scope:** Per role
**Response:**
```json
{
  "id", "name", "client": { "id", "name" }, "type", "status", "billing_currency",
  "contract_value",        // Phase 2 — null in Phase 1
  "start_date", "contract_end_date",
  "dm": { "id", "name" }, "pm": { "id", "name" },
  "worklog_enabled", "notes", "created_at"
}
```

---

### PUT /api/projects/:id
**Description:** Update project fields.
**Auth:** CEO, CTO, DM (own portfolio), PM (own portfolio — limited fields)
**Scope:** OWN_PORTFOLIO for DM/PM
**Request Body:** Any subset of project fields.
**Validations:** Status transition rules enforced. contract_end_date required for T&M/ONBOARDING.
**Notes:** Audit log UPDATE per changed field.

---

### PUT /api/projects/:id/status
**Description:** Transition project status.
**Auth:** CEO, CTO, DM (own portfolio)
**Scope:** OWN_PORTFOLIO for DM
**Request Body:** `{ "status": "COMPLETED|ON_HOLD|CANCELLED|ACTIVE" }`
**Validations:** Only valid transitions from FSD §6.4 allowed.
**Notes:** COMPLETED or CANCELLED → triggers auto-release of all ACTIVE assignments. Audit logged.

---

### GET /api/projects/:id/assignments
**Description:** List all assignments for this project (used by Module 05).
**Auth:** CEO, CTO; DM/PM (own portfolio); Finance (VIEW)
**Scope:** OWN_PORTFOLIO for DM/PM
**Response:** Array of assignment objects. Sensitive fields (billing_rate, billability_pct, is_shadow) follow field-level restrictions from `shared/ACCESS-MATRIX.md`.
**Notes:** This endpoint is specified here but implemented as part of Module 05.
