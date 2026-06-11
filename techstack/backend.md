# Backend — Python + FastAPI

## Language & Framework

**Python 3.12** with **FastAPI 0.115+**.

FastAPI was chosen for: automatic OpenAPI documentation, Pydantic v2 integration for request/response validation, native async support, and deep familiarity by Claude Code. Combined with SQLAlchemy 2.0's async sessions, it handles the full CRUD + RBAC + financial calculation workload efficiently.

---

## Architecture Pattern

**Modular monolith.** One FastAPI application, 13 modules as Python packages, one shared database. Modules are logically separated with clear import boundaries but deployed as a single process.

Two runtime processes:
1. **API server** — FastAPI via uvicorn (2 workers)
2. **Celery worker** — background jobs + celery-beat scheduler

Both share the same codebase and database connection.

---

## API Design

**REST** with consistent resource patterns. No GraphQL — the data model is straightforward CRUD with RBAC filtering.

| Convention | Pattern |
|------------|---------|
| List | `GET /api/v1/{entity}?page=1&limit=20&status=ACTIVE` |
| Detail | `GET /api/v1/{entity}/{id}` |
| Create | `POST /api/v1/{entity}` |
| Update | `PUT /api/v1/{entity}/{id}` |
| Soft Delete | `DELETE /api/v1/{entity}/{id}` |
| Nested | `GET /api/v1/projects/{id}/assignments` |

**Versioning:** URL-based (`/api/v1/`). Add `/api/v2/` only when breaking changes are unavoidable.

**Documentation:** FastAPI auto-generates OpenAPI 3.1 spec at `/docs` (Swagger UI) and `/redoc`.

**Response format:**
```json
// Success
{ "data": {...}, "meta": { "page": 1, "limit": 20, "total": 45 } }

// Error
{ "error": true, "message": "Email is already in use", "field": "email" }
```

---

## Key Libraries

| Category | Library | Purpose |
|----------|---------|---------|
| Framework | FastAPI | API framework |
| Server | uvicorn | ASGI server |
| ORM | SQLAlchemy 2.0 | Database ORM with async support |
| DB Driver (local) | aiosqlite | Async SQLite driver for local dev |
| DB Driver (prod) | asyncpg | Async PostgreSQL driver for production |
| Migrations | Alembic | Schema migrations (production only) |
| Validation | Pydantic v2 | Request/response schemas |
| Auth | python-jose | JWT encoding/decoding |
| Password | argon2-cffi | Password hashing (OWASP recommended) |
| Background | Celery 5.4 | Task queue and scheduling |
| Scheduler | celery-beat | Cron-like job scheduling |
| HTTP | httpx | Async HTTP client (for future integrations) |
| Testing | pytest + pytest-asyncio | Unit and integration tests |
| Coverage | pytest-cov | Test coverage reporting |
| Linting | ruff | Linting + formatting (replaces flake8, black, isort) |
| Type Check | mypy | Static type checking |
| CORS | FastAPI CORSMiddleware | Cross-origin requests from frontend |

---

## Project Structure

```
backend/
├── app/
│   ├── main.py                    # FastAPI app factory, middleware, router mount
│   ├── config.py                  # Settings from env vars (pydantic-settings)
│   ├── database.py                # SQLAlchemy engine, session factory
│   ├── dependencies.py            # Shared DI: get_db, get_current_user
│   ├── middleware/
│   │   ├── auth.py                # JWT validation middleware
│   │   └── rbac.py                # RolePermission check middleware
│   ├── modules/
│   │   ├── auth/
│   │   │   ├── __init__.py
│   │   │   ├── router.py          # /api/v1/auth/* endpoints
│   │   │   ├── service.py         # Login, token refresh, user CRUD logic
│   │   │   ├── schemas.py         # Pydantic request/response models
│   │   │   ├── models.py          # SQLAlchemy: Role, RolePermission, User
│   │   │   └── seed.py            # Seed 7 roles, 105 permissions, admin user
│   │   ├── clients/
│   │   │   ├── router.py
│   │   │   ├── service.py
│   │   │   ├── schemas.py
│   │   │   └── models.py
│   │   ├── projects/
│   │   ├── resources/
│   │   ├── allocations/
│   │   ├── utilization/
│   │   ├── financial/
│   │   ├── invoicing/
│   │   ├── nonhuman_costs/
│   │   ├── worklogs/
│   │   ├── alerts/
│   │   └── audit/
│   │       ├── models.py          # AuditLog model (append-only)
│   │       ├── service.py         # audit_log() helper used by all modules
│   │       └── router.py          # GET /api/v1/audit (read-only)
│   ├── shared/
│   │   ├── models.py              # Base model, UUID mixin, timestamp mixin
│   │   ├── schemas.py             # Pagination, error response, common types
│   │   ├── exceptions.py          # Custom HTTP exceptions
│   │   └── utils.py               # Currency conversion, date helpers
│   └── jobs/
│       ├── __init__.py
│       ├── celery_app.py          # Celery configuration
│       ├── auto_release.py        # Daily: release expired assignments
│       ├── alert_checks.py        # Contract expiry, bench, utilization alerts
│       └── recurring_costs.py     # Monthly: create entries for recurring costs
├── alembic/
│   ├── env.py
│   └── versions/                  # Migration files
├── tests/
│   ├── conftest.py                # Fixtures: test client, test DB, auth helpers
│   ├── test_auth/
│   ├── test_clients/
│   └── ...
├── alembic.ini
├── pyproject.toml                 # Dependencies, ruff config, pytest config
├── Dockerfile
└── .env.example
```

---

## Error Handling Strategy

Global exception handler in `main.py`:

```python
@app.exception_handler(AppException)
async def app_exception_handler(request, exc):
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": True, "message": exc.message, "field": exc.field}
    )
```

All business-logic errors raise `AppException` subclasses. Unhandled exceptions return 500 with a generic message (details in Sentry, not in the response).

---

## Background Job Worker

Celery with Redis broker. Jobs defined in `app/jobs/`.

| Job | Schedule | Module |
|-----|----------|--------|
| auto_release_assignments | Daily 00:00 IST | allocations |
| check_contract_expiry | Daily 06:00 IST | alerts |
| check_bench_duration | Daily 06:00 IST | alerts |
| check_milestone_overdue | Daily 06:00 IST | alerts |
| check_utilization_drop | Weekly Mon 06:00 IST | alerts |
| process_recurring_costs | Monthly 1st 00:00 IST | nonhuman_costs |

Retry policy: 3 retries with exponential backoff (10s, 60s, 300s). Failed jobs logged to Sentry.

---

## API Rate Limiting

`slowapi` library (built on `limits`):
- Default: 100 requests/minute per user
- Auth endpoints: 10 requests/minute per IP (brute-force protection)

At 20 concurrent users, rate limiting is precautionary — not a current bottleneck.

---

## Secrets Management

All secrets via environment variables. Never in code, never in git.

| Secret | Source |
|--------|--------|
| `DATABASE_URL` | RDS connection string |
| `REDIS_URL` | Redis connection string |
| `JWT_SECRET_KEY` | 256-bit random key for JWT signing |
| `JWT_REFRESH_SECRET_KEY` | Separate key for refresh tokens |
| `SENTRY_DSN` | Sentry project DSN |

Managed via `.env` locally, AWS Systems Manager Parameter Store in production.
