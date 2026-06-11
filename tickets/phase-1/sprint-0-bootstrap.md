# Sprint 0 — Project Bootstrap & DevOps

**Goal:** Runnable empty project with CI/CD, Docker, database, seed data, and audit infrastructure.
**Capacity:** 22 SP | **Duration:** 1 week

---

## Epic: EP-0 — Project Bootstrap & DevOps

### S0-01: Scaffold FastAPI backend project structure
**Type:** Story | **Points:** 3 (M) | **Priority:** P0 — Blocker
**Labels:** `backend`, `devops`, `phase-1`, `must-have`, `agentic`
**Depends On:** None

#### Context (read before starting)
- `CLAUDE.md` → Repo Structure, Coding Conventions, Backend section
- `techstack/backend.md` → Project structure, libraries
- `techstack/main.md` → Architecture overview

#### Description
As a developer, I want a scaffolded FastAPI project so that I can start building modules immediately.

#### Acceptance Criteria
- [ ] `backend/` directory with structure matching `techstack/backend.md`
- [ ] `app/main.py` — FastAPI app factory with CORS, exception handler, router mounts
- [ ] `app/config.py` — pydantic-settings reading from env vars
- [ ] `app/database.py` — SQLAlchemy 2.0 async engine + session factory
- [ ] `app/dependencies.py` — `get_db` dependency
- [ ] `app/shared/models.py` — Base model with UUID mixin, timestamp mixin
- [ ] `app/shared/schemas.py` — Pagination, error response schemas
- [ ] `app/shared/exceptions.py` — AppException base class
- [ ] `app/modules/` — empty `__init__.py` per module folder (auth, clients, projects, resources, allocations, utilization, worklogs, audit)
- [ ] `pyproject.toml` with all dependencies from `techstack/backend.md`
- [ ] `.env.example` with placeholder values
- [ ] `GET /api/v1/health` returns 200

#### Out of Scope
- Module-specific code (just the skeleton)
- Docker setup (separate story)

---

### S0-02: Scaffold React + Vite frontend project structure
**Type:** Story | **Points:** 3 (M) | **Priority:** P0 — Blocker
**Labels:** `frontend`, `devops`, `phase-1`, `must-have`, `agentic`
**Depends On:** None

#### Context (read before starting)
- `CLAUDE.md` → Repo Structure, Frontend section
- `techstack/frontend.md` → Libraries, folder structure, vite config

#### Description
As a developer, I want a scaffolded React+Vite project so that I can start building module UIs.

#### Acceptance Criteria
- [ ] `frontend/` directory with structure matching `techstack/frontend.md`
- [ ] Vite 6 config with path aliases (`@/`), API proxy to localhost:8000
- [ ] Tailwind CSS 4 configured with `globals.css`
- [ ] shadcn/ui initialized with base components (Button, Input, Table, Card, Dialog, Toast)
- [ ] React Router v7 with root layout (`_layout.tsx`): sidebar placeholder + role bar placeholder
- [ ] TanStack Query provider configured in `App.tsx`
- [ ] Zustand store skeleton for auth (`modules/auth/store.ts`)
- [ ] Axios instance with interceptor for JWT refresh (`shared/lib/axios.ts`)
- [ ] TypeScript strict mode, ESLint, Prettier configured
- [ ] `npm run dev` starts dev server on port 5173
- [ ] `npm run build` produces `dist/` static output

#### Out of Scope
- Actual pages/screens (just the skeleton and shared infrastructure)

---

### S0-03: Docker Compose for local development
**Type:** Story | **Points:** 2 (S) | **Priority:** P0 — Blocker
**Labels:** `devops`, `phase-1`, `must-have`, `agentic`
**Depends On:** S0-01

#### Context (read before starting)
- `techstack/devops.md` → Docker Compose dev section
- `techstack/infra.md` → Container architecture

#### Description
As a developer, I want `docker-compose up` to boot the full backend stack locally.

#### Acceptance Criteria
- [ ] `docker-compose.dev.yml` with 4 services: api (FastAPI with hot-reload), celery-worker, redis, postgres
- [ ] PostgreSQL 16 container with `ri_platform` database
- [ ] Redis 7 container
- [ ] API container with volume mount for hot-reload
- [ ] Celery worker container with volume mount
- [ ] `backend/Dockerfile` — multi-stage build
- [ ] `docker-compose up` boots all services, API responds on port 8000
- [ ] `.env.example` has all required env vars documented

---

### S0-04: GitHub Actions CI pipeline
**Type:** Story | **Points:** 2 (S) | **Priority:** P1 — Critical
**Labels:** `devops`, `phase-1`, `must-have`, `agentic`
**Depends On:** S0-01, S0-02

#### Context (read before starting)
- `techstack/devops.md` → CI/CD pipeline section
- `.github/workflows/traceability-check.yml` — existing workflow (don't break it)

#### Description
As a developer, I want CI to lint and test on every push so that broken code is caught early.

#### Acceptance Criteria
- [ ] `.github/workflows/ci.yml` — triggers on push to main + PRs
- [ ] Stage 1 (Lint): ESLint + tsc for frontend, ruff + mypy for backend (parallel)
- [ ] Stage 2 (Test): vitest for frontend, pytest for backend with PostgreSQL service container (parallel)
- [ ] Stage 3 (Build): vite build + docker build (parallel, main branch only)
- [ ] CI passes on clean scaffold (no false failures)
- [ ] Existing traceability-check workflow unchanged

---

### S0-05: Create Auth database schema and migrations
**Type:** Story | **Points:** 3 (M) | **Priority:** P0 — Blocker
**Labels:** `database`, `backend`, `phase-1`, `must-have`, `agentic`
**Depends On:** S0-01, S0-03

#### Context (read before starting)
- `modules/01-auth-and-roles/SCHEMA.md` — exact field definitions
- `shared/ENTITIES.md` → Role, RolePermission, User, SystemConfig
- `CLAUDE.md` → Database conventions (UUID PKs, timestamps, soft delete)

#### Description
As a developer, I want the auth tables in the database so that I can build login and RBAC.

#### Acceptance Criteria
- [ ] Alembic initialized in `backend/alembic/`
- [ ] Migration creates `roles` table: id (UUID PK), name (UNIQUE), code (UNIQUE), permission_level (INT), is_active, created_at, updated_at
- [ ] Migration creates `role_permissions` table: id (UUID PK), role_id (FK), data_type (STRING), access_level (ENUM: NONE/VIEW/EDIT), scope (ENUM: ALL/OWN_PORTFOLIO/SELF_ONLY), is_configurable (BOOL), unique constraint on (role_id, data_type)
- [ ] Migration creates `users` table: id (UUID PK), email (UNIQUE), name, password_hash, role_id (FK), resource_id (FK nullable), is_active, created_at, updated_at
- [ ] Migration creates `system_config` table: id (UUID PK), key (UNIQUE), value, description, created_at, updated_at
- [ ] SQLAlchemy models in `app/modules/auth/models.py`
- [ ] All FKs indexed
- [ ] Migration is reversible (up/down)
- [ ] `alembic upgrade head` runs successfully against Docker PostgreSQL

---

### S0-06: Create seed script for roles, permissions, config, and admin user
**Type:** Story | **Points:** 2 (S) | **Priority:** P0 — Blocker
**Labels:** `database`, `backend`, `phase-1`, `must-have`, `agentic`
**Depends On:** S0-05

#### Context (read before starting)
- `shared/ACCESS-MATRIX.md` — full 7×15 permission matrix
- `modules/01-auth-and-roles/REQUIREMENTS.md` → Seed Data section
- `CLAUDE.md` → Seed Data section

#### Description
As a developer, I want seed data so that the system is functional on first boot.

#### Acceptance Criteria
- [ ] `app/modules/auth/seed.py` — callable function
- [ ] 7 roles seeded: CEO(100), CTO(90), DM(70), PM(60), FINANCE(70), HR(50), ENGINEER(10)
- [ ] 105 RolePermission rows per `shared/ACCESS-MATRIX.md` exactly
- [ ] 7 SystemConfig keys: alert.contract_expiry_days=30, alert.contract_expiry_urgent_days=7, alert.bench_threshold_days=7, alert.utilization_threshold_pct=70, system.working_days_per_month=22, system.working_hours_per_day=8, system.default_currency=INR
- [ ] 1 admin user (CEO role) with argon2 hashed password
- [ ] Idempotent — re-run doesn't duplicate
- [ ] Runs as part of Docker entrypoint after migrations

---

### S0-07: Create AuditLog table and logging wrapper
**Type:** Story | **Points:** 3 (M) | **Priority:** P0 — Blocker
**Labels:** `database`, `backend`, `phase-1`, `must-have`, `agentic`
**Depends On:** S0-05

#### Context (read before starting)
- `modules/13-audit-history/SCHEMA.md` — AuditLog fields
- `shared/ENTITIES.md` → AuditLog entity
- `CLAUDE.md` → Audit Logging section

#### Description
As a developer, I want an audit logging wrapper so that all modules can log changes from day one.

#### Acceptance Criteria
- [ ] Migration creates `audit_logs` table: id (UUID PK), entity_type (STRING), entity_id (UUID), action (ENUM: CREATE/UPDATE/DELETE), field_name (STRING nullable), old_value (TEXT nullable), new_value (TEXT nullable), changed_by (UUID FK to users), changed_at (TIMESTAMP), metadata (JSONB nullable)
- [ ] Table is append-only — no UPDATE or DELETE allowed (enforced at app level)
- [ ] Index on (entity_type, entity_id) and changed_at
- [ ] `app/modules/audit/service.py` — `audit_log(db, entity_type, entity_id, action, changes, user_id)` function
- [ ] For UPDATE: creates one row per changed field with old_value + new_value
- [ ] old_value and new_value stored as JSON-serialized strings
- [ ] Wrapper is importable by all modules: `from app.modules.audit.service import audit_log`

---

### S0-08: Celery + Redis job infrastructure setup
**Type:** Story | **Points:** 2 (S) | **Priority:** P1 — Critical
**Labels:** `backend`, `devops`, `phase-1`, `must-have`, `agentic`
**Depends On:** S0-01, S0-03

#### Context (read before starting)
- `techstack/backend.md` → Background Job Worker section
- `techstack/decisions/007-background-jobs.md` — Celery rationale

#### Description
As a developer, I want Celery configured so that scheduled jobs work when modules need them.

#### Acceptance Criteria
- [ ] `app/jobs/celery_app.py` — Celery app configured with Redis broker
- [ ] celery-beat scheduler configured (empty schedule, ready for jobs)
- [ ] Celery worker starts in Docker Compose and connects to Redis
- [ ] Health check: test task `ping.delay()` returns `pong`
- [ ] Retry policy configured: 3 retries with exponential backoff (10s, 60s, 300s)
- [ ] Sentry integration for failed tasks (placeholder DSN)

---

### S0-09: SQLite support for local development
**Type:** Story | **Points:** 2 (S) | **Priority:** P1 — Critical
**Labels:** `backend`, `devops`, `database`, `phase-1`, `must-have`, `agentic`
**Depends On:** S0-01, S0-05

#### Context (read before starting)
- `techstack/database.md` → Local Development — SQLite section
- `techstack/backend.md` → Key Libraries (aiosqlite)
- `techstack/devops.md` → Local Development → Quick Start section
- `CLAUDE.md` → Database conventions

#### Description
As a developer, I want the backend to default to SQLite locally so that I can run the API without Docker or PostgreSQL.

#### Acceptance Criteria
- [ ] `aiosqlite>=0.20.0` added to `pyproject.toml` and installed
- [ ] `app/config.py` — `DATABASE_URL` defaults to `sqlite+aiosqlite:///./ri_platform.db` when env var not set
- [ ] `app/database.py` — detects SQLite vs PostgreSQL URL, applies correct engine kwargs (no pool for SQLite, `check_same_thread=False`)
- [ ] `app/database.py` — exposes `create_tables()` helper for SQLite auto-schema creation
- [ ] `app/main.py` — calls `create_tables()` on startup when using SQLite
- [ ] All SQLAlchemy models use `sqlalchemy.Uuid` instead of `sqlalchemy.dialects.postgresql.UUID`
- [ ] All SQLAlchemy models use `sqlalchemy.JSON` instead of `sqlalchemy.dialects.postgresql.JSONB`
- [ ] `*.db` in `.gitignore` — SQLite file never committed
- [ ] Alembic migrations remain PostgreSQL-specific (production only)
- [ ] `python -m uvicorn app.main:app --reload` starts successfully with SQLite (no env vars needed)
- [ ] Existing tests pass with SQLite backend
- [ ] Health check endpoint returns 200 on SQLite

#### Out of Scope
- Celery/Redis (still requires Docker for background jobs)
- Migration auto-generation for SQLite

---

## Sprint 0 Summary

| Story | Title | SP | Labels |
|-------|-------|---|--------|
| S0-01 | Scaffold FastAPI backend | 3 | backend, devops |
| S0-02 | Scaffold React+Vite frontend | 3 | frontend, devops |
| S0-03 | Docker Compose local dev | 2 | devops |
| S0-04 | GitHub Actions CI | 2 | devops |
| S0-05 | Auth database schema | 3 | database, backend |
| S0-06 | Seed script | 2 | database, backend |
| S0-07 | AuditLog table + wrapper | 3 | database, backend |
| S0-08 | Celery + Redis setup | 2 | backend, devops |
| S0-09 | SQLite local dev support | 2 | backend, devops, database |
| **Total** | | **22** | |
