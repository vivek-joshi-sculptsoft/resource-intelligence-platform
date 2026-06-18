# Module 05: Allocation Tracking — API Endpoints

## Endpoints

### GET /api/projects/:projectId/assignments
**Description:** List all assignments for a project.
**Auth:** CEO, CTO; DM (own portfolio); PM (own portfolio); Finance (VIEW). Reference `shared/ACCESS-MATRIX.md`.
**Scope:** OWN_PORTFOLIO for DM/PM
**Response:** Array of:
```json
{
  "id", "resource": { "id", "name", "designation", "technical_expertise" },
  "effective_designation",   // project_designation ?? resource.designation
  "effective_expertise",     // project_expertise ?? resource.technical_expertise
  "allocation_pct", "billability_pct",  // billability_pct null for HR/Engineer
  "is_shadow",              // null for HR/Engineer
  "billing_rate",           // null unless CEO/CTO/Finance/DM(configurable); value is in project billing_currency
  "billing_currency",       // project's ISO 4217 currency code (e.g. "INR", "USD"); always present
  "start_date", "end_date", "status", "released_at"
}
```
**Notes:** `?status=ACTIVE` to filter. Designation resolution applied.

---

### POST /api/projects/:projectId/assignments
**Description:** Create a new assignment.
**Auth:** CEO, CTO, DM (own portfolio), PM (own portfolio — EDIT on allocation)
**Scope:** OWN_PORTFOLIO for DM/PM
**Request Body:**
```json
{
  "resource_id": "uuid*",
  "allocation_pct": "integer* 1-100",
  "billability_pct": "integer* 0-100",
  "is_shadow": "boolean default false",
  "project_designation": "string",
  "project_expertise": "string",
  "billing_rate": "decimal (Phase 2 only)",
  "start_date": "date*",
  "end_date": "date"
}
```
**Validations:** All 7 FSD §11 assignment validations. Over-allocation is a soft warning (not blocking).
**Notes:** Audit log CREATE (one row per field). Returns warning array if over-allocation.

---

### GET /api/assignments/:id
**Description:** Get a single assignment.
**Auth:** CEO, CTO; DM/PM (own portfolio); Engineer (own assignment only)
**Scope:** Per role
**Response:** Full assignment object with resource and project info. Project sub-object includes `billing_currency`.

---

### PUT /api/assignments/:id
**Description:** Update assignment fields.
**Auth:** CEO, CTO, DM (own portfolio), PM (own portfolio)
**Scope:** OWN_PORTFOLIO for DM/PM
**Request Body:** Any subset of: `allocation_pct, billability_pct, is_shadow, project_designation, project_expertise, billing_rate (Phase 2), start_date, end_date`
**Validations:** All 7 validations re-applied.
**Notes:** Audit log UPDATE (one row per changed field, with old_value and new_value).

---

### POST /api/assignments/:id/release
**Description:** Manually release an active assignment.
**Auth:** CEO, CTO, DM (own portfolio), PM (own portfolio)
**Scope:** OWN_PORTFOLIO for DM/PM
**Response:** Updated assignment with `status = RELEASED`, `released_at = now()`.
**Validations:** Assignment must be ACTIVE.
**Notes:** Logs early release if before end_date. Audit logged.

---

### POST /api/jobs/auto-release
**Description:** Trigger the auto-release daily job (also runs on schedule — midnight IST).
**Auth:** Internal/admin only (or scheduled job token)
**Scope:** ALL
**Response:** `{ "released_count": int, "assignments": [{ "id", "resource_name", "project_name" }] }`
**Notes:** Processes all `ACTIVE` assignments with `end_date <= today`. Sets `AUTO_RELEASED`, fires alerts, audit logs each release.

---

### GET /api/resources/:resourceId/assignments
**Description:** List all assignments for a specific resource (active + history).
**Auth:** CEO, CTO, DM, PM (own portfolio), HR; Engineer (own resource only)
**Scope:** SELF_ONLY for Engineer
**Response:** Array of assignments with project info. Sensitive fields follow access matrix.
**Notes:** `?status=ACTIVE` to filter to current assignments.
