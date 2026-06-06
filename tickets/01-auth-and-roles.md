# Module 01: Auth & Roles — JIRA Tickets

---

## Story: Create Role, RolePermission, User, and SystemConfig database schema and migrations
**Type:** Task
**Phase:** 1
**Module:** 01-auth-and-roles
**Priority:** P0
**Estimate:** M (3-5d)
**Depends On:** None
**Labels:** backend, database, infrastructure

### Description
Create the database tables for Role, RolePermission, User, and SystemConfig (Phase 1 keys). Role has id (UUID PK), name (STRING UNIQUE), code (STRING UNIQUE), permission_level (INTEGER), is_active, created_at. RolePermission has id (UUID PK), role_id (FK), data_type (STRING, 15 allowed values), access_level (ENUM: NONE/VIEW/EDIT), scope (ENUM: ALL/OWN_PORTFOLIO/SELF_ONLY), is_configurable (BOOLEAN), with a unique constraint on (role_id, data_type). User has id (UUID PK), email (STRING UNIQUE), name, role_id (FK), resource_id (FK nullable), is_active, created_at, updated_at. SystemConfig has key-value pairs. All PKs are UUID v4. All tables have created_at and updated_at where specified. Foreign keys and status fields indexed.

### Acceptance Criteria
- [ ] Role table created with all fields per SCHEMA.md
- [ ] RolePermission table created with unique constraint on (role_id, data_type) and 15 allowed data_type values enforced
- [ ] User table created with unique email constraint and FK to Role
- [ ] SystemConfig table created with key/value/description fields
- [ ] All foreign keys indexed
- [ ] Migration is reversible (up/down)
- [ ] UUID v4 used for all primary keys

---

## Story: Create seed script for 7 default roles, 105 RolePermission rows, SystemConfig defaults, and admin user
**Type:** Task
**Phase:** 1
**Module:** 01-auth-and-roles
**Priority:** P0
**Estimate:** M (3-5d)
**Depends On:** Database schema (previous story)
**Labels:** backend, database, infrastructure

### Description
Build an idempotent seed script that populates the system with initial data on first deployment. The script must insert 7 roles (CEO permission_level=100, CTO=90, DM=70, PM=60, FINANCE=70, HR=50, ENGINEER=10), all 105 RolePermission rows per the full matrix in shared/ACCESS-MATRIX.md, 7 SystemConfig default keys (alert thresholds, working days/hours, default currency), and one admin user with the CEO role. The seed must be safe to run multiple times without duplicating data.

### Acceptance Criteria
- [ ] 7 roles seeded: CEO, CTO, DM, PM, FINANCE, HR, ENGINEER with correct permission_levels
- [ ] 105 RolePermission rows seeded (7 roles x 15 data_types) with correct access_level, scope, and is_configurable values per shared/ACCESS-MATRIX.md
- [ ] 7 SystemConfig keys seeded with defaults: alert.contract_expiry_days=30, alert.contract_expiry_urgent_days=7, alert.bench_threshold_days=7, alert.utilization_threshold_pct=70, system.working_days_per_month=22, system.working_hours_per_day=8, system.default_currency=INR
- [ ] 1 admin user created with CEO role and valid hashed password
- [ ] Seed is idempotent — running it again does not create duplicate rows
- [ ] Seed script can be run as part of deployment pipeline

---

## Story: Implement login and logout authentication endpoints
**Type:** Feature
**Phase:** 1
**Module:** 01-auth-and-roles
**Priority:** P0
**Estimate:** M (3-5d)
**Depends On:** Database schema, seed data
**Labels:** backend, infrastructure

### Description
Build POST /api/auth/login and POST /api/auth/logout endpoints. Login accepts email and password, validates credentials against the User table with hashed password comparison, and returns a JWT token (or session) with user info including role code and name. Login must return a generic 401 error for any invalid credential (no disclosure of which field is wrong). Inactive users (is_active=false) are blocked with "Account is inactive". Logout invalidates the current session/token.

### Acceptance Criteria
- [ ] POST /api/auth/login accepts email + password, returns token and user object with id, name, email, role (code + name)
- [ ] Invalid credentials return generic 401 (no field-level disclosure)
- [ ] Inactive users (is_active=false) cannot log in, returns "Account is inactive"
- [ ] POST /api/auth/logout invalidates the session/token
- [ ] Password stored as a secure hash (bcrypt or argon2), never plaintext
- [ ] Response follows consistent error format: { error: true, message: "..." }

---

## Story: Implement GET /api/auth/me endpoint for current user profile
**Type:** Feature
**Phase:** 1
**Module:** 01-auth-and-roles
**Priority:** P0
**Estimate:** S (1-2d)
**Depends On:** Login endpoint
**Labels:** backend

### Description
Build GET /api/auth/me to return the authenticated user's profile including id, name, email, role (id, code, name, permission_level), and resource_id. Returns 401 if no valid session exists. This endpoint is used by the frontend on page load to establish the current user context.

### Acceptance Criteria
- [ ] GET /api/auth/me returns user id, name, email, role (id, code, name, permission_level), resource_id
- [ ] Returns 401 if no valid session/token
- [ ] Works for all authenticated roles

---

## Story: Build access control middleware that checks RolePermission on every API call
**Type:** Feature
**Phase:** 1
**Module:** 01-auth-and-roles
**Priority:** P0
**Estimate:** L (5-10d)
**Depends On:** Login endpoint, seed data
**Labels:** backend, infrastructure

### Description
Create middleware/decorator that intercepts every protected API call, reads the user's role_id from the session, looks up RolePermission for (role_id, data_type), and enforces access rules. Returns HTTP 403 for access_level=NONE. Applies scope filtering (ALL, OWN_PORTFOLIO, SELF_ONLY) as a WHERE clause at the database query level, not post-fetch. Sets restricted sensitive fields (loaded_cost_monthly, billing_rate, billability_pct, is_shadow, margin fields) to null in responses for unauthorized roles. All 15 data_types must be handled. This middleware is the foundation for access control across the entire platform.

### Acceptance Criteria
- [ ] Middleware reads role_id from authenticated session
- [ ] Looks up RolePermission for role_id + data_type
- [ ] Returns HTTP 403 for access_level = NONE
- [ ] Applies scope filter ALL = no filter, OWN_PORTFOLIO = dm_id/pm_id match, SELF_ONLY = resource_id match
- [ ] Scope filtering applied as WHERE clause at DB query level, not post-fetch
- [ ] Sensitive fields set to null (not omitted) in responses for unauthorized roles
- [ ] All 15 data_types handled: client_profiles, project_details, resource_profiles, allocation, billability, billing_rates, ctc_loaded_cost, project_margin, non_human_costs, shadow_assignments, resource_availability, bench_data, invoicing, worklogs, alerts
- [ ] Middleware is reusable across all modules
- [ ] Consistent error response: { error: true, message: "Access denied" }

---

## Story: Implement User CRUD API endpoints for admin management
**Type:** Feature
**Phase:** 1
**Module:** 01-auth-and-roles
**Priority:** P1
**Estimate:** M (3-5d)
**Depends On:** Access control middleware
**Labels:** backend

### Description
Build GET /api/users (paginated list), POST /api/users (create), GET /api/users/:id (detail), and PUT /api/users/:id (update) endpoints. All endpoints are restricted to CEO and CTO roles only. Create requires email (unique), name, role_id, password, and optional resource_id. Update supports changing name, role_id, resource_id, and is_active. Deactivation of the last active admin user is blocked. Email uniqueness enforced on create and update. All changes are audit logged.

### Acceptance Criteria
- [ ] GET /api/users returns paginated list with role info, supports ?page, ?limit, ?status, ?search
- [ ] POST /api/users creates user with email, name, role_id, password, optional resource_id
- [ ] GET /api/users/:id returns full user object with role details
- [ ] PUT /api/users/:id updates name, role_id, resource_id, is_active
- [ ] Email must be unique across all users — error: "Email is already in use"
- [ ] Role is required — error: "User must have a role"
- [ ] Cannot deactivate the last active user with CEO or CTO role
- [ ] Soft-delete via is_active=false, never hard delete
- [ ] All endpoints restricted to CEO and CTO only (HTTP 403 for others)
- [ ] All changes audit logged (entity_type=User, one row per changed field)

---

## Story: Implement Role and RolePermission read-only API endpoints
**Type:** Feature
**Phase:** 1
**Module:** 01-auth-and-roles
**Priority:** P1
**Estimate:** S (1-2d)
**Depends On:** Access control middleware
**Labels:** backend

### Description
Build GET /api/roles (list all roles with nested RolePermission arrays), GET /api/roles/:id (single role with full permission set), and GET /api/roles/:id/permissions (15 data-type permissions for a role). All endpoints are restricted to CEO and CTO only. Role editing is deferred to Phase 3.

### Acceptance Criteria
- [ ] GET /api/roles returns array of roles, each with nested array of 15 RolePermission rows
- [ ] GET /api/roles/:id returns single role with full permission set
- [ ] GET /api/roles/:id/permissions returns array of { data_type, access_level, scope, is_configurable }
- [ ] All endpoints restricted to CEO and CTO only
- [ ] All 7 roles and their 15 permissions each are returned correctly

---

## Story: Build Login screen UI
**Type:** Feature
**Phase:** 1
**Module:** 01-auth-and-roles
**Priority:** P0
**Estimate:** S (1-2d)
**Depends On:** Login API endpoint
**Labels:** frontend

### Description
Create the /login page with a centered card layout containing logo/system name, email input, password input, login button, and error message area. On submit, POST to /api/auth/login. On success, store token and redirect to home dashboard. On failure, display generic error message below the form. Authenticated users are redirected away from the login page.

### Acceptance Criteria
- [ ] Login page at /login with centered card layout
- [ ] Email and password input fields with login button
- [ ] Submit calls POST /api/auth/login
- [ ] On success: stores token, redirects to dashboard
- [ ] On failure: shows generic error message (no field-level disclosure)
- [ ] Authenticated users redirected to dashboard
- [ ] Loading state on submit button while request is in flight

---

## Story: Build User Management list screen
**Type:** Feature
**Phase:** 1
**Module:** 01-auth-and-roles
**Priority:** P1
**Estimate:** M (3-5d)
**Depends On:** User CRUD API, Login screen
**Labels:** frontend

### Description
Create the /admin/users page with a full-width table showing all users (name, email, role, linked resource name, active/inactive status, created date). Include an "Add User" button, status filter dropdown (Active/Inactive/All), and search by name or email. Clicking a row opens the user edit form. CEO and CTO only — not visible to other roles.

### Acceptance Criteria
- [ ] User table displays name, email, role name, resource link (or dash if none), status badge, created date
- [ ] "Add User" button opens create form
- [ ] Status filter dropdown: Active / Inactive / All
- [ ] Search by name or email
- [ ] Click row opens user edit form
- [ ] Toggle active/inactive via PUT /api/users/:id
- [ ] Empty state: "No users found. Add your first user to get started."
- [ ] Only accessible to CEO and CTO roles

---

## Story: Build Create / Edit User form
**Type:** Feature
**Phase:** 1
**Module:** 01-auth-and-roles
**Priority:** P1
**Estimate:** M (3-5d)
**Depends On:** User Management list screen, Role API
**Labels:** frontend

### Description
Create the user create (/admin/users/new) and edit (/admin/users/:id/edit) form with name (required), email (required, unique validation), password (required on create, optional on edit), role dropdown (populated from GET /api/roles), resource link dropdown (from active resources), and active toggle (edit only). On save, call POST or PUT. Show success toast and return to list. Client-side validation mirrors server-side rules.

### Acceptance Criteria
- [ ] Name input (required)
- [ ] Email input (required, validated unique with inline error)
- [ ] Password input (required on create, optional blank on edit)
- [ ] Role dropdown populated from GET /api/roles (required)
- [ ] Resource link dropdown populated from active resources (optional)
- [ ] Active toggle visible on edit only
- [ ] Save calls POST (create) or PUT (edit)
- [ ] Success toast + redirect to user list
- [ ] Cancel returns to user list without saving
- [ ] Client-side validations match server rules: email unique, role required
- [ ] Only accessible to CEO and CTO

---

## Story: Build Role Management screen with permission matrix view
**Type:** Feature
**Phase:** 1
**Module:** 01-auth-and-roles
**Priority:** P2
**Estimate:** M (3-5d)
**Depends On:** Role API endpoints
**Labels:** frontend

### Description
Create the /admin/roles page with a split layout: role list on the left (name, code, permission level) and permission matrix on the right. Selecting a role displays its 15 data-type permissions in a table showing data type (human-readable label), access level (NONE/VIEW/EDIT, color-coded), scope (ALL/OWN_PORTFOLIO/SELF_ONLY), and configurable flag. Editing permissions is disabled in Phase 1/2 (Phase 3 feature). CEO and CTO only.

### Acceptance Criteria
- [ ] Role list displays name, code, permission level for all 7 roles
- [ ] Clicking a role shows its 15-row permission matrix on the right
- [ ] Permission matrix columns: Data Type (label), Access Level (color-coded), Scope, Configurable (Yes/No)
- [ ] Edit permissions button present but disabled (Phase 3)
- [ ] Empty state: "Select a role to view its permissions."
- [ ] Only accessible to CEO and CTO

---

## Story: Write integration tests for auth flow and access control middleware
**Type:** Task
**Phase:** 1
**Module:** 01-auth-and-roles
**Priority:** P1
**Estimate:** M (3-5d)
**Depends On:** All auth API endpoints, access control middleware
**Labels:** backend, infrastructure

### Description
Write integration tests covering: login happy path and failure cases (wrong password, inactive user, missing fields), logout and token invalidation, GET /api/auth/me with and without valid session, user CRUD happy paths, user CRUD access control (non-admin blocked), access control middleware for each of the 15 data_types across multiple roles (verifying NONE returns 403, scope filtering is correct, and sensitive fields are null for unauthorized roles). Each validation rule from FSD must have a test that triggers it.

### Acceptance Criteria
- [ ] Login: valid credentials return token + user; invalid return 401 generic error; inactive user returns "Account is inactive"
- [ ] Logout: token invalidated, subsequent requests return 401
- [ ] GET /api/auth/me: returns profile when authenticated, 401 when not
- [ ] User CRUD: create, read, update, deactivate happy paths pass
- [ ] User CRUD: non-CEO/CTO users receive 403
- [ ] Cannot deactivate last active admin user
- [ ] Email uniqueness enforced on create and update
- [ ] Access control middleware: NONE returns 403 for each role/data_type combo
- [ ] Access control middleware: OWN_PORTFOLIO scope filters correctly for DM and PM
- [ ] Access control middleware: SELF_ONLY scope filters correctly for Engineer
- [ ] Sensitive fields (loaded_cost_monthly, billing_rate, etc.) return null for unauthorized roles
