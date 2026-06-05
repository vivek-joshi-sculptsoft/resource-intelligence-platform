# Module 04: Resource Management — API Endpoints

## Endpoints

### GET /api/resources
**Description:** List resources with filters and total allocation.
**Auth:** CEO, CTO, DM, PM, Finance, HR (VIEW/EDIT per matrix); Engineer (SELF_ONLY). Reference `shared/ACCESS-MATRIX.md`.
**Scope:** ALL for most roles; SELF_ONLY for Engineer
**Response:** Paginated. Each item: `{ id, employee_id, name, designation, technical_expertise, total_allocation_pct, is_active, tags }`
**Notes:** `?page=1&limit=20&status=ACTIVE&designation=<val>&expertise=<val>&tag=<val>&availability=bench|partial|full&search=<name>`
`loaded_cost_monthly` returned as `null` for roles without access.

---

### POST /api/resources
**Description:** Create a new resource.
**Auth:** CEO, CTO, HR (EDIT on resource_profiles)
**Scope:** ALL
**Request Body:**
```json
{
  "employee_id": "string*",
  "name": "string*",
  "designation": "string*",
  "technical_expertise": "string",
  "date_of_joining": "date",
  "reporting_manager_id": "uuid|null",
  "tags": ["string"]
}
```
**Validations:** name, employee_id, designation required. employee_id unique.
**Notes:** Audit log CREATE entry.

---

### GET /api/resources/:id
**Description:** Get full resource profile.
**Auth:** CEO, CTO, DM, PM, Finance, HR; Engineer (own id only)
**Scope:** SELF_ONLY for Engineer
**Response:**
```json
{
  "id", "employee_id", "name", "designation", "technical_expertise",
  "date_of_joining", "reporting_manager": { "id", "name" },
  "loaded_cost_monthly": null,   // null unless CEO/CTO/Finance
  "is_active", "tags": ["string"],
  "active_assignments": [ { assignment fields with project name } ],
  "total_allocation_pct": int
}
```
**Notes:** `loaded_cost_monthly` — null for unauthorized roles (not omitted).

---

### PUT /api/resources/:id
**Description:** Update resource profile fields.
**Auth:** CEO, CTO, HR (all fields except loaded_cost_monthly); Finance (loaded_cost_monthly only)
**Scope:** ALL
**Request Body:** Any subset of resource fields.
**Validations:** employee_id unique if changed. No self-referencing reporting manager.
**Notes:** Audit log UPDATE per changed field. `loaded_cost_monthly` changes audit logged with old/new values.

---

### DELETE /api/resources/:id
**Description:** Soft-deactivate a resource (`is_active = false`).
**Auth:** CEO, CTO, HR
**Scope:** ALL
**Validations:** Blocks if resource is assigned as DM or PM on an ACTIVE project. Cascades: release all ACTIVE assignments.
**Notes:** Audit logged.

---

### POST /api/resources/:id/tags
**Description:** Add a tag to a resource.
**Auth:** CEO, CTO, HR, DM (own portfolio)
**Request Body:** `{ "tag": "string*" }`
**Response:** Updated tags array.
**Validations:** Tag max 100 chars.

---

### DELETE /api/resources/:id/tags/:tag
**Description:** Remove a tag from a resource.
**Auth:** CEO, CTO, HR, DM (own portfolio)
**Response:** Updated tags array.

---

### GET /api/resources/:id/assignments
**Description:** Get all assignments for a resource (active + history).
**Auth:** CEO, CTO, DM, PM (own portfolio), HR; Engineer (own only)
**Scope:** SELF_ONLY for Engineer; OWN_PORTFOLIO for DM/PM
**Response:** Array of assignments with project name, status, dates.
**Notes:** Sensitive fields (billing_rate, billability_pct, is_shadow) follow field restrictions.
