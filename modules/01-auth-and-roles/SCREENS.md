# Module 01: Auth & Roles — Screen Specifications

## Screen: Login
**Route:** `/login`
**Audience:** All users (unauthenticated)
**Layout:** Centered card with logo, email/password fields, and login button.

### Components
- Email input field
- Password input field
- Login button
- Error message area (shown below form on failure)

### Data Displayed
- System name / logo
- Error message on invalid login

### Actions
- Submit login form → POST /api/auth/login → redirect to home dashboard on success
- Show generic error on failure (no field-level disclosure)

### Empty State
N/A — always shows the login form.

### Access Restrictions
Only accessible when unauthenticated. Authenticated users are redirected to their dashboard.

---

## Screen: User Management
**Route:** `/admin/users`
**Audience:** CEO, CTO
**Layout:** Full-width table with header action bar.

### Components
- User table: name, email, role, resource link, status (active/inactive), created date
- "Add User" button → opens create form
- Status filter dropdown (Active / Inactive / All)
- Search by name or email

### Data Displayed

| Field | Source | Notes |
|---|---|---|
| Name | User.name | |
| Email | User.email | |
| Role | Role.name (via role_id) | |
| Resource | Resource.name (via resource_id) | "—" if no resource linked |
| Status | User.is_active | Active / Inactive |
| Created | User.created_at | Formatted date |

### Actions
- Add User → modal/form → POST /api/users
- Click row → User edit form → PUT /api/users/:id
- Toggle active/inactive → PUT /api/users/:id `{ is_active: false/true }`

### Empty State
"No users found. Add your first user to get started."

### Access Restrictions
CEO and CTO only. Not visible to other roles.

---

## Screen: Create / Edit User Form
**Route:** `/admin/users/new` and `/admin/users/:id/edit`
**Audience:** CEO, CTO
**Layout:** Modal or dedicated form page.

### Components
- Name input (required)
- Email input (required, validated unique)
- Password input (required on create; optional on edit — blank = no change)
- Role dropdown (required) — populated from GET /api/roles
- Resource link dropdown (optional) — populated from active resources
- Active toggle (edit only)

### Actions
- Save → POST (create) or PUT (edit) → success toast + return to list
- Cancel → back to user list without saving

### Empty State
N/A.

### Access Restrictions
CEO and CTO only.

---

## Screen: Role Management
**Route:** `/admin/roles`
**Audience:** CEO, CTO
**Layout:** Role list on left, permission matrix on right.

### Components
- Role list: name, code, permission level
- Permission matrix table (read-only in Phase 1/2): 15 data types × access_level + scope + is_configurable
- Edit permissions (Phase 3 feature — disabled in earlier phases)

### Data Displayed

| Column | Notes |
|---|---|
| Data Type | Human-readable label |
| Access Level | NONE / VIEW / EDIT — color coded |
| Scope | ALL / OWN_PORTFOLIO / SELF_ONLY |
| Configurable | Yes / No |

### Actions
- Select role → update permission matrix display
- Edit permissions (Phase 3 only)

### Empty State
"Select a role to view its permissions."

### Access Restrictions
CEO and CTO only.

---

## Component: User Profile Dropdown
**Location:** App header — top-right user avatar/name area
**Audience:** All authenticated users
**Layout:** Clickable user profile area that opens a dropdown menu below it.

### Trigger
Click on the user avatar or name in the app header.

### Dropdown Contents
- User name (display only)
- User email (display only)
- User role (display only)
- Divider
- Logout action

### Actions
- Click user avatar/name → toggle dropdown open/close
- Click outside dropdown → close dropdown
- Click "Logout" → POST /api/auth/logout → redirect to /login

### Access Restrictions
Visible to all authenticated users. Dropdown shows the current user's own info only.
