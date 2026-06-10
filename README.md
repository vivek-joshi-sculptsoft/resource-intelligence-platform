# Resource Intelligence & Project Economics Platform

An internal tool for an IT services company (~30-40 employees) to track resource allocations, project delivery, client billing, and financial margins. Replaces Google Sheets with a structured, role-based platform.

## Tech Stack

| Layer | Choice | Notes |
|---|---|---|
| Frontend | React 19 + Vite 6 | shadcn/ui, Tailwind CSS 4, React Router v7, TanStack Query v5, Zustand v5 |
| Backend | Python 3.12 + FastAPI | Pydantic v2, SQLAlchemy 2.0 async, Alembic, Celery 5.4 |
| Database | PostgreSQL 16 | UUID PKs, DECIMAL(15,2) for financials, soft delete |
| Cache / Broker | Redis 7 | Celery broker + API cache |
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
│   │   │   ├── auth/           # models, seed, schemas, service, router
│   │   │   └── audit/          # models, service (append-only audit log)
│   │   ├── shared/             # Base models, schemas, exceptions, utils
│   │   └── jobs/               # Celery app + tasks
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
├── docker-compose.dev.yml      # Local dev: api, celery, redis, postgres
├── .github/workflows/ci.yml    # CI pipeline
├── CLAUDE.md                   # Master build instructions
└── ROADMAP.md                  # Phase-wise build plan
```

## Quick Start

### Prerequisites

- Python 3.11+
- Node.js 22+
- Docker & Docker Compose

### Local Development

```bash
# Start infrastructure (PostgreSQL + Redis)
docker compose -f docker-compose.dev.yml up postgres redis -d

# Backend
cd backend
pip install -e ".[dev]"
python3 -m uvicorn app.main:app --reload --port 8000

# Frontend (new terminal)
cd frontend
npm install
npm run dev
```

- Backend: http://localhost:8000 (API docs at `/docs`)
- Frontend: http://localhost:5173

### Claude Code Commands

| Command | Description |
|---|---|
| `/dev-backend` | Start FastAPI dev server (port 8000, hot-reload) |
| `/dev-frontend` | Start Vite dev server (port 5173, HMR) |
| `/dev-infra` | Start PostgreSQL + Redis via Docker Compose |
| `/dev-all` | Start full stack (infra + backend + frontend) |
| `/test backend` | Run backend tests |
| `/test frontend` | Run frontend tests |
| `/test coverage` | Backend tests with coverage report |
| `/lint` | Run linters (ruff + tsc) |
| `/lint fix` | Auto-fix backend lint issues |

### Running Tests

```bash
# Backend (74 tests)
cd backend && python3 -m pytest tests/ -v

# Frontend
cd frontend && npx vitest run
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

### Phase 1 — Foundation & Visibility (Sprints 0–5)

- [x] Sprint 0: Bootstrap & DevOps (8 stories — backend scaffold, frontend scaffold, Docker, CI, auth schema, seed data, audit log, Celery)
- [ ] Sprint 1: Auth & Roles
- [ ] Sprint 2: Data Foundation (Resources + Clients)
- [ ] Sprint 3: Projects & Allocations BE
- [ ] Sprint 4: Projects & Allocations FE + Terraform IaC
- [ ] Sprint 5: Dashboards & Worklog

### Phase 2 — Financial Engine
### Phase 3 — Intelligence & Alerts

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
