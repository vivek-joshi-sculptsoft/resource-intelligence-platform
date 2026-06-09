# Authentication & Authorization

## Auth Provider

**Custom-built** using python-jose (JWT) + argon2-cffi (password hashing).

Chosen over managed providers (Auth0, Cognito, Supabase Auth) because: this is an internal tool with email/password only, 30-40 users total, no social login, no SSO/SAML. A managed provider adds cost and vendor dependency for zero benefit here.

---

## Authentication Flow

### Login

```
POST /api/v1/auth/login
Body: { "email": "...", "password": "..." }

1. Look up User by email (must be is_active = true)
2. Verify password with argon2
3. Generate access token (15 min) + refresh token (7 days)
4. Set both as httpOnly, Secure, SameSite=Strict cookies
5. Return user profile (id, name, email, role code, resource_id)
```

### Token Refresh

```
POST /api/v1/auth/refresh
(Refresh token read from httpOnly cookie)

1. Validate refresh token signature and expiry
2. Look up user (must still be active)
3. Issue new access token (15 min)
4. Rotate refresh token (new 7-day token, old one invalidated)
5. Set new cookies
```

### Logout

```
POST /api/v1/auth/logout

1. Clear access + refresh cookies
2. Add refresh token to Redis blacklist (TTL = remaining lifetime)
```

---

## Token Strategy

| Token | Lifetime | Storage | Purpose |
|-------|----------|---------|---------|
| Access token | 15 minutes | httpOnly cookie | API authentication |
| Refresh token | 7 days | httpOnly cookie | Silent token renewal |

**JWT payload (access token):**
```json
{
  "sub": "user-uuid",
  "role": "CTO",
  "role_id": "role-uuid",
  "resource_id": "resource-uuid-or-null",
  "exp": 1720000000,
  "iat": 1719999100
}
```

**Why httpOnly cookies over localStorage:**
- XSS attacks cannot read httpOnly cookies
- Automatically sent with every request (no manual header management)
- SameSite=Strict prevents CSRF

---

## Authorization Model

**RBAC (Role-Based Access Control)** implemented via the `RolePermission` table.

### How It Works

1. Every API endpoint declares its `data_type` (e.g., `allocation`, `billing_rates`)
2. FastAPI dependency (`require_access`) reads the user's role from the JWT
3. Looks up `RolePermission` for `(role_id, data_type)`
4. Enforces:
   - `NONE` → HTTP 403
   - `VIEW` → read-only (blocks POST/PUT/DELETE)
   - `EDIT` → full access
5. Applies scope filtering:
   - `ALL` → no additional filter
   - `OWN_PORTFOLIO` → `WHERE project.dm_id = user.resource_id OR project.pm_id = user.resource_id`
   - `SELF_ONLY` → `WHERE resource_id = user.resource_id`
6. Sensitive fields (`loaded_cost_monthly`, `billing_rate`, margins) set to `null` in response for unauthorized roles

### Implementation

```python
# FastAPI dependency
def require_access(data_type: str, min_level: AccessLevel = AccessLevel.VIEW):
    async def checker(current_user: User = Depends(get_current_user), db = Depends(get_db)):
        permission = await get_permission(db, current_user.role_id, data_type)
        if permission.access_level.value < min_level.value:
            raise HTTPException(403, "Insufficient permissions")
        return permission  # includes scope for query filtering
    return Depends(checker)

# Usage in router
@router.get("/allocations")
async def list_allocations(
    permission = require_access("allocation"),
    db = Depends(get_db)
):
    query = apply_scope_filter(base_query, permission)
    ...
```

### Role Definitions (7 default)

| Role | Code | Permission Level |
|------|------|-----------------|
| CEO | CEO | 100 |
| CTO | CTO | 90 |
| Delivery Manager | DM | 70 |
| Project Manager | PM | 60 |
| Finance | FINANCE | 70 |
| HR | HR | 50 |
| Engineer | ENGINEER | 10 |

105 RolePermission rows seeded on first deploy (7 roles × 15 data types). Full matrix in `shared/ACCESS-MATRIX.md`.

---

## Session Management

- Access tokens are stateless (validated by signature + expiry)
- Refresh tokens tracked in Redis for rotation and blacklisting
- On password change: all existing refresh tokens for that user are invalidated
- On deactivation (`is_active = false`): next access token check fails (user lookup in middleware)

---

## Security Hardening

| Measure | Implementation |
|---------|---------------|
| Rate limiting | 10 req/min on `/auth/login` per IP (slowapi) |
| Account lockout | 5 failed attempts → 15-minute lockout (tracked in Redis) |
| Password hashing | argon2id with default parameters (19 MiB memory, 2 iterations) |
| CORS | Whitelist frontend origin only |
| HTTPS | Enforced via CloudFront + Nginx (redirect HTTP → HTTPS) |
| Cookie flags | httpOnly, Secure, SameSite=Strict |
| Token rotation | Refresh token rotated on every use; old token immediately invalidated |

---

## Password Policy

| Rule | Requirement |
|------|-------------|
| Minimum length | 8 characters |
| Complexity | At least 1 uppercase, 1 lowercase, 1 digit |
| Hashing algorithm | argon2id (via argon2-cffi) |
| Password in response | Never returned in any API response |
| Password in logs | Never logged |
| Reset flow | Admin resets password directly (internal tool — no self-service reset in Phase 1) |
