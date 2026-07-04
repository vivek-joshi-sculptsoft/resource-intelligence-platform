# Module 11: Worklog — API Endpoints

## Endpoints

### GET /api/worklogs
**Description:** View worklogs company-wide (or within own portfolio) across all projects — backs the Worklogs page (`/worklogs`). Documented here as it predates this file; was implemented alongside `GET /api/projects/:projectId/worklogs` but not previously written up.
**Auth:** CEO, CTO, FINANCE, HR (ALL); DM/PM (own portfolio); ENGINEER (SELF_ONLY — own entries only). Reference `shared/ACCESS-MATRIX.md` (`worklogs`).
**Scope:** Per role, per `shared/ACCESS-MATRIX.md`
**Response:** Paginated: `[{ id, resource: { id, name }, project: { id, name }, log_date, hours, note }]`
**Notes:** `?client_id=<uuid>&project_id=<uuid>&resource_id=<uuid>&start_date=<date>&end_date=<date>` filters. `client_id` joins through Project.client_id to filter worklogs belonging to projects under that client.

---

### GET /api/worklogs/export
**Description:** Export worklogs company-wide (or within own portfolio) to Excel, using the same filters as `GET /api/worklogs`.
**Auth:** Same as `GET /api/worklogs`.
**Scope:** Same as `GET /api/worklogs`.
**Response:** `.xlsx` file stream (`Content-Type: application/vnd.openxmlformats-officedocument.spreadsheetml.sheet`) — all matching rows, no pagination.
**Notes:** `?client_id=<uuid>&project_id=<uuid>&resource_id=<uuid>&start_date=<date>&end_date=<date>` filters — identical params to `GET /api/worklogs`. Columns: Date, Resource, Project, Hours, Note.

---

### GET /api/worklogs/my
**Description:** Get current user's own worklog entries.
**Auth:** Any authenticated user with a resource_id (Engineer, PM, DM, etc.)
**Scope:** SELF_ONLY
**Response:** Paginated array: `[{ id, project: { id, name }, log_date, hours, note, created_at }]`
**Notes:** `?project_id=<uuid>&start_date=<date>&end_date=<date>` filters.

---

### GET /api/worklogs/my/export
**Description:** Export the current user's own worklog entries to Excel, using the same filters as `GET /api/worklogs/my`.
**Auth:** Any authenticated user with a resource_id.
**Scope:** SELF_ONLY
**Response:** `.xlsx` file stream — all matching rows, no pagination.
**Notes:** `?project_id=<uuid>&start_date=<date>&end_date=<date>` filters. Columns: Date, Project, Hours, Note.

---

### POST /api/worklogs
**Description:** Create a new worklog entry.
**Auth:** Requires EDIT on `worklogs` (CEO, CTO, DM, PM, ENGINEER) and a linked resource_id. FINANCE/HR have VIEW-only and get 403.
**Scope:** SELF_ONLY (always writes the caller's own resource_id — scope on the RolePermission row governs viewing, not the write target)
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
**Auth:** Requires EDIT on `worklogs` and ownership of the entry. FINANCE/HR get 403.
**Scope:** SELF_ONLY
**Request Body:** `{ "hours": decimal, "note": string }`
**Validations:** Hours range (0.5–24.0). Cannot change project_id or log_date.

---

### DELETE /api/worklogs/:id
**Description:** Delete own worklog entry.
**Auth:** Requires EDIT on `worklogs` and ownership of the entry. FINANCE/HR get 403.
**Scope:** SELF_ONLY
**Response:** `{ "success": true }`
**Notes:** No side effects on any financial or allocation data.

---

### GET /api/projects/:projectId/worklogs
**Description:** View all worklogs for a project (manager view).
**Auth:** CEO, CTO, FINANCE, HR (ALL); DM (own portfolio); PM (own portfolio). Reference `shared/ACCESS-MATRIX.md` (`worklogs`).
**Scope:** OWN_PORTFOLIO for DM/PM
**Response:** Paginated: `[{ id, resource: { id, name }, log_date, hours, note }]`
**Notes:** `?resource_id=<uuid>&start_date=<date>&end_date=<date>`

---

### GET /api/projects/:projectId/worklogs/export
**Description:** Export all worklogs for a project to Excel, using the same filters as `GET /api/projects/:projectId/worklogs`.
**Auth:** Same as `GET /api/projects/:projectId/worklogs`.
**Scope:** OWN_PORTFOLIO for DM/PM
**Response:** `.xlsx` file stream — all matching rows, no pagination.
**Notes:** `?resource_id=<uuid>&start_date=<date>&end_date=<date>` filters. Columns: Date, Resource, Hours, Note.

---

### GET /api/resources/:resourceId/worklogs
**Description:** View worklogs for a specific resource.
**Auth:** CEO, CTO, FINANCE, HR (ALL); DM/PM (own portfolio); the resource themselves (SELF_ONLY)
**Scope:** Per role
**Response:** Paginated: `[{ id, project: { id, name }, log_date, hours, note }]`
