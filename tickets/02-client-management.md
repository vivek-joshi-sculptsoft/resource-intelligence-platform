# Module 02: Client Management — JIRA Tickets

---

## Story: Create Client database table and migration
**Type:** Task
**Phase:** 1
**Module:** 02-client-management
**Priority:** P0
**Estimate:** S (1-2d)
**Depends On:** 01-auth-and-roles (database schema)
**Labels:** backend, database

### Description
Create the Client table with id (UUID PK), name (STRING 255, UNIQUE), industry (STRING 100), contact_name (STRING 255), contact_email (STRING 255), contact_phone (STRING 20), engagement_start_date (DATE), notes (TEXT), is_active (BOOLEAN DEFAULT true), and created_at (TIMESTAMP AUTO). Add indexes on name and is_active. Migration must be reversible.

### Acceptance Criteria
- [ ] Client table created with all fields per SCHEMA.md
- [ ] name column has UNIQUE constraint
- [ ] is_active defaults to true
- [ ] UUID v4 used for primary key
- [ ] Indexes on name and is_active
- [ ] Migration is reversible (up/down)

---

## Story: Implement Client CRUD API endpoints
**Type:** Feature
**Phase:** 1
**Module:** 02-client-management
**Priority:** P1
**Estimate:** M (3-5d)
**Depends On:** Client database table, access control middleware (01-auth-and-roles)
**Labels:** backend

### Description
Build POST /api/clients (create), GET /api/clients (paginated list), GET /api/clients/:id (detail with projects and dashboard stats), PUT /api/clients/:id (update), and DELETE /api/clients/:id (soft-delete). Create requires name (unique). The detail endpoint includes the client's project list and Phase 1 dashboard metrics (active_resource_count, active_project_count). All endpoints enforce access control: CEO/CTO have EDIT ALL; DM/PM have VIEW OWN_PORTFOLIO; Finance/HR have VIEW ALL; Engineer has NONE.

### Acceptance Criteria
- [ ] POST /api/clients creates client with name (required, unique), industry, contact fields, engagement_start_date, notes
- [ ] GET /api/clients returns paginated list with ?page, ?limit, ?status, ?search; each row includes active_project_count
- [ ] GET /api/clients/:id returns full client with project list and dashboard stats (active_resource_count, active_project_count)
- [ ] PUT /api/clients/:id updates any client field; name uniqueness enforced if changed
- [ ] DELETE /api/clients/:id soft-deletes (sets is_active=false)
- [ ] Validation: "Client name is required" when name is blank
- [ ] Validation: "A client with this name already exists" on duplicate name
- [ ] All changes audit logged (entity_type=Client, one row per changed field)

---

## Story: Implement access control and deactivation guard for Client endpoints
**Type:** Feature
**Phase:** 1
**Module:** 02-client-management
**Priority:** P1
**Estimate:** S (1-2d)
**Depends On:** Client CRUD API
**Labels:** backend

### Description
Apply access control middleware to all Client endpoints per shared/ACCESS-MATRIX.md. CEO/CTO have EDIT ALL access. DM and PM have VIEW OWN_PORTFOLIO (scoped to clients with projects where dm_id or pm_id matches the user). Finance and HR have VIEW ALL. Engineer has NONE (403). Additionally, block client deactivation when the client has any project with status=ACTIVE, returning the error "Complete or cancel all projects before deactivating this client."

### Acceptance Criteria
- [ ] CEO, CTO: EDIT ALL access on all client endpoints
- [ ] DM, PM: VIEW OWN_PORTFOLIO — see only clients with projects in their portfolio
- [ ] Finance, HR: VIEW ALL — read-only access to all clients
- [ ] Engineer: NONE — returns 403 on all client endpoints
- [ ] Deactivation blocked if any project with status=ACTIVE exists — error: "Complete or cancel all projects before deactivating this client"
- [ ] Scope filtering applied as WHERE clause at DB level

---

## Story: Implement Client dashboard aggregation endpoint
**Type:** Feature
**Phase:** 1
**Module:** 02-client-management
**Priority:** P2
**Estimate:** S (1-2d)
**Depends On:** Client CRUD API, 03-project-management, 05-allocation-tracking
**Labels:** backend

### Description
Build GET /api/clients/:id/dashboard returning aggregated metrics for the client. Phase 1 metrics: active_resource_count (count of distinct resources with ACTIVE assignments on the client's projects) and active_project_count (count of projects with status=ACTIVE). Phase 2 fields (total_monthly_billing_inr, total_cost_inr, aggregate_margin_inr, project_count_by_type) return null in Phase 1.

### Acceptance Criteria
- [ ] active_resource_count = count of distinct resources with ACTIVE assignments on client's projects
- [ ] active_project_count = count of projects with status=ACTIVE for this client
- [ ] project_count_by_type returns breakdown by FIXED_PRICE, TIME_AND_MATERIAL, CLIENT_ONBOARDING
- [ ] Phase 2 financial fields return null in Phase 1
- [ ] Same access control as GET /api/clients/:id
- [ ] Response shape includes all Phase 2 fields as null (not omitted)

---

## Story: Build Client List screen with search and filters
**Type:** Feature
**Phase:** 1
**Module:** 02-client-management
**Priority:** P1
**Estimate:** M (3-5d)
**Depends On:** Client CRUD API, access control
**Labels:** frontend

### Description
Create the /clients page with a full-width table displaying client name (link to detail), industry, engagement start date, active project count, and status (Active/Inactive badge). Include an "Add Client" button (visible to CEO/CTO only), status filter dropdown (Active/Inactive/All), and search by client name. Table is sortable by name and engagement_start_date. DM/PM see only clients in their portfolio. Engineer role does not see the clients screen.

### Acceptance Criteria
- [ ] Client table with columns: Name (link), Industry, Engagement Start, Active Projects, Status
- [ ] "Add Client" button visible to CEO and CTO only
- [ ] Status filter: Active / Inactive / All
- [ ] Search by client name
- [ ] Column sorting on name and engagement_start_date
- [ ] DM/PM see only clients for their portfolio
- [ ] Engineer role cannot access this screen
- [ ] Empty state: "No clients found. Add your first client to get started."
- [ ] Pagination controls

---

## Story: Build Client Detail screen with project list and dashboard stats
**Type:** Feature
**Phase:** 1
**Module:** 02-client-management
**Priority:** P1
**Estimate:** M (3-5d)
**Depends On:** Client List screen, Client dashboard aggregation API
**Labels:** frontend

### Description
Create the /clients/:id page with a header showing all client fields (name, industry, contact info, engagement start, notes) and an edit button (CEO/CTO only). Below the header, a dashboard stats row showing active resource count and active project count (Phase 2 adds billing, cost, margin). Below that, a projects table listing all projects for this client (name, type badge, status badge, DM name, PM name) with links to project detail. Include a deactivate button with confirmation dialog.

### Acceptance Criteria
- [ ] Client header displays all client fields
- [ ] Edit button visible to CEO and CTO only
- [ ] Dashboard stats row: Active Resources count, Active Projects count
- [ ] Phase 2 financial metrics hidden in Phase 1
- [ ] Projects table: name (link), type (badge), status (badge), DM, PM
- [ ] Click project row navigates to /projects/:id
- [ ] Deactivate button (CEO/CTO) with confirmation dialog — calls DELETE /api/clients/:id
- [ ] Projects empty state: "No projects yet. Add a project for this client."
- [ ] Financial metrics visible only to CEO, CTO, Finance per access matrix

---

## Story: Build Client Create / Edit form
**Type:** Feature
**Phase:** 1
**Module:** 02-client-management
**Priority:** P1
**Estimate:** S (1-2d)
**Depends On:** Client CRUD API
**Labels:** frontend

### Description
Create the /clients/new and /clients/:id/edit forms with name (required), industry, contact name, contact email, contact phone, engagement start date picker, and notes textarea. Save calls POST (create) or PUT (edit), then redirects to client detail on success. Cancel returns to client list. Client-side validation: name required and unique (inline error from server response). CEO and CTO only.

### Acceptance Criteria
- [ ] Name input (required)
- [ ] Industry, contact name, contact email, contact phone inputs
- [ ] Engagement start date picker
- [ ] Notes textarea
- [ ] Save calls POST or PUT, redirects to client detail on success
- [ ] Cancel returns to client list
- [ ] Client-side validation: name required
- [ ] Server error "A client with this name already exists" displayed inline
- [ ] Only accessible to CEO and CTO

---

## Story: Implement audit logging for all Client write operations
**Type:** Task
**Phase:** 1
**Module:** 02-client-management
**Priority:** P1
**Estimate:** S (1-2d)
**Depends On:** Client CRUD API
**Labels:** backend

### Description
Wrap all Client CREATE, UPDATE, and DELETE operations in audit-aware functions that insert rows into the AuditLog table. For CREATE: one row with action=CREATE. For UPDATE: one row per changed field with old_value and new_value as JSON-serialized strings. For DELETE (deactivation): one row logging the is_active change. Capture entity_type=Client, entity_id, action, field_name, old_value, new_value, changed_by, changed_at.

### Acceptance Criteria
- [ ] CREATE: AuditLog entry with entity_type=Client, action=CREATE, all field values logged
- [ ] UPDATE: one AuditLog row per changed field with old_value and new_value
- [ ] DELETE (deactivation): AuditLog entry for is_active change from true to false
- [ ] changed_by captures the current authenticated user ID
- [ ] changed_at captures the timestamp of the operation
- [ ] old_value and new_value stored as JSON-serialized strings
- [ ] AuditLog is append-only (no UPDATE or DELETE on AuditLog)

---

## Story: Write tests for Client module validation, access control, and deactivation guard
**Type:** Task
**Phase:** 1
**Module:** 02-client-management
**Priority:** P1
**Estimate:** S (1-2d)
**Depends On:** All Client API endpoints
**Labels:** backend

### Description
Write tests covering: CRUD happy paths, name required validation, name uniqueness validation, deactivation guard (block when active projects exist, allow when no active projects), access control per role (CEO/CTO EDIT, DM/PM VIEW scoped, Finance/HR VIEW, Engineer 403), dashboard aggregation correctness, and audit log generation.

### Acceptance Criteria
- [ ] Create client: happy path passes
- [ ] Create client: blank name returns "Client name is required"
- [ ] Create client: duplicate name returns "A client with this name already exists"
- [ ] Deactivation: blocked when active projects exist
- [ ] Deactivation: allowed when no active projects
- [ ] Access control: CEO/CTO can create, read, update, deactivate
- [ ] Access control: DM/PM can read only own-portfolio clients
- [ ] Access control: Finance/HR can read all clients
- [ ] Access control: Engineer receives 403
- [ ] Dashboard aggregation returns correct counts
- [ ] Audit log entries created for all write operations
