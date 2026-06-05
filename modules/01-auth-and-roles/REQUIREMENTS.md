# Module 01: Auth & Roles

## Overview

This module handles authentication, session management, user accounts, and role-based access control. It is the foundation all other modules depend on — it seeds the 7 default roles, 105 RolePermission rows, and the initial admin user. The access control middleware built here is used by every API endpoint in the system.

## Phase

Phase 1 — must be built first.

## Dependencies

None — this is the root module.

---

## Features

### Feature: Login / Logout
**Description:** Email + password authentication with session management. On successful login, returns a token (JWT or session) identifying the user and their role.
**Acceptance Criteria:**
- [ ] User can log in with valid email and password
- [ ] Login fails with a generic error for invalid credentials (no disclosure of which field is wrong)
- [ ] Logout invalidates the session / token
- [ ] Inactive users (`is_active = false`) cannot log in

### Feature: Current User Profile
**Description:** Authenticated users can retrieve their own profile including role and linked resource.
**Acceptance Criteria:**
- [ ] `GET /api/auth/me` returns user's id, name, email, role (code + name), resource_id
- [ ] Returns 401 if no valid session

### Feature: User Management (Admin)
**Description:** Admin (CEO/CTO) can create, update, and deactivate users.
**Acceptance Criteria:**
- [ ] Create user with email, name, role assignment, optional resource linkage
- [ ] Update user role or resource link
- [ ] Soft-delete user (`is_active = false`) — never hard delete
- [ ] Cannot delete or deactivate the last active admin user
- [ ] Email must be unique across all users

### Feature: Role Management (Admin)
**Description:** Admin can view roles and their permission matrices. Role permission editing is Phase 3.
**Acceptance Criteria:**
- [ ] List all roles with their codes and permission levels
- [ ] View a role's full RolePermission set (all 15 data types)

### Feature: Seed Data
**Description:** On first deployment, the system populates all default roles, permissions, and an admin user.
**Acceptance Criteria:**
- [ ] 7 roles seeded: CEO, CTO, DM, PM, FINANCE, HR, ENGINEER
- [ ] 105 RolePermission rows seeded (7 roles × 15 data types) per `shared/ACCESS-MATRIX.md`
- [ ] 7 SystemConfig keys seeded with default values per `CLAUDE.md` seed data section
- [ ] 1 admin user seeded with CEO role for initial access
- [ ] Seed is idempotent — safe to run multiple times

### Feature: Access Control Middleware
**Description:** Every API endpoint goes through the access control middleware that checks RolePermission before returning data.
**Acceptance Criteria:**
- [ ] Middleware reads `role_id` from authenticated session
- [ ] Looks up `RolePermission` for `role_id + data_type`
- [ ] Returns HTTP 403 for `access_level = NONE`
- [ ] Applies scope filter (`ALL`, `OWN_PORTFOLIO`, `SELF_ONLY`) as a WHERE clause
- [ ] Sensitive fields are set to `null` (not omitted) in responses for unauthorized roles
- [ ] All 15 data types handled

---

## Validations

From FSD §11 — no specific assignment/invoice validations apply to this module. General:

| Rule | Condition | Error |
|---|---|---|
| Email unique | Duplicate email on create/update | "Email is already in use" |
| Role required | No role assigned | "User must have a role" |
| Active user only | Login with `is_active = false` | "Account is inactive" |

---

## Business Rules

- Role permission levels: CEO=100, CTO=90, DM=70, PM=60, FINANCE=70, HR=50, ENGINEER=10
- Access check algorithm from `shared/ACCESS-MATRIX.md` — runtime check section
- Never hardcode role names — always query the Role table
