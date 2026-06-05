# Module 11: Worklog — API Endpoints

## Endpoints

### GET /api/worklogs/my
**Description:** Get current user's own worklog entries.
**Auth:** Any authenticated user with a resource_id (Engineer, PM, DM, etc.)
**Scope:** SELF_ONLY
**Response:** Paginated array: `[{ id, project: { id, name }, log_date, hours, note, created_at }]`
**Notes:** `?project_id=<uuid>&start_date=<date>&end_date=<date>` filters.

---

### POST /api/worklogs
**Description:** Create a new worklog entry.
**Auth:** Any user with a linked resource_id
**Scope:** SELF_ONLY
**Request Body:**
```json
{
  "project_id": "uuid*",
  "log_date": "date*",
  "hours": "decimal* 0.5-24.0",
  "note": "string"
}
```
**Validations:** All 5 FSD §11 Worklog validations. Backfill check: resource must have had ACTIVE assignment on log_date.
**Notes:** No audit log required (informational only, no financial impact).

---

### PUT /api/worklogs/:id
**Description:** Update own worklog entry.
**Auth:** Owner of the worklog entry only
**Scope:** SELF_ONLY
**Request Body:** `{ "hours": decimal, "note": string }`
**Validations:** Hours range (0.5–24.0). Cannot change project_id or log_date.

---

### DELETE /api/worklogs/:id
**Description:** Delete own worklog entry.
**Auth:** Owner of the worklog entry only
**Scope:** SELF_ONLY
**Response:** `{ "success": true }`
**Notes:** No side effects on any financial or allocation data.

---

### GET /api/projects/:projectId/worklogs
**Description:** View all worklogs for a project (manager view).
**Auth:** CEO, CTO (ALL); DM (own portfolio); PM (own portfolio). Reference `shared/ACCESS-MATRIX.md` (`worklogs`).
**Scope:** OWN_PORTFOLIO for DM/PM
**Response:** Paginated: `[{ id, resource: { id, name }, log_date, hours, note }]`
**Notes:** `?resource_id=<uuid>&start_date=<date>&end_date=<date>`

---

### GET /api/resources/:resourceId/worklogs
**Description:** View worklogs for a specific resource.
**Auth:** CEO, CTO; DM/PM (own portfolio); the resource themselves (SELF_ONLY)
**Scope:** Per role
**Response:** Paginated: `[{ id, project: { id, name }, log_date, hours, note }]`
