# Module 01: Auth & Roles — API Endpoints

## Endpoints

### POST /api/auth/login
**Description:** Authenticate with email + password. Returns session token.
**Auth:** Public (no token required)
**Scope:** N/A
**Request Body:**
```json
{ "email": "string", "password": "string" }
```
**Response:**
```json
{ "token": "string", "user": { "id", "name", "email", "role": { "code", "name" } } }
```
**Validations:** Email + password required. Inactive user blocked.
**Notes:** Returns generic 401 for any invalid credential — no field-level disclosure.

---

### POST /api/auth/logout
**Description:** Invalidate the current session / token.
**Auth:** Authenticated (any role)
**Scope:** N/A
**Response:** `{ "success": true }`

---

### GET /api/auth/me
**Description:** Returns authenticated user's profile and role.
**Auth:** Authenticated (any role)
**Scope:** SELF_ONLY
**Response:**
```json
{ "id", "name", "email", "role": { "id", "code", "name", "permission_level" }, "resource_id" }
```

---

### GET /api/users
**Description:** List all users with role info.
**Auth:** CEO, CTO only
**Scope:** ALL
**Response:** Paginated list. `?page=1&limit=20&status=ACTIVE`
**Notes:** Includes role name, is_active status.

---

### POST /api/users
**Description:** Create a new user.
**Auth:** CEO, CTO only
**Scope:** ALL
**Request Body:**
```json
{ "email": "string*", "name": "string*", "role_id": "uuid*", "resource_id": "uuid|null", "password": "string*" }
```
**Response:** Created user object.
**Validations:** Email unique. Role must exist. resource_id must exist if provided.

---

### GET /api/users/:id
**Description:** Get a specific user by ID.
**Auth:** CEO, CTO only
**Scope:** ALL
**Response:** Full user object with role.

---

### PUT /api/users/:id
**Description:** Update user's name, role, or resource link.
**Auth:** CEO, CTO only
**Scope:** ALL
**Request Body:** Any subset of `{ name, role_id, resource_id, is_active }`
**Validations:** Cannot deactivate last active admin. Email change must remain unique.
**Notes:** All changes audit logged.

---

### GET /api/roles
**Description:** List all roles with their permission matrices.
**Auth:** CEO, CTO only
**Scope:** ALL
**Response:** Array of roles each with nested array of 15 RolePermission rows.

---

### GET /api/roles/:id
**Description:** Get single role with full permission set.
**Auth:** CEO, CTO only
**Scope:** ALL
**Response:** Role + all 15 RolePermission rows.

---

### GET /api/roles/:id/permissions
**Description:** Get all 15 data-type permissions for a role.
**Auth:** CEO, CTO only
**Scope:** ALL
**Response:** Array of `{ data_type, access_level, scope, is_configurable }`.
