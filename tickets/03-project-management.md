# Module 03: Project Management — JIRA Tickets

---

## Story: Create Project database table and migration
**Type:** Task
**Phase:** 1
**Module:** 03-project-management
**Priority:** P0
**Estimate:** S (1-2d)
**Depends On:** 01-auth-and-roles (database schema), 02-client-management (Client table)
**Labels:** backend, database

### Description
Create the Project table with id (UUID PK), name (STRING 255), client_id (FK to Client), type (ENUM: FIXED_PRICE, TIME_AND_MATERIAL, CLIENT_ONBOARDING), billing_currency (STRING 3 DEFAULT INR), contract_value (DECIMAL 15,2 — Phase 2, nullable), start_date (DATE), contract_end_date (DATE), dm_id (FK to Resource), pm_id (FK to Resource), worklog_enabled (BOOLEAN DEFAULT false), notes (TEXT), status (ENUM: ACTIVE, COMPLETED, ON_HOLD, CANCELLED DEFAULT ACTIVE), and created_at (TIMESTAMP AUTO). Add indexes on client_id, dm_id, pm_id, and status. Migration must be reversible.

### Acceptance Criteria
- [ ] Project table created with all Phase 1 fields per SCHEMA.md
- [ ] ENUM types enforced for type and status fields
- [ ] Foreign keys to Client (client_id), Resource (dm_id, pm_id) created
- [ ] contract_value column present but nullable (Phase 2)
- [ ] Indexes on client_id, dm_id, pm_id, status
- [ ] UUID v4 for primary key
- [ ] Migration is reversible

---

## Story: Implement Project CRUD API endpoints
**Type:** Feature
**Phase:** 1
**Module:** 03-project-management
**Priority:** P1
**Estimate:** M (3-5d)
**Depends On:** Project database table, access control middleware
**Labels:** backend

### Description
Build POST /api/projects (create), GET /api/projects (paginated list with filters), GET /api/projects/:id (detail), and PUT /api/projects/:id (update). Create requires name, client_id, type, dm_id, pm_id. contract_end_date is required for T&M and CLIENT_ONBOARDING types. The list endpoint supports filtering by client_id, type, status, dm_id and search by project name. DM/PM scope filtering is applied at the DB level. The detail endpoint returns nested client and DM/PM resource info.

### Acceptance Criteria
- [ ] POST /api/projects creates project with all required fields; status defaults to ACTIVE
- [ ] GET /api/projects returns paginated list with filters: ?client_id, ?type, ?status, ?dm_id, ?search, ?page, ?limit
- [ ] GET /api/projects/:id returns full project with nested client {id, name} and dm/pm {id, name}
- [ ] PUT /api/projects/:id updates any project field
- [ ] Validation: "Project name is required" when name blank
- [ ] Validation: "Project must belong to a client" when client_id null
- [ ] Validation: "Project type is required" when type not set
- [ ] Validation: "A Delivery Manager must be assigned" when dm_id null
- [ ] Validation: "A Project Manager must be assigned" when pm_id null
- [ ] Validation: "Contract end date is required for this project type" when T&M or ONBOARDING missing contract_end_date
- [ ] All changes audit logged (one row per changed field)

---

## Story: Implement access control for Project endpoints
**Type:** Feature
**Phase:** 1
**Module:** 03-project-management
**Priority:** P1
**Estimate:** S (1-2d)
**Depends On:** Project CRUD API
**Labels:** backend

### Description
Apply role-based access control to all Project endpoints per shared/ACCESS-MATRIX.md. CEO/CTO have EDIT ALL. DM has EDIT OWN_PORTFOLIO (dm_id = current user). PM has EDIT OWN_PORTFOLIO (pm_id = current user). Finance and HR have VIEW ALL. Engineer has NONE (403). DM on create can only set dm_id to themselves; CEO/CTO can assign any DM. Scope filtering is applied as a WHERE clause at the DB level.

### Acceptance Criteria
- [ ] CEO, CTO: EDIT ALL on all project endpoints
- [ ] DM: EDIT OWN_PORTFOLIO — create/update/view only projects where dm_id = self
- [ ] PM: EDIT OWN_PORTFOLIO — update/view only projects where pm_id = self (limited fields)
- [ ] Finance, HR: VIEW ALL — read-only access
- [ ] Engineer: NONE — returns 403
- [ ] DM on create: dm_id auto-set to self (cannot assign another DM)
- [ ] CEO/CTO on create: can assign any DM

---

## Story: Implement project status lifecycle and state machine transitions
**Type:** Feature
**Phase:** 1
**Module:** 03-project-management
**Priority:** P0
**Estimate:** M (3-5d)
**Depends On:** Project CRUD API
**Labels:** backend

### Description
Build PUT /api/projects/:id/status endpoint that enforces the project status state machine from FSD section 6.4. Valid transitions: ACTIVE to COMPLETED, ACTIVE to ON_HOLD, ON_HOLD to ACTIVE, ACTIVE to CANCELLED. Invalid transitions return "Invalid status transition". When a project transitions to COMPLETED or CANCELLED, all ACTIVE assignments on that project are immediately auto-released (status=AUTO_RELEASED, released_at=now()). New assignments cannot be created on COMPLETED or CANCELLED projects. All status changes are audit logged.

### Acceptance Criteria
- [ ] PUT /api/projects/:id/status accepts { status: "COMPLETED|ON_HOLD|CANCELLED|ACTIVE" }
- [ ] Valid transitions enforced: ACTIVE->COMPLETED, ACTIVE<->ON_HOLD, ACTIVE->CANCELLED
- [ ] Invalid transitions return "Invalid status transition"
- [ ] COMPLETED or CANCELLED triggers auto-release of all ACTIVE assignments on the project
- [ ] Auto-released assignments get status=AUTO_RELEASED, released_at=now()
- [ ] Cannot create new assignments on COMPLETED or CANCELLED projects — "Cannot create assignment on a non-active project"
- [ ] Status changes audit logged
- [ ] Only CEO, CTO, DM (own portfolio) can transition status

---

## Story: Build Project List screen with filters
**Type:** Feature
**Phase:** 1
**Module:** 03-project-management
**Priority:** P1
**Estimate:** M (3-5d)
**Depends On:** Project CRUD API, access control
**Labels:** frontend

### Description
Create the /projects page with a full-width table displaying project name (link), client name, type badge (FP/T&M/Onboarding), status badge (colored), DM name, PM name, start date, and contract end date (highlighted if expiring soon). Include filter bar with status dropdown, type dropdown, client dropdown, DM dropdown, and search by project name. "Add Project" button visible to CEO, CTO, DM only. Table supports column sorting. DM sees only own-portfolio projects; PM sees only own projects.

### Acceptance Criteria
- [ ] Project table with columns: Name (link), Client, Type (badge), Status (badge), DM, PM, Start Date, Contract End
- [ ] Filter bar: status, type, client, DM dropdowns
- [ ] Search by project name
- [ ] "Add Project" button visible to CEO, CTO, DM only
- [ ] Column sorting on name, start_date, status
- [ ] Contract end date highlighted if expiring within 30 days
- [ ] DM sees only own-portfolio projects; PM sees only own projects
- [ ] Empty state: "No projects found. Try adjusting your filters or create a new project."
- [ ] Pagination controls

---

## Story: Build Project Detail screen with tabs and status transition buttons
**Type:** Feature
**Phase:** 1
**Module:** 03-project-management
**Priority:** P1
**Estimate:** L (5-10d)
**Depends On:** Project CRUD API, status lifecycle API, 05-allocation-tracking
**Labels:** frontend

### Description
Create the /projects/:id page with a header section (name, client link, type badge, status badge, billing currency, DM, PM, edit button) and status transition buttons ("Complete", "Put on Hold", "Cancel", "Reactivate" — context-dependent, CEO/CTO/DM only). Below the header, tab navigation: Assignments (Phase 1, data from Module 05), Non-Human Costs (Phase 2 placeholder), Milestones (FP only, Phase 2 placeholder), Invoices (Phase 2 placeholder), Financials (restricted, Phase 2 placeholder), Worklogs (shown only if worklog_enabled=true). Status transition triggers a confirmation dialog then calls PUT /api/projects/:id/status.

### Acceptance Criteria
- [ ] Project header with all project fields, edit button (CEO/CTO/DM/PM)
- [ ] Status transition buttons shown contextually based on current status and allowed transitions
- [ ] Status transition buttons visible to CEO, CTO, DM only
- [ ] Confirmation dialog before status transition
- [ ] Tab navigation: Assignments, Non-Human Costs (Phase 2), Milestones (Phase 2), Invoices (Phase 2), Financials (Phase 2), Worklogs
- [ ] Assignments tab shows data from Module 05
- [ ] Phase 2 tabs display "Coming soon" placeholder
- [ ] Worklogs tab shown only when worklog_enabled=true
- [ ] Financials tab visible to CEO, CTO, Finance only
- [ ] Assignments empty state: "No resources assigned yet. Add an assignment to get started."

---

## Story: Build Project Create / Edit form with conditional fields
**Type:** Feature
**Phase:** 1
**Module:** 03-project-management
**Priority:** P1
**Estimate:** M (3-5d)
**Depends On:** Project CRUD API, Client list API, Resource list API
**Labels:** frontend

### Description
Create the /projects/new and /projects/:id/edit forms. Fields: name (required), client dropdown from active clients (required), type radio/dropdown (required: Fixed Price/Time & Material/Client Onboarding), billing currency dropdown (default INR), start date picker, contract end date picker (required if T&M or Onboarding — conditionally shown/required), DM dropdown from active resources (required), PM dropdown from active resources (required), worklog enabled toggle, notes textarea. DM creating a project can only assign themselves as DM. Save calls POST or PUT; redirect to project detail on success.

### Acceptance Criteria
- [ ] Name input (required)
- [ ] Client dropdown populated from active clients (required)
- [ ] Type selection: Fixed Price / Time & Material / Client Onboarding (required)
- [ ] Billing currency dropdown (default INR)
- [ ] Start date picker
- [ ] Contract end date picker — required and visually highlighted when T&M or Onboarding selected
- [ ] DM dropdown from active resources (required); DM role auto-selects self
- [ ] PM dropdown from active resources (required)
- [ ] Worklog enabled toggle (default off)
- [ ] Notes textarea
- [ ] Save calls POST or PUT, redirects to project detail
- [ ] Cancel returns to project list
- [ ] Client-side validations match all server-side rules
- [ ] DM can only set themselves as DM; CEO/CTO can assign any DM

---

## Story: Implement worklog toggle for projects
**Type:** Feature
**Phase:** 1
**Module:** 03-project-management
**Priority:** P2
**Estimate:** S (1-2d)
**Depends On:** Project CRUD API
**Labels:** backend, frontend

### Description
Allow PM and DM to toggle the worklog_enabled field on their projects via PUT /api/projects/:id. When worklog_enabled=false, employees cannot see the worklog option for that project in the UI. The toggle should be accessible from the project detail screen as a simple switch, calling the update endpoint.

### Acceptance Criteria
- [ ] PM and DM can toggle worklog_enabled on their own projects
- [ ] CEO and CTO can toggle worklog_enabled on any project
- [ ] When disabled, worklog tab/option hidden for employees on that project
- [ ] Toggle change audit logged
- [ ] UI toggle on project detail page

---

## Story: Implement audit logging for all Project write operations
**Type:** Task
**Phase:** 1
**Module:** 03-project-management
**Priority:** P1
**Estimate:** S (1-2d)
**Depends On:** Project CRUD API, status lifecycle
**Labels:** backend

### Description
Wrap all Project CREATE, UPDATE, and status transition operations in audit-aware functions. For CREATE: one AuditLog row. For UPDATE: one row per changed field with old_value and new_value. For status transitions: log the status change and all side effects (auto-released assignments). Capture entity_type=Project, entity_id, action, field_name, old_value, new_value, changed_by, changed_at.

### Acceptance Criteria
- [ ] CREATE: AuditLog entry with entity_type=Project, action=CREATE
- [ ] UPDATE: one AuditLog row per changed field with old and new values
- [ ] Status transition: AuditLog entry for status field change
- [ ] Cascading auto-release on COMPLETED/CANCELLED: each released assignment also audit logged
- [ ] changed_by captures the authenticated user
- [ ] old_value and new_value stored as JSON-serialized strings

---

## Story: Write tests for Project module validations, status machine, and cascading release
**Type:** Task
**Phase:** 1
**Module:** 03-project-management
**Priority:** P1
**Estimate:** M (3-5d)
**Depends On:** All Project API endpoints, status lifecycle
**Labels:** backend

### Description
Write tests covering: CRUD happy paths, all 8 validation rules (name required, client required, type required, DM required, PM required, contract_end_date required for T&M/Onboarding, assignment on non-active project blocked, invalid status transition), all valid status transitions, all invalid status transitions, cascading auto-release when project is COMPLETED or CANCELLED, access control per role, and audit log generation.

### Acceptance Criteria
- [ ] CRUD happy paths pass
- [ ] All 8 validation rules tested with expected error messages
- [ ] Valid transitions: ACTIVE->COMPLETED, ACTIVE->ON_HOLD, ON_HOLD->ACTIVE, ACTIVE->CANCELLED all succeed
- [ ] Invalid transitions return "Invalid status transition"
- [ ] COMPLETED/CANCELLED cascades: all ACTIVE assignments auto-released
- [ ] Cannot create assignment on COMPLETED/CANCELLED project
- [ ] Access control: CEO/CTO full access; DM own portfolio; PM own portfolio; Finance/HR view-only; Engineer 403
- [ ] Audit log entries verified for all operations
