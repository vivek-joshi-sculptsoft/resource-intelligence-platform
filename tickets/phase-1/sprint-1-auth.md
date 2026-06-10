# Sprint 1 — Authentication & Roles

**Goal:** Login works. RBAC middleware enforced on every API call. User management for admins. Role permission viewer.
**Capacity:** 25 SP | **Duration:** 1 week
**Epic:** EP-1 — Authentication & Roles

---

### S1-01: Implement login and logout API endpoints
**Type:** Story | **Points:** 3 (M) | **Priority:** P0 — Blocker
**Labels:** `backend`, `phase-1`, `must-have`, `agentic`
**Depends On:** S0-05, S0-06

#### Context (read before starting)
- `modules/01-auth-and-roles/API.md` → POST /auth/login, POST /auth/logout
- `modules/01-auth-and-roles/REQUIREMENTS.md` → Login/Logout section
- `techstack/auth.md` → Login flow, Token strategy, Cookie flags

#### Description
As a user, I want to log in with email/password so that I can access the platform.

#### Acceptance Criteria
- [ ] `POST /api/v1/auth/login` — accepts email + password
- [ ] Validates password with argon2id
- [ ] Returns user profile (id, name, email, role code+name, resource_id)
- [ ] Sets httpOnly, Secure, SameSite=Strict cookies for access (15min) and refresh (7d) tokens
- [ ] JWT payload: sub (user UUID), role (code), role_id, resource_id, exp, iat
- [ ] Invalid credentials: generic 401 `{"error": true, "message": "Invalid email or password"}`
- [ ] Inactive user: 401 `{"error": true, "message": "Account is inactive"}`
- [ ] `POST /api/v1/auth/logout` — clears cookies, blacklists refresh token in Redis
- [ ] Rate limit: 10 req/min on login per IP

---

### S1-02: Implement token refresh and GET /api/v1/auth/me
**Type:** Story | **Points:** 2 (S) | **Priority:** P0 — Blocker
**Labels:** `backend`, `phase-1`, `must-have`, `agentic`
**Depends On:** S1-01

#### Context (read before starting)
- `modules/01-auth-and-roles/API.md` → POST /auth/refresh, GET /auth/me
- `techstack/auth.md` → Token Refresh flow, Session Management

#### Description
As a frontend app, I want to silently refresh tokens and get the current user so that sessions persist.

#### Acceptance Criteria
- [ ] `POST /api/v1/auth/refresh` — reads refresh token from cookie
- [ ] Validates signature and expiry
- [ ] Checks user still active
- [ ] Issues new access token, rotates refresh token (old invalidated)
- [ ] `GET /api/v1/auth/me` — returns user profile with role details
- [ ] Returns 401 if no valid session
- [ ] Refresh token rotation: old token immediately blacklisted in Redis

---

### S1-03: Build RBAC access control middleware
**Type:** Story | **Points:** 5 (L) | **Priority:** P0 — Blocker
**Labels:** `backend`, `phase-1`, `must-have`, `agentic`
**Depends On:** S1-01, S0-06

#### Context (read before starting)
- `shared/ACCESS-MATRIX.md` — full permission matrix (105 rows)
- `modules/01-auth-and-roles/REQUIREMENTS.md` → Access Control Middleware
- `techstack/auth.md` → Authorization Model, Implementation code sample
- `CLAUDE.md` → Access Control Implementation section

#### Description
As a platform, I want every API call checked against RolePermission so that unauthorized access is blocked.

#### Acceptance Criteria
- [ ] `app/middleware/rbac.py` — `require_access(data_type, min_level)` FastAPI dependency
- [ ] Reads role_id from JWT, looks up RolePermission for (role_id, data_type)
- [ ] access_level=NONE → HTTP 403 `{"error": true, "message": "Access denied"}`
- [ ] access_level=VIEW → blocks POST/PUT/DELETE, allows GET
- [ ] access_level=EDIT → full access
- [ ] Scope filtering returns Permission object with scope enum
- [ ] `apply_scope_filter(query, permission, user)` helper that adds WHERE clauses:
  - ALL → no filter
  - OWN_PORTFOLIO → `project.dm_id = user.resource_id OR project.pm_id = user.resource_id`
  - SELF_ONLY → `resource_id = user.resource_id`
- [ ] `null_restricted_fields(data, permission, field_map)` helper that sets sensitive fields to null
- [ ] All 15 data_types handled
- [ ] RolePermission lookups cached in Redis (5min TTL)
- [ ] Middleware is reusable: `permission = require_access("allocation")` in any router

---

### S1-04: Implement User CRUD API endpoints
**Type:** Story | **Points:** 3 (M) | **Priority:** P1 — Critical
**Labels:** `backend`, `phase-1`, `must-have`, `agentic`
**Depends On:** S1-03, S0-07

#### Context (read before starting)
- `modules/01-auth-and-roles/API.md` → /users endpoints
- `modules/01-auth-and-roles/REQUIREMENTS.md` → User Management section
- `modules/01-auth-and-roles/SCHEMA.md` → User entity

#### Description
As a CEO/CTO, I want to manage platform users so that the right people have access.

#### Acceptance Criteria
- [ ] `GET /api/v1/users` — paginated list with ?page, ?limit, ?status, ?search
- [ ] `POST /api/v1/users` — create with email (unique), name, role_id, password
- [ ] `GET /api/v1/users/:id` — detail with role info
- [ ] `PUT /api/v1/users/:id` — update name, role_id, resource_id, is_active
- [ ] Validation: "Email is already in use" on duplicate
- [ ] Validation: "User must have a role" when role_id missing
- [ ] Cannot deactivate last active CEO/CTO user
- [ ] Soft delete via is_active=false
- [ ] Restricted to CEO and CTO only (403 for others)
- [ ] All changes audit logged via audit wrapper

---

### S1-05: Implement Role and RolePermission read-only API
**Type:** Story | **Points:** 2 (S) | **Priority:** P1 — Critical
**Labels:** `backend`, `phase-1`, `must-have`, `agentic`
**Depends On:** S1-03

#### Context (read before starting)
- `modules/01-auth-and-roles/API.md` → /roles endpoints
- `modules/01-auth-and-roles/REQUIREMENTS.md` → Role Management section

#### Description
As a CEO/CTO, I want to view role permissions so that I can understand the access matrix.

#### Acceptance Criteria
- [ ] `GET /api/v1/roles` — list all roles with nested permissions array
- [ ] `GET /api/v1/roles/:id` — single role with full 15-row permission set
- [ ] `GET /api/v1/roles/:id/permissions` — flat array of permissions
- [ ] CEO and CTO only (403 for others)
- [ ] All 7 roles and 105 permissions returned correctly

---

### S1-06: Build Login screen UI
**Type:** Story | **Points:** 2 (S) | **Priority:** P0 — Blocker
**Labels:** `frontend`, `phase-1`, `must-have`, `agentic`
**Depends On:** S1-01, S0-02

#### Context (read before starting)
- `modules/01-auth-and-roles/SCREENS.md` → Login screen spec
- `techstack/frontend.md` → Routing, state management

#### Description
As a user, I want a login page so that I can authenticate into the platform.

#### Acceptance Criteria
- [ ] `/login` route with centered card layout
- [ ] App name/logo placeholder, email input, password input, login button
- [ ] Submit calls `POST /api/v1/auth/login`
- [ ] On success: store user in Zustand auth store, redirect to `/`
- [ ] On failure: show generic error below form (no field-level disclosure)
- [ ] Loading state on button during request
- [ ] Authenticated users auto-redirected away from `/login`
- [ ] Protected route wrapper: unauthenticated users redirect to `/login`
- [ ] On app load: call `GET /api/v1/auth/me` to restore session

---

### S1-07: Build User Management screens (list + form)
**Type:** Story | **Points:** 3 (M) | **Priority:** P1 — Critical
**Labels:** `frontend`, `phase-1`, `must-have`, `agentic`
**Depends On:** S1-04, S1-06

#### Context (read before starting)
- `modules/01-auth-and-roles/SCREENS.md` → User Management, Create/Edit User Form
- `shared/ACCESS-MATRIX.md` → CEO/CTO only for user management

#### Description
As a CEO/CTO, I want a user management page so that I can add, edit, and deactivate users.

#### Acceptance Criteria
- [ ] `/admin/users` — table: name, email, role, resource link, status badge, created date
- [ ] "Add User" button → `/admin/users/new`
- [ ] Status filter (Active/Inactive/All), search by name/email
- [ ] Click row → `/admin/users/:id/edit`
- [ ] Create form: name (required), email (required), password (required), role dropdown, resource link dropdown
- [ ] Edit form: same fields, password optional, active toggle
- [ ] Client-side validations match server rules
- [ ] Success toast + redirect to list on save
- [ ] Empty state: "No users found. Add your first user to get started."
- [ ] Only accessible to CEO/CTO (RoleGuard component)

---

### S1-08: Build Role Management screen with permission matrix
**Type:** Story | **Points:** 2 (S) | **Priority:** P2 — Major
**Labels:** `frontend`, `phase-1`, `nice-to-have`, `agentic`
**Depends On:** S1-05, S1-06

#### Context (read before starting)
- `modules/01-auth-and-roles/SCREENS.md` → Role Management screen

#### Description
As a CEO/CTO, I want to view the permission matrix per role so that I understand who can see what.

#### Acceptance Criteria
- [ ] `/admin/roles` — split layout: role list (left) + permission matrix (right)
- [ ] Role list: name, code, permission level for all 7 roles
- [ ] Click role → shows 15-row permission matrix
- [ ] Matrix columns: Data Type (label), Access Level (color-coded NONE/VIEW/EDIT), Scope, Configurable
- [ ] Edit permissions button present but disabled (Phase 3)
- [ ] Default state: "Select a role to view its permissions."
- [ ] CEO/CTO only

---

### S1-09: Write auth integration tests
**Type:** Story | **Points:** 3 (M) | **Priority:** P1 — Critical
**Labels:** `testing`, `backend`, `phase-1`, `must-have`, `agentic`
**Depends On:** S1-01 through S1-05

#### Context (read before starting)
- `modules/01-auth-and-roles/REQUIREMENTS.md` → all acceptance criteria
- `CLAUDE.md` → Testing Expectations section
- `techstack/backend.md` → Testing stack (pytest + pytest-asyncio)

#### Description
As a developer, I want comprehensive auth tests so that the security foundation is proven.

#### Acceptance Criteria
- [ ] `tests/conftest.py` — fixtures: test client, test DB, auth helper (login as any role)
- [ ] Login: valid creds → token + user; invalid → 401 generic; inactive → "Account is inactive"
- [ ] Logout: token invalidated, subsequent requests 401
- [ ] Token refresh: valid refresh → new access token; expired → 401
- [ ] GET /me: authenticated → profile; unauthenticated → 401
- [ ] User CRUD: create, read, update, deactivate happy paths
- [ ] User CRUD: non-CEO/CTO → 403
- [ ] Cannot deactivate last active admin
- [ ] Email uniqueness enforced
- [ ] RBAC middleware: NONE → 403 for each data_type/role combo (sample 5 combos minimum)
- [ ] RBAC middleware: OWN_PORTFOLIO scope filters correctly
- [ ] RBAC middleware: SELF_ONLY scope filters correctly
- [ ] Sensitive fields return null for unauthorized roles

---

## Sprint 1 Summary

| Story | Title | SP | Labels | Priority |
|-------|-------|---|--------|----------|
| S1-01 | Login/logout API | 3 | backend | P0 |
| S1-02 | Token refresh + /me | 2 | backend | P0 |
| S1-03 | RBAC middleware | 5 | backend | P0 |
| S1-04 | User CRUD API | 3 | backend | P1 |
| S1-05 | Role/Permission API | 2 | backend | P1 |
| S1-06 | Login screen UI | 2 | frontend | P0 |
| S1-07 | User management UI | 3 | frontend | P1 |
| S1-08 | Role management UI | 2 | frontend | P2 |
| S1-09 | Auth integration tests | 3 | testing | P1 |
| **Total** | | **25** | | |
