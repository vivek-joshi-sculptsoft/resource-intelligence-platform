# SculptNexus

Resource Intelligence & Project Economics Platform — an internal tool for an IT services company (~30-40 employees) to track resource allocations, project delivery, client billing, and financial margins. Replaces Google Sheets with a structured, role-based platform.

## Tech Stack

| Layer | Choice | Notes |
|---|---|---|
| Frontend | React 19 + Vite 6 | shadcn/ui, Tailwind CSS 4, React Router v7, TanStack Query v5, Zustand v5 |
| Backend | Python 3.12 + FastAPI | Pydantic v2, SQLAlchemy 2.0 async, Alembic |
| Database | PostgreSQL 16 | UUID PKs, DECIMAL(15,2) for financials, soft delete |
| Background Jobs | APScheduler (default) or Celery 5.4 | `SCHEDULER_BACKEND` env var — APScheduler runs in-process, no Redis needed |
| Cache / Broker | Redis 7 (optional) | Only needed when `SCHEDULER_BACKEND=celery` |
| Auth | Custom JWT | argon2 password hashing, httpOnly cookies, 15min access + 7d refresh tokens |
| Hosting | AWS (EC2 + RDS + S3/CloudFront) | ap-south-1 (Mumbai), ~$36/mo |
| CI/CD | GitHub Actions | Lint → Test → Build → Deploy |

## Repo Structure

```
project/
├── backend/                    # Python + FastAPI
│   ├── app/
│   │   ├── main.py             # FastAPI app factory
│   │   ├── config.py           # pydantic-settings
│   │   ├── database.py         # SQLAlchemy async engine + session
│   │   ├── dependencies.py     # get_db, get_current_user
│   │   ├── modules/            # One package per module
│   │   │   ├── auth/           # JWT auth, roles, users
│   │   │   ├── clients/        # Client CRUD
│   │   │   ├── projects/       # Project lifecycle + transitions
│   │   │   ├── resources/      # Resource profiles + tags
│   │   │   ├── allocations/    # Assignments + auto-release job
│   │   │   ├── utilization/    # Dashboard APIs (company, DM, availability)
│   │   │   ├── worklogs/       # Daily worklog CRUD
│   │   │   └── audit/          # Append-only audit log
│   │   ├── shared/             # Base models, schemas, exceptions, utils
│   │   └── jobs/               # scheduler.py (APScheduler) + celery_app.py (Celery), both configurable via SCHEDULER_BACKEND
│   ├── alembic/                # Database migrations
│   ├── tests/                  # pytest test suites
│   ├── pyproject.toml
│   └── Dockerfile
├── frontend/                   # React 19 + Vite 6
│   ├── src/
│   │   ├── app/                # Routes, App.tsx, RootLayout
│   │   ├── modules/            # Feature modules (auth, etc.)
│   │   └── shared/             # Reusable components, hooks, constants
│   ├── package.json
│   └── vite.config.ts
├── prd/PRD.md                  # Product requirements
├── fsd/FSD.md                  # Functional specifications
├── shared/                     # Cross-cutting references
│   ├── ENTITIES.md             # Master entity definitions (14 entities)
│   ├── BUSINESS-RULES.md       # Formulas, calculations, constraints
│   ├── ACCESS-MATRIX.md        # 7 roles × 15 data types
│   └── GLOSSARY.md             # Term definitions
├── modules/                    # Module-wise specs (13 modules)
├── techstack/                  # Architecture decisions and stack docs
├── tickets/                    # JIRA-ready story breakdowns
├── docker-compose.dev.yml      # Local dev: api, postgres (+ optional celery-worker, redis via `--profile celery`)
├── .github/workflows/ci.yml    # CI pipeline
├── CLAUDE.md                   # Master build instructions
└── ROADMAP.md                  # Phase-wise build plan
```

## Quick Start

### Prerequisites

- Python 3.11+
- Node.js 22+
- Docker & Docker Compose

### Local Development (no Docker needed)

```bash
# Backend — uses SQLite by default
cd backend
pip install -e ".[dev]"
python3 -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Frontend (new terminal) — proxies API to :8000
cd frontend
npm install
npm run dev
```

- Backend: http://localhost:8000 (API docs at `/docs`)
- Frontend: http://localhost:5173

### Full Stack (Docker)

```bash
docker compose -f docker-compose.dev.yml up postgres -d         # infra
cd backend && python3 -m uvicorn app.main:app --reload          # API (APScheduler runs in-process by default)
cd frontend && npm run dev                                       # UI
```

- PostgreSQL: `localhost:5432` (ri_platform / dev / dev)

**Using Celery instead of APScheduler:** set `SCHEDULER_BACKEND=celery` in `backend/.env`, then start Redis and the worker via the `celery` Compose profile:

```bash
docker compose -f docker-compose.dev.yml --profile celery up redis celery-worker -d
cd backend && celery -A app.jobs.celery_app beat -l info   # separate terminal, if scheduled jobs are needed
```

- Redis: `localhost:6379` (only running when the `celery` profile is active)

### Claude Code Commands

| Command | Description |
|---|---|
| `/dev-backend` | Start FastAPI dev server (port 8000, hot-reload) |
| `/dev-frontend` | Start Vite dev server (port 5173, HMR) |
| `/dev-infra` | Start PostgreSQL via Docker Compose (add `redis` only if testing the Celery backend) |
| `/dev-all` | Start full stack (infra + backend + frontend) |
| `/test backend` | Run backend tests |
| `/test frontend` | Run frontend tests |
| `/test coverage` | Backend tests with coverage report |
| `/lint` | Run linters (ruff + tsc) |
| `/lint fix` | Auto-fix backend lint issues |

### Running Tests

```bash
# Backend (377 tests)
cd backend && python -m pytest

# Frontend
cd frontend && npx vitest run

# E2E (Playwright)
cd e2e && npx playwright test --project=smoke       # Smoke only
cd e2e && npx playwright test                        # All tiers
```

## Modules

| # | Module | Phase | Key Entities | Description |
|---|---|---|---|---|
| 01 | auth-and-roles | 1 | Role, RolePermission, User | Authentication, authorization, role management |
| 02 | client-management | 1 | Client | Client CRUD and portfolio tracking |
| 03 | project-management | 1 | Project | Project lifecycle (FP/T&M/Onboarding) |
| 04 | resource-management | 1 | Resource, ResourceTag | Employee profiles, skills, designations |
| 05 | allocation-tracking | 1 | Assignment | Resource-to-project assignments with auto-release |
| 06 | non-human-costs | 2 | NonHumanCost | Software, infrastructure, and travel costs |
| 07 | utilization-dashboards | 1+2 | — | Company/DM/client/project/resource dashboards |
| 08 | financial-engine | 2 | — | Cost, revenue, and margin calculations |
| 09 | invoicing | 2 | Milestone, Invoice | Milestone tracking and invoice lifecycle |
| 10 | bench-forecasting | 2 | — | Bench tracking and availability projections |
| 11 | worklog | 1 | Worklog | Daily hour logging per project |
| 12 | alerts | 3 | Alert, SystemConfig | Proactive alerts and system configuration |
| 13 | audit-history | 1+3 | AuditLog | Append-only audit trail |

## User Roles

| Role | Level | Primary Responsibility |
|---|---|---|
| CEO | 100 | Full visibility, strategic decisions |
| CTO | 90 | Technical oversight, resource costs, utilization |
| Delivery Manager (DM) | 70 | Portfolio management, resource allocation |
| Project Manager (PM) | 60 | Project execution, assignments, worklogs |
| Finance | 70 | Billing, invoicing, cost tracking |
| HR | 50 | Resource onboarding, bench tracking |
| Engineer | 10 | Own profile, assignments, worklogs |

## Build Progress

### Phase 1 — Foundation & Visibility (Sprints 0–5) ✅ Complete

- [x] Sprint 0: Bootstrap & DevOps — repo scaffold, Docker, CI, auth schema, seed data, Celery
- [x] Sprint 1: Auth & Roles — login/logout, JWT, user CRUD, role management, protected routes
- [x] Sprint 2: Data Foundation — Resource CRUD + tags, Client CRUD, access control, 31 tests
- [x] Sprint 3: Projects & Allocations BE — Project CRUD + transitions, Assignment CRUD + auto-release
- [x] Sprint 4: Projects & Allocations FE — Project list/detail/form, Assignment UI, My Assignments
- [x] Sprint 5: Dashboards & Worklog — Company/DM/Availability dashboards, Worklog CRUD + UI, E2E smoke tests

**46 API endpoints | 377 backend tests | 7 roles × 15 data types access matrix**

### Phase 2 — Financial Engine (upcoming)
### Phase 3 — Intelligence & Alerts (upcoming)

## Key Documents

| Document | Purpose |
|---|---|
| `prd/PRD.md` | Business requirements — the "why" |
| `fsd/FSD.md` | Technical specifications — the "how" |
| `shared/ENTITIES.md` | All 14 entity definitions |
| `shared/BUSINESS-RULES.md` | Formulas and calculations |
| `shared/ACCESS-MATRIX.md` | Who sees what |
| `CLAUDE.md` | Build instructions and conventions |
| `ROADMAP.md` | Build plan and estimates |
| `techstack/main.md` | Architecture overview and stack decisions |
