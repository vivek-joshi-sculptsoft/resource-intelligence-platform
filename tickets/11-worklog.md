# Module 11: Worklog -- JIRA Tickets

---

## Story: Create Worklog database table
**Type:** Task
**Phase:** 1
**Module:** 11-worklog
**Priority:** P0
**Estimate:** S (1-2d)
**Depends On:** 04-resource-management, 03-project-management, 05-allocation-tracking
**Labels:** backend, database

### Description
Create the database migration for the Worklog table per SCHEMA.md. The table tracks daily hour entries per resource per project. Hours are stored as DECIMAL(4,1) supporting half-hour increments. A unique constraint on (resource_id, project_id, log_date) prevents duplicate entries. No foreign key or trigger relationship to any financial entity -- worklog is decoupled by design.

### Acceptance Criteria
- [ ] Worklog table created: id (UUID PK), resource_id (FK -> Resource), project_id (FK -> Project), log_date (DATE, not future), hours (DECIMAL(4,1)), note (TEXT NULLABLE), created_at (TIMESTAMP AUTO)
- [ ] Unique constraint on (resource_id, project_id, log_date)
- [ ] DB indexes on: resource_id, project_id, log_date
- [ ] No FK or trigger to Invoice, Assignment billability, or any financial table
- [ ] Migration is idempotent

---

## Story: Build worklog CRUD API
**Type:** Feature
**Phase:** 1
**Module:** 11-worklog
**Priority:** P0
**Estimate:** M (3-5d)
**Depends On:** 11-worklog (DB table)
**Labels:** backend

### Description
Implement worklog CRUD endpoints: `POST /api/worklogs` (create), `PUT /api/worklogs/:id` (update hours/note), `DELETE /api/worklogs/:id` (delete own entry), `GET /api/worklogs/my` (own entries). All operations are SELF_ONLY -- employees can only manage their own worklog entries. The resource_id is derived from the authenticated user, not passed in the request body.

### Acceptance Criteria
- [ ] POST creates worklog: project_id (required), log_date (required), hours (required, 0.5-24.0 in 0.5 increments), note (optional)
- [ ] resource_id automatically set from authenticated user's linked resource
- [ ] PUT updates hours and note only (cannot change project_id or log_date)
- [ ] DELETE removes own entry; no side effects on any other entity
- [ ] GET /api/worklogs/my returns paginated own entries
- [ ] GET supports filters: ?project_id, ?start_date, ?end_date
- [ ] All operations are SELF_ONLY (403 if attempting to modify another user's entry)
- [ ] Unit tests for CRUD operations

---

## Story: Implement worklog validation rules
**Type:** Feature
**Phase:** 1
**Module:** 11-worklog
**Priority:** P0
**Estimate:** M (3-5d)
**Depends On:** 11-worklog (CRUD API), 03-project-management, 05-allocation-tracking
**Labels:** backend

### Description
Implement all 5 FSD Section 11 worklog validations. These are enforced on POST (create) and relevant ones on PUT (update). The backfill rule allows logging for past dates if the resource had an ACTIVE assignment on that date. Total hours > 24 across projects on same day triggers a warning (not blocking).

### Acceptance Criteria
- [ ] Validation 1: "Worklog is not enabled for this project" -- rejects if project.worklog_enabled = false
- [ ] Validation 2: "You must have an active assignment to log hours" -- rejects if no ACTIVE assignment for resource on project
- [ ] Validation 3: "Cannot log hours for future dates" -- rejects if log_date > today
- [ ] Validation 4: "Hours must be between 0.5 and 24" -- rejects if hours < 0.5 or > 24
- [ ] Validation 5: "Entry already exists for this date. Edit the existing entry." -- rejects duplicate (resource_id, project_id, log_date)
- [ ] Backfill: allows past dates if assignment was ACTIVE on that date (check start_date/end_date range)
- [ ] Backfill: rejects past dates if no ACTIVE assignment existed on that date
- [ ] Warning (non-blocking): total hours across all projects > 24 on same day
- [ ] Hours must be in 0.5 increments (0.5, 1.0, 1.5, ... 24.0)
- [ ] Unit tests for each validation rule including edge cases

---

## Story: Build manager worklog viewing APIs
**Type:** Feature
**Phase:** 1
**Module:** 11-worklog
**Priority:** P1
**Estimate:** M (3-5d)
**Depends On:** 11-worklog (CRUD API)
**Labels:** backend

### Description
Implement manager-facing worklog viewing endpoints: `GET /api/projects/:projectId/worklogs` (all worklogs for a project) and `GET /api/resources/:resourceId/worklogs` (worklogs for a specific resource). Scoped by role: CEO/CTO view all, DM/PM view own portfolio, resource user views own (SELF_ONLY). Support date range and resource/project filters.

### Acceptance Criteria
- [ ] GET /api/projects/:projectId/worklogs returns paginated worklogs for a project
- [ ] Supports filters: ?resource_id, ?start_date, ?end_date
- [ ] GET /api/resources/:resourceId/worklogs returns paginated worklogs for a resource
- [ ] CEO, CTO see all worklogs (ALL scope)
- [ ] DM sees worklogs for projects where dm_id = current user (OWN_PORTFOLIO)
- [ ] PM sees worklogs for projects where pm_id = current user (OWN_PORTFOLIO)
- [ ] Resource user sees own worklogs only (SELF_ONLY)
- [ ] Each entry shows: resource name, log_date, hours, note
- [ ] Unit tests for scope filtering per role

---

## Story: Build worklog entry UI for employees
**Type:** Feature
**Phase:** 1
**Module:** 11-worklog
**Priority:** P1
**Estimate:** L (5-10d)
**Depends On:** 11-worklog (CRUD API, validations)
**Labels:** frontend

### Description
Build the worklog entry interface at `/my-assignments` within the worklog section. Shows a project selector (pre-populated from active assignments where worklog_enabled = true), date picker (defaults to today, no future dates), hours input (0.5-24.0 in 0.5 increments), optional note textarea, and submit button. Display recent entries (last 30 days) with edit/delete capabilities. All 5 validation messages must be shown client-side.

### Acceptance Criteria
- [ ] Project selector shows only active assignments where worklog_enabled = true
- [ ] Date picker defaults to today; cannot select future dates
- [ ] Hours input supports 0.5-24.0 in 0.5 increments (spinner or dropdown)
- [ ] Note textarea (optional)
- [ ] "Log Hours" / "Save" button submits entry
- [ ] Recent entries table shows last 30 days: date, project, hours, note, edit button
- [ ] Edit opens inline or modal form for hours and note
- [ ] Delete with confirmation dialog
- [ ] Client-side validations with exact error messages from FSD Section 11
- [ ] Empty state: "No projects with worklog enabled. Ask your manager to enable worklog for your project."
- [ ] Only logs for own resource; cannot see other resources' worklogs
- [ ] Loading and error states handled

---

## Story: Build worklog tab UI in project detail (manager view)
**Type:** Feature
**Phase:** 1
**Module:** 11-worklog
**Priority:** P1
**Estimate:** M (3-5d)
**Depends On:** 11-worklog (manager viewing APIs), 03-project-management (project detail page)
**Labels:** frontend

### Description
Add a "Worklogs" tab to the project detail view, visible only when `worklog_enabled = true`. Displays a table of worklog entries for the project with date range filter and resource filter dropdown. Accessible to CEO, CTO, DM (own portfolio), PM (own portfolio). Engineers view their own entries via `/my-assignments`, not this tab.

### Acceptance Criteria
- [ ] Worklogs tab shown only when project.worklog_enabled = true
- [ ] Date range filter (start/end date pickers)
- [ ] Resource filter dropdown (all resources on this project)
- [ ] Worklog table: Date, Resource Name, Hours, Note (truncated with expand)
- [ ] Accessible to CEO, CTO, DM (own portfolio), PM (own portfolio)
- [ ] Engineers do not see this tab
- [ ] Empty state: "No worklog entries for this period."

---

## Story: Build personal worklog history page
**Type:** Feature
**Phase:** 1
**Module:** 11-worklog
**Priority:** P2
**Estimate:** S (1-2d)
**Depends On:** 11-worklog (CRUD API)
**Labels:** frontend

### Description
Build the `/my-worklogs` page for any logged-in user with a resource_id. Shows a full history table with date and project filters, edit/delete capabilities per entry. This is a read/manage view separate from the entry form.

### Acceptance Criteria
- [ ] Date range filter
- [ ] Project filter dropdown
- [ ] Worklog table: date, project, hours, note, edit/delete buttons
- [ ] Edit entry via inline or modal form
- [ ] Delete entry with confirmation dialog
- [ ] Empty state: "No worklog entries found."
- [ ] Accessible to any logged-in user with a resource_id

---

## Story: Implement worklog access control
**Type:** Task
**Phase:** 1
**Module:** 11-worklog
**Priority:** P0
**Estimate:** S (1-2d)
**Depends On:** 01-auth-and-roles, 11-worklog (all APIs)
**Labels:** backend

### Description
Enforce access control across all worklog endpoints per ACCESS-MATRIX.md. Engineer has EDIT SELF_ONLY for worklogs (create/edit/delete own entries). CEO/CTO have VIEW ALL. DM/PM have VIEW OWN_PORTFOLIO. Finance and HR have NONE for worklogs. Scope filtering via WHERE clauses at the database level.

### Acceptance Criteria
- [ ] Engineer: EDIT own worklogs (create, edit, delete own entries)
- [ ] CEO, CTO: VIEW ALL worklogs across all projects
- [ ] DM: VIEW worklogs for projects where dm_id = current user
- [ ] PM: VIEW worklogs for projects where pm_id = current user
- [ ] Finance: NONE -- no access to worklog endpoints (403)
- [ ] HR: NONE -- no access to worklog endpoints (403)
- [ ] Scope filtering applied at DB query level
- [ ] Access control tests for all 7 roles
