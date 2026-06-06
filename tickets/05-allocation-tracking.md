# Module 05: Allocation Tracking — JIRA Tickets

---

## Story: Create Assignment database table and migration
**Type:** Task
**Phase:** 1
**Module:** 05-allocation-tracking
**Priority:** P0
**Estimate:** S (1-2d)
**Depends On:** 03-project-management (Project table), 04-resource-management (Resource table)
**Labels:** backend, database

### Description
Create the Assignment table with id (UUID PK), project_id (FK to Project), resource_id (FK to Resource), allocation_pct (INTEGER 1-100), billability_pct (INTEGER 0-100), is_shadow (BOOLEAN DEFAULT false), project_designation (STRING 100 NULLABLE), project_expertise (STRING 100 NULLABLE), billing_rate (DECIMAL 10,2 NULLABLE — Phase 2), start_date (DATE), end_date (DATE NULLABLE), status (ENUM: ACTIVE, RELEASED, AUTO_RELEASED DEFAULT ACTIVE), released_at (TIMESTAMP NULLABLE), created_at (TIMESTAMP AUTO), updated_at (TIMESTAMP AUTO). Add indexes on project_id, resource_id, status, and end_date (for auto-release job). A soft unique constraint ensures only one ACTIVE assignment per (resource_id, project_id).

### Acceptance Criteria
- [ ] Assignment table created with all Phase 1 fields per SCHEMA.md
- [ ] ENUM for status: ACTIVE, RELEASED, AUTO_RELEASED
- [ ] Foreign keys to Project (project_id) and Resource (resource_id)
- [ ] billing_rate column present but nullable (Phase 2)
- [ ] Indexes on project_id, resource_id, status, end_date
- [ ] Partial unique index or application-level constraint: one ACTIVE assignment per (resource_id, project_id)
- [ ] UUID v4 for primary key
- [ ] Migration is reversible

---

## Story: Implement Assignment CRUD API endpoints with all 7 FSD validations
**Type:** Feature
**Phase:** 1
**Module:** 05-allocation-tracking
**Priority:** P0
**Estimate:** L (5-10d)
**Depends On:** Assignment database table, access control middleware
**Labels:** backend

### Description
Build POST /api/projects/:projectId/assignments (create), GET /api/projects/:projectId/assignments (list for project), GET /api/assignments/:id (single), PUT /api/assignments/:id (update), and GET /api/resources/:resourceId/assignments (list for resource). All write operations enforce all 7 FSD section 11 assignment validations: billability <= allocation, shadow = zero billability, end after start, no duplicate active assignment on same resource+project, project must be ACTIVE, allocation range 1-100, over-allocation soft warning. Create and update apply designation resolution (project_designation ?? resource.designation). Sensitive fields (billability_pct, is_shadow, billing_rate) return null for unauthorized roles per the access matrix.

### Acceptance Criteria
- [ ] POST /api/projects/:projectId/assignments creates assignment with all required fields
- [ ] GET /api/projects/:projectId/assignments returns array with designation resolution applied
- [ ] GET /api/assignments/:id returns full assignment with resource and project info
- [ ] PUT /api/assignments/:id updates any assignment field, re-applies all validations
- [ ] GET /api/resources/:resourceId/assignments returns active + history with ?status filter
- [ ] Validation 1: "Billability cannot exceed allocation percentage" when billability_pct > allocation_pct
- [ ] Validation 2: "Shadow resources cannot have billability" when is_shadow=true AND billability_pct > 0
- [ ] Validation 3: "End date must be after start date" when end_date <= start_date
- [ ] Validation 4: "Resource already has an active assignment on this project" on duplicate ACTIVE
- [ ] Validation 5: "Cannot create assignment on a non-active project" when project.status != ACTIVE
- [ ] Validation 6: "Allocation must be between 1% and 100%" when < 1 or > 100
- [ ] Validation 7: Over-allocation soft warning returned (not blocking): "This will bring total allocation to {X}%"
- [ ] Designation resolution: effective_designation = project_designation ?? resource.designation
- [ ] Sensitive fields (billability_pct, is_shadow, billing_rate) null for HR and Engineer
- [ ] All changes audit logged (one row per field, with old/new values on update)

---

## Story: Implement access control for Assignment endpoints
**Type:** Feature
**Phase:** 1
**Module:** 05-allocation-tracking
**Priority:** P1
**Estimate:** S (1-2d)
**Depends On:** Assignment CRUD API
**Labels:** backend

### Description
Apply role-based access control to all Assignment endpoints per shared/ACCESS-MATRIX.md. CEO/CTO have EDIT ALL. DM has EDIT OWN_PORTFOLIO (projects where dm_id = self). PM has EDIT OWN_PORTFOLIO (projects where pm_id = self). Finance has VIEW ALL. HR has VIEW ALL but billability_pct, is_shadow, billing_rate return null. Engineer has VIEW SELF_ONLY (only own assignments, no billability/shadow/rate). Scope filtering applied as WHERE clause at DB level.

### Acceptance Criteria
- [ ] CEO, CTO: EDIT ALL on all assignment endpoints
- [ ] DM: EDIT OWN_PORTFOLIO — create/update/view assignments on own projects (dm_id = self)
- [ ] PM: EDIT OWN_PORTFOLIO — create/update/view assignments on own projects (pm_id = self)
- [ ] Finance: VIEW ALL — read-only
- [ ] HR: VIEW ALL — billability_pct, is_shadow, billing_rate return null
- [ ] Engineer: VIEW SELF_ONLY — own assignments only, no sensitive fields
- [ ] Scope filtering applied as WHERE clause at DB level

---

## Story: Implement manual release of assignments
**Type:** Feature
**Phase:** 1
**Module:** 05-allocation-tracking
**Priority:** P1
**Estimate:** S (1-2d)
**Depends On:** Assignment CRUD API
**Labels:** backend

### Description
Build POST /api/assignments/:id/release endpoint that manually releases an ACTIVE assignment. Sets status=RELEASED and released_at=now(). If released before end_date, the audit log captures it as an early release. The resource's total allocation is recalculated after release. Only ACTIVE assignments can be released; already-released assignments return an error. Released assignments cannot be modified — PM must create a new assignment instead.

### Acceptance Criteria
- [ ] POST /api/assignments/:id/release sets status=RELEASED, released_at=now()
- [ ] Only ACTIVE assignments can be released — error if status != ACTIVE
- [ ] Early release (before end_date) logged in AuditLog
- [ ] Total allocation recalculated for the resource after release
- [ ] Released assignments cannot be modified via PUT
- [ ] CEO, CTO, DM (own portfolio), PM (own portfolio) can release
- [ ] Audit logged

---

## Story: Implement auto-release daily scheduled job
**Type:** Feature
**Phase:** 1
**Module:** 05-allocation-tracking
**Priority:** P0
**Estimate:** M (3-5d)
**Depends On:** Assignment CRUD API, manual release
**Labels:** backend, infrastructure

### Description
Build the daily auto-release job (POST /api/jobs/auto-release, also triggered by scheduler at midnight IST). The job finds all assignments with status=ACTIVE, end_date IS NOT NULL, and end_date <= today, then sets status=AUTO_RELEASED and released_at=end_date 23:59:59. For each released assignment, the job creates an alert for PM and DM (ASSIGNMENT_AUTO_RELEASED type). Edge cases: if PM extended end_date before the job runs, the job skips that assignment; released assignments cannot be modified (PM must create new). The job response returns released_count and affected assignment details.

### Acceptance Criteria
- [ ] Job processes all ACTIVE assignments where end_date IS NOT NULL AND end_date <= today
- [ ] Sets status=AUTO_RELEASED, released_at=end_date + 23:59:59
- [ ] Creates ASSIGNMENT_AUTO_RELEASED alert for PM and DM of each released assignment
- [ ] All releases audit logged (entity_type=Assignment, action=UPDATE, field=status)
- [ ] Edge case: assignment with extended end_date (now in future) is skipped
- [ ] Edge case: already-released assignment is not reprocessed
- [ ] Job is idempotent — safe to run multiple times on the same day
- [ ] Returns { released_count, assignments: [{ id, resource_name, project_name }] }
- [ ] Endpoint secured: internal/admin access only

---

## Story: Implement recurring model and shadow flagging business logic
**Type:** Feature
**Phase:** 1
**Module:** 05-allocation-tracking
**Priority:** P1
**Estimate:** S (1-2d)
**Depends On:** Assignment CRUD API
**Labels:** backend

### Description
Ensure the recurring allocation model works correctly: an assignment runs continuously from start_date until end_date (if set) or manual release with no monthly rollover or re-entry. Validate shadow flagging logic: when is_shadow=true, billability_pct must be 0 (error otherwise). Shadow assignments contribute to resource cost but NOT to projected revenue. Shadow flag visible to CEO, CTO, DM, PM, Finance only — hidden from HR and Engineer.

### Acceptance Criteria
- [ ] Assignment runs from start_date until end_date or manual release — no monthly re-entry needed
- [ ] Mid-period revisions to allocation_pct, billability_pct supported without disruption
- [ ] is_shadow=true forces billability_pct=0 — "Shadow resources cannot have billability"
- [ ] Shadow assignments contribute to cost calculations (Module 08 integration)
- [ ] Shadow assignments do NOT contribute to projected revenue
- [ ] Shadow flag visible to CEO, CTO, DM, PM, Finance; null for HR and Engineer
- [ ] Designation resolution: project_designation shown if set, else resource.designation; same for expertise

---

## Story: Build Assignment List UI within Project Detail (Assignments tab)
**Type:** Feature
**Phase:** 1
**Module:** 05-allocation-tracking
**Priority:** P1
**Estimate:** M (3-5d)
**Depends On:** Assignment CRUD API, 03-project-management (Project Detail screen)
**Labels:** frontend

### Description
Create the Assignments tab within /projects/:id showing a table of all assignments for the project. Columns: resource name (link to profile), effective designation (with fallback), effective expertise, allocation %, billability % (hidden from HR/Engineer), shadow badge (hidden from HR/Engineer), billing rate (Phase 2, restricted), start date, end date ("Ongoing" if null), status badge. Include "Add Assignment" button (PM, DM, CEO, CTO), status filter (Active/Released/All), release button on each active assignment row, and an over-allocation banner when any listed resource is over-allocated.

### Acceptance Criteria
- [ ] Assignment table with all specified columns
- [ ] Designation resolution applied: project_designation ?? resource.designation
- [ ] "Add Assignment" button visible to PM, DM, CEO, CTO
- [ ] Status filter: Active / Released / All
- [ ] Release button on each active assignment row with confirmation dialog
- [ ] Over-allocation banner shown when any resource exceeds 100% total allocation
- [ ] billability_pct and is_shadow hidden from HR and Engineer
- [ ] billing_rate column present but shows Phase 2 placeholder
- [ ] End date shows "Ongoing" if null
- [ ] Empty state: "No assignments yet. Add a resource to this project."

---

## Story: Build Assignment Create / Edit form
**Type:** Feature
**Phase:** 1
**Module:** 05-allocation-tracking
**Priority:** P1
**Estimate:** M (3-5d)
**Depends On:** Assignment CRUD API, Assignment List UI
**Labels:** frontend

### Description
Create the assignment create/edit form as a modal or slide-over within the project detail page. Fields: resource dropdown (required, showing current total allocation for each resource), allocation % input (required, 1-100), billability % input (required, 0-100), shadow toggle (when enabled, billability auto-set to 0 and input disabled), project designation override (optional), project expertise override (optional), billing rate input (Phase 2, visible to authorized roles), start date picker (required), end date picker (optional — "Ongoing" if blank). Show over-allocation warning inline when total would exceed 100%. All 7 validation messages displayed inline.

### Acceptance Criteria
- [ ] Resource dropdown with current total allocation shown per resource
- [ ] Allocation % input (1-100, required)
- [ ] Billability % input (0-100, required)
- [ ] Shadow toggle: when on, billability auto-sets to 0 and input is disabled
- [ ] Project designation and expertise override inputs (optional)
- [ ] Billing rate input (Phase 2, restricted visibility)
- [ ] Start date picker (required), end date picker (optional)
- [ ] Over-allocation warning shown inline (non-blocking)
- [ ] All 7 validation messages displayed inline on submit
- [ ] Save calls POST (create) or PUT (edit)
- [ ] Cancel closes form without saving

---

## Story: Build Resource Assignments panel within Resource Profile
**Type:** Feature
**Phase:** 1
**Module:** 05-allocation-tracking
**Priority:** P2
**Estimate:** S (1-2d)
**Depends On:** Assignment CRUD API, 04-resource-management (Resource Profile screen)
**Labels:** frontend

### Description
Add an assignments section/tab to the /resources/:id page showing the resource's active assignments table (project name, effective designation, allocation %, billability %, shadow, start/end date) and total allocation % indicator (highlighted red if > 100%). Below, an expandable assignment history section showing released and auto-released assignments with dates. This view is read-only — assignment edits are done from the project detail page. billability_pct and is_shadow follow access restrictions.

### Acceptance Criteria
- [ ] Active assignments table: project name, effective designation, allocation %, billability %, shadow, start/end date
- [ ] Total allocation % indicator, highlighted red if > 100%
- [ ] Assignment history section: released/auto-released with release dates
- [ ] Read-only — no edit/release actions from this view
- [ ] billability_pct and is_shadow hidden from HR and Engineer
- [ ] Empty state: "No active assignments. This resource is currently on bench."

---

## Story: Implement audit logging for all Assignment write operations
**Type:** Task
**Phase:** 1
**Module:** 05-allocation-tracking
**Priority:** P1
**Estimate:** S (1-2d)
**Depends On:** Assignment CRUD API, manual release, auto-release job
**Labels:** backend

### Description
Wrap all Assignment CREATE, UPDATE, manual release, and auto-release operations in audit-aware functions. CREATE: one AuditLog row per field. UPDATE: one row per changed field with old_value and new_value. Release (manual or auto): log status change and released_at, plus early release indicator if applicable. All entries capture entity_type=Assignment, entity_id, action, field_name, old_value, new_value, changed_by, changed_at. Auto-release uses system/job user as changed_by.

### Acceptance Criteria
- [ ] CREATE: one AuditLog row per field with entity_type=Assignment, action=CREATE
- [ ] UPDATE: one AuditLog row per changed field with old_value and new_value
- [ ] Manual release: AuditLog for status change (ACTIVE->RELEASED) and released_at
- [ ] Auto-release: AuditLog for status change (ACTIVE->AUTO_RELEASED) and released_at, changed_by=system
- [ ] Early release (before end_date) explicitly noted in audit
- [ ] old_value and new_value stored as JSON-serialized strings

---

## Story: Write tests for Assignment validations, state transitions, auto-release job, and access control
**Type:** Task
**Phase:** 1
**Module:** 05-allocation-tracking
**Priority:** P1
**Estimate:** L (5-10d)
**Depends On:** All Assignment API endpoints, auto-release job
**Labels:** backend

### Description
Write comprehensive tests covering: all 7 FSD validation rules (each rule triggered and error message verified), happy path CRUD, manual release (ACTIVE->RELEASED, already-released error, early release logging), auto-release job (normal release, extended end_date skip, already-released skip, idempotency), project completion cascade (all assignments auto-released), designation resolution, shadow flagging (is_shadow=true forces billability=0), recurring model (no re-entry needed), access control per role, sensitive field null enforcement, and over-allocation warning generation.

### Acceptance Criteria
- [ ] All 7 validation rules: each triggered with correct error message
- [ ] CRUD happy paths pass
- [ ] Manual release: ACTIVE->RELEASED succeeds; non-ACTIVE returns error; early release logged
- [ ] Auto-release job: processes eligible assignments; skips extended; skips already-released; idempotent
- [ ] Project completion cascade: all ACTIVE assignments auto-released
- [ ] Designation resolution: project_designation used when set, resource.designation as fallback
- [ ] Shadow: is_shadow=true with billability>0 returns error; billability=0 succeeds
- [ ] Recurring model: assignment persists across months without re-entry
- [ ] Access control: CEO/CTO full access; DM/PM own portfolio; Finance view-only; HR view-only (no sensitive); Engineer self-only
- [ ] Sensitive fields (billability_pct, is_shadow, billing_rate) null for HR and Engineer
- [ ] Over-allocation warning returned when total > 100%
- [ ] Audit log entries verified for all write operations
