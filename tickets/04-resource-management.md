# Module 04: Resource Management — JIRA Tickets

---

## Story: Create Resource and ResourceTag database tables and migration
**Type:** Task
**Phase:** 1
**Module:** 04-resource-management
**Priority:** P0
**Estimate:** S (1-2d)
**Depends On:** 01-auth-and-roles (database schema)
**Labels:** backend, database

### Description
Create the Resource table with id (UUID PK), employee_id (STRING 50 UNIQUE), name (STRING 255), designation (STRING 100), technical_expertise (STRING 100 NULLABLE), date_of_joining (DATE), reporting_manager_id (FK to Resource NULLABLE, self-referencing), loaded_cost_monthly (DECIMAL 15,2 NULLABLE — Phase 2), is_active (BOOLEAN DEFAULT true), and created_at (TIMESTAMP AUTO). Create the ResourceTag join table with resource_id (FK to Resource) and tag (STRING 100) as a composite primary key. Add indexes on employee_id, is_active, designation, reporting_manager_id for Resource, and resource_id and tag for ResourceTag.

### Acceptance Criteria
- [ ] Resource table created with all fields per SCHEMA.md
- [ ] employee_id has UNIQUE constraint
- [ ] reporting_manager_id is a self-referencing FK, nullable
- [ ] loaded_cost_monthly column present but nullable (Phase 2)
- [ ] ResourceTag table with composite PK (resource_id, tag)
- [ ] Indexes on employee_id, is_active, designation, reporting_manager_id, resource_id, tag
- [ ] UUID v4 for Resource primary key
- [ ] Migration is reversible

---

## Story: Implement Resource CRUD API endpoints
**Type:** Feature
**Phase:** 1
**Module:** 04-resource-management
**Priority:** P1
**Estimate:** M (3-5d)
**Depends On:** Resource database table, access control middleware
**Labels:** backend

### Description
Build POST /api/resources (create), GET /api/resources (paginated list with filters), GET /api/resources/:id (profile with assignments and tags), PUT /api/resources/:id (update), and DELETE /api/resources/:id (soft-deactivate). Create requires name, employee_id (unique), and designation. The list endpoint supports filtering by designation, expertise, tags, availability (bench/partial/full), status, and search by name or employee_id. Each list item includes computed total_allocation_pct. The profile endpoint includes active_assignments array and total_allocation_pct. loaded_cost_monthly is returned as null for unauthorized roles.

### Acceptance Criteria
- [ ] POST /api/resources creates resource with name, employee_id, designation (all required), plus optional fields and tags array
- [ ] GET /api/resources returns paginated list with filters: ?designation, ?expertise, ?tag, ?availability, ?status, ?search, ?page, ?limit
- [ ] Each list item includes total_allocation_pct (sum of ACTIVE assignment allocation_pct values)
- [ ] GET /api/resources/:id returns full profile with tags, active_assignments (with project name), total_allocation_pct
- [ ] PUT /api/resources/:id updates any resource field
- [ ] DELETE /api/resources/:id sets is_active=false
- [ ] Validation: "Resource name is required" when name blank
- [ ] Validation: "Employee ID is required" when employee_id blank
- [ ] Validation: "This employee ID is already in use" on duplicate employee_id
- [ ] Validation: "Designation is required" when designation blank
- [ ] Validation: "A resource cannot report to themselves" when reporting_manager_id = self
- [ ] loaded_cost_monthly returned as null for roles without access (not omitted)
- [ ] All changes audit logged

---

## Story: Implement access control for Resource endpoints
**Type:** Feature
**Phase:** 1
**Module:** 04-resource-management
**Priority:** P1
**Estimate:** S (1-2d)
**Depends On:** Resource CRUD API
**Labels:** backend

### Description
Apply role-based access control to all Resource endpoints per shared/ACCESS-MATRIX.md. CEO/CTO have EDIT ALL. HR has EDIT ALL on resource_profiles (but no access to loaded_cost_monthly). Finance has VIEW ALL on profiles and can edit loaded_cost_monthly only (Phase 2). DM has VIEW OWN_PORTFOLIO (resources on DM's projects). PM has VIEW OWN_PORTFOLIO. Engineer has VIEW SELF_ONLY (can only see own resource profile). loaded_cost_monthly, billing_rate, billability_pct, and is_shadow fields return null for unauthorized roles.

### Acceptance Criteria
- [ ] CEO, CTO: EDIT ALL on all resource endpoints
- [ ] HR: EDIT ALL for profiles (create/update resource profiles, not loaded_cost_monthly)
- [ ] Finance: VIEW ALL for profiles; EDIT loaded_cost_monthly (Phase 2)
- [ ] DM, PM: VIEW OWN_PORTFOLIO — see only resources on their projects
- [ ] Engineer: VIEW SELF_ONLY — can only access own resource profile
- [ ] loaded_cost_monthly returns null for all roles except CEO, CTO, Finance
- [ ] Scope filtering applied as WHERE clause at DB level

---

## Story: Implement Resource deactivation cascade
**Type:** Feature
**Phase:** 1
**Module:** 04-resource-management
**Priority:** P1
**Estimate:** S (1-2d)
**Depends On:** Resource CRUD API, 05-allocation-tracking
**Labels:** backend

### Description
When a resource is deactivated (is_active set to false via DELETE /api/resources/:id), all of their ACTIVE assignments must be immediately released (status=RELEASED, released_at=now()). The resource must also be blocked from receiving new assignments after deactivation. Additionally, block deactivation if the resource is currently assigned as DM or PM on any ACTIVE project. All cascade effects are audit logged.

### Acceptance Criteria
- [ ] Deactivation cascades: all ACTIVE assignments released (status=RELEASED, released_at=now())
- [ ] Deactivated resource cannot receive new assignments
- [ ] Block deactivation if resource is DM or PM on any ACTIVE project
- [ ] Each released assignment audit logged
- [ ] Resource deactivation audit logged
- [ ] Only CEO, CTO, HR can deactivate resources

---

## Story: Implement Tag Management API endpoints
**Type:** Feature
**Phase:** 1
**Module:** 04-resource-management
**Priority:** P2
**Estimate:** S (1-2d)
**Depends On:** Resource CRUD API
**Labels:** backend

### Description
Build POST /api/resources/:id/tags (add a tag) and DELETE /api/resources/:id/tags/:tag (remove a tag). Tags are free-form strings up to 100 characters with no predefined list. Adding a tag inserts a row in ResourceTag; removing deletes it. Both endpoints return the updated tags array. Tags are searchable in the resource list filter. CEO, CTO, HR, and DM (own portfolio) can manage tags.

### Acceptance Criteria
- [ ] POST /api/resources/:id/tags adds a tag { tag: "string" } and returns updated tags array
- [ ] DELETE /api/resources/:id/tags/:tag removes a tag and returns updated tags array
- [ ] Tag max length 100 characters
- [ ] Tags are free-form — no predefined list validation
- [ ] Duplicate tag on same resource is a no-op or returns existing tags
- [ ] Tags searchable in GET /api/resources via ?tag= filter
- [ ] CEO, CTO, HR can manage tags on any resource; DM on own portfolio resources

---

## Story: Build Resource List screen with search and filters
**Type:** Feature
**Phase:** 1
**Module:** 04-resource-management
**Priority:** P1
**Estimate:** M (3-5d)
**Depends On:** Resource CRUD API, Tag Management API
**Labels:** frontend

### Description
Create the /resources page with a full-width table displaying resource name (link to profile), employee ID, designation, expertise, tags (pill badges), total allocation %, availability status (Bench/Partial/Full), and active/inactive status. Include search by name or employee ID, filters for designation, expertise, tags (multi-select), availability (Bench/Partial/Fully Allocated/All), and status (Active/Inactive/All). "Add Resource" button visible to CEO, CTO, HR only. Table supports column sorting. Engineer sees only own record. loaded_cost_monthly never shown in list view.

### Acceptance Criteria
- [ ] Resource table: Name (link), Employee ID, Designation, Expertise, Tags (pills), Total Allocation %, Availability, Status
- [ ] Search by name or employee ID
- [ ] Filters: designation, expertise, tags (multi-select), availability, status
- [ ] "Add Resource" button visible to CEO, CTO, HR only
- [ ] Column sorting on name, designation, date_of_joining
- [ ] Availability computed: Bench (0%), Partial (<100%), Full (100%+)
- [ ] Engineer sees only own record
- [ ] loaded_cost_monthly never shown in list
- [ ] Empty state: "No resources found. Try adjusting filters."
- [ ] Pagination controls

---

## Story: Build Resource Profile screen with assignments, stats, and tags
**Type:** Feature
**Phase:** 1
**Module:** 04-resource-management
**Priority:** P1
**Estimate:** L (5-10d)
**Depends On:** Resource CRUD API, Tag Management API, 05-allocation-tracking
**Labels:** frontend

### Description
Create the /resources/:id page with a header (name, employee ID, designation, expertise, date of joining, reporting manager, tags with add/remove, edit button), a stats row (total allocation %, availability status, days on bench if 0%), an active assignments table (project name, effective designation with fallback, allocation %, billability % — hidden from HR/Engineer, shadow flag — hidden from HR/Engineer, start/end dates), and an assignment history section (released/auto-released with dates). Loaded cost field visible to CEO/CTO/Finance only (Phase 2). Over-allocation highlighted red when total > 100%.

### Acceptance Criteria
- [ ] Header: name, employee ID, designation, expertise, DOJ, reporting manager, tags (editable), edit button
- [ ] Stats row: total allocation %, availability status, days on bench (if bench)
- [ ] Active assignments table: project name, effective designation (project_designation or resource.designation), allocation %, billability %, shadow flag, start/end dates
- [ ] billability_pct and is_shadow hidden from HR and Engineer
- [ ] Assignment history section: released/auto-released assignments with dates
- [ ] Total allocation > 100% highlighted in red
- [ ] Loaded cost field: visible to CEO/CTO/Finance only, Phase 2
- [ ] Tags: inline add/remove
- [ ] Edit button: CEO/CTO/HR for profiles
- [ ] Assignments empty state: "No active assignments. This resource is on bench."
- [ ] Engineer can only view own profile (SELF_ONLY)

---

## Story: Build Resource Create / Edit form
**Type:** Feature
**Phase:** 1
**Module:** 04-resource-management
**Priority:** P1
**Estimate:** S (1-2d)
**Depends On:** Resource CRUD API
**Labels:** frontend

### Description
Create the /resources/new and /resources/:id/edit forms. Fields: name (required), employee ID (required), designation (required), technical expertise, date of joining date picker, reporting manager dropdown from active resources (self excluded), tags input with add/remove, and loaded cost monthly input (Phase 2 — visible to CEO/CTO/Finance only). Save calls POST or PUT, redirects to resource profile. Cancel returns to list. Client-side validations match server-side rules.

### Acceptance Criteria
- [ ] Name input (required)
- [ ] Employee ID input (required)
- [ ] Designation input (required)
- [ ] Technical expertise input
- [ ] Date of joining date picker
- [ ] Reporting manager dropdown from active resources (excludes self)
- [ ] Tags input with add/remove capability
- [ ] Loaded cost monthly input (Phase 2, visible to CEO/CTO/Finance only)
- [ ] Save calls POST or PUT, redirects to resource profile
- [ ] Cancel returns to resource list
- [ ] Client-side validations: name required, employee_id required and unique, designation required, no self-reporting
- [ ] Accessible to CEO, CTO, HR (create/edit); Finance (loaded_cost_monthly only, Phase 2)

---

## Story: Implement audit logging for all Resource write operations
**Type:** Task
**Phase:** 1
**Module:** 04-resource-management
**Priority:** P1
**Estimate:** S (1-2d)
**Depends On:** Resource CRUD API, Tag Management API
**Labels:** backend

### Description
Wrap all Resource CREATE, UPDATE, DELETE (deactivation), and tag management operations in audit-aware functions. For UPDATE: one AuditLog row per changed field including loaded_cost_monthly changes with old/new values. Deactivation logs the is_active change and each cascaded assignment release. Tag additions and removals are audit logged.

### Acceptance Criteria
- [ ] CREATE: AuditLog entry with entity_type=Resource, action=CREATE
- [ ] UPDATE: one AuditLog row per changed field with old_value and new_value
- [ ] loaded_cost_monthly changes explicitly audit logged with old and new values
- [ ] Deactivation: AuditLog for is_active change plus each cascaded assignment release
- [ ] Tag add/remove: audit logged
- [ ] changed_by and changed_at captured
- [ ] old_value and new_value as JSON-serialized strings

---

## Story: Write tests for Resource module validations, deactivation cascade, and access control
**Type:** Task
**Phase:** 1
**Module:** 04-resource-management
**Priority:** P1
**Estimate:** M (3-5d)
**Depends On:** All Resource API endpoints
**Labels:** backend

### Description
Write tests covering: CRUD happy paths, all 5 validation rules (name required, employee_id required, employee_id unique, designation required, no self-reporting-manager), deactivation cascade (all active assignments released), deactivation blocked when resource is DM/PM on active project, tag management (add, remove, search by tag), access control per role (CEO/CTO EDIT ALL, HR EDIT profiles, DM/PM VIEW OWN_PORTFOLIO, Engineer SELF_ONLY), loaded_cost_monthly null for unauthorized roles, and audit log generation.

### Acceptance Criteria
- [ ] CRUD happy paths pass
- [ ] All 5 validation rules tested with expected error messages
- [ ] Deactivation cascade: ACTIVE assignments released
- [ ] Deactivation blocked: resource is DM/PM on ACTIVE project
- [ ] Tag add/remove works correctly
- [ ] Resource search by tag returns correct results
- [ ] Access control: CEO/CTO full access, HR can create/edit profiles, DM/PM view own portfolio, Engineer sees self only
- [ ] loaded_cost_monthly null for HR, DM, PM, Engineer
- [ ] Audit log entries verified for all operations
