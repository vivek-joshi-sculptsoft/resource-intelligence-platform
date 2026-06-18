# CLAUDE.md — Master Instructions for Claude Code
## Behavior

Enable /caveman skills if available before any conversation but not if it is explicitely asked for disabling it.

## Project Overview

You are building a **Resource Intelligence & Project Economics Platform** — an internal tool for an IT services company (~30-40 employees) to track resource allocations, project delivery, client billing, and financial margins. It replaces Google Sheets.

**Read these files first before writing any code:**
1. `prd/PRD.md` — What the product does (business perspective)
2. `fsd/FSD.md` — How the system works (technical specifications)
3. `shared/ENTITIES.md` — Master entity definitions (single source of truth for all field types, constraints, relationships)
4. `shared/BUSINESS-RULES.md` — Canonical calculations, formulas, and rules
5. `shared/ACCESS-MATRIX.md` — Role-based access control rules
6. This file — Build conventions and module structure

---

## Tech Stack

> **Decided 2026-06-09. Full details in `techstack/main.md` and per-layer docs.**

| Layer | Choice | Notes |
|---|---|---|
| Frontend | React 19 + Vite 6 | shadcn/ui + Tailwind CSS, React Router v7, TanStack Query + Zustand |
| Backend | Python 3.12 + FastAPI | Pydantic v2, SQLAlchemy 2.0 + Alembic, uvicorn |
| Database | PostgreSQL 16 (prod/Docker) / SQLite (local dev) | UUID PKs, DECIMAL(15,2) for financials |
| Cache / Broker | Redis 7 (Docker on EC2) | Celery broker + API cache |
| Background Jobs | Celery 5.4 + celery-beat | 6 scheduled jobs (auto-release, alerts, recurring costs) |
| Auth | Custom JWT (python-jose + argon2) | httpOnly cookies, 15min access + 7d refresh tokens |
| Hosting | AWS (EC2 t3.small + RDS + S3/CloudFront) | Docker Compose, ap-south-1 (Mumbai), ~$36/mo |
| CI/CD | GitHub Actions | `ci.yml` (Lint → Test → Build → Deploy), `traceability-check.yml` |
| Monitoring | Sentry + CloudWatch | Error tracking + infra metrics |
| Local Dev | SQLite + uvicorn (no Docker needed) | `DATABASE_URL` defaults to `sqlite+aiosqlite:///./ri_platform.db` |

See `techstack/decisions/` for Architecture Decision Records (8 ADRs) explaining the reasoning behind each choice.

---

## Repo Structure

Monorepo — backend and frontend live alongside specs in one repository.

```
project/
├── backend/                          # Python + FastAPI (see techstack/backend.md)
│   ├── app/
│   │   ├── main.py                   # FastAPI app factory
│   │   ├── config.py                 # pydantic-settings (SQLite default for local dev)
│   │   ├── database.py               # SQLAlchemy async engine + session
│   │   ├── dependencies.py           # get_db, get_current_user
│   │   ├── middleware/               # (empty — auth/rbac to be built in Sprint 1)
│   │   ├── modules/                  # One package per module
│   │   │   ├── auth/                 # models.py, seed.py (Sprint 0 scaffold)
│   │   │   ├── clients/
│   │   │   ├── projects/
│   │   │   ├── resources/
│   │   │   ├── allocations/
│   │   │   ├── utilization/
│   │   │   ├── worklogs/
│   │   │   ├── audit/
│   │   │   ├── financial/
│   │   │   ├── invoicing/
│   │   │   └── nonhuman_costs/
│   │   ├── shared/                   # Base models, schemas, exceptions, utils
│   │   └── jobs/                     # Celery app + tasks
│   ├── alembic/                      # Database migrations
│   ├── tests/                        # pytest test suites
│   ├── pyproject.toml
│   ├── Dockerfile
│   └── .env.example
├── e2e/                              # Playwright E2E tests (ticket-wise, sprint-organized)
│   ├── playwright.config.ts          # Config: webServer auto-starts BE+FE, smoke project
│   ├── fixtures/auth.ts              # loginAs(role) fixture for all 7 roles
│   ├── utils/                        # API helpers, constants
│   └── tests/sprint-N/              # VRIP-XX-slug.spec.ts — one file per Jira ticket
├── frontend/                         # React 19 + Vite 6 (see techstack/frontend.md)
│   ├── src/
│   │   ├── app/                      # App.tsx + routes/ (file-based routing)
│   │   ├── modules/                  # Feature modules (auth, clients, projects, etc.)
│   │   ├── shared/                   # components, hooks, lib, constants, types
│   │   └── styles/                   # globals.css
│   ├── package.json
│   ├── vite.config.ts
│   └── vitest.config.ts
├── prd/PRD.md                        # Product requirements (read-only reference)
├── fsd/FSD.md                        # Functional specs (read-only reference)
├── shared/                           # Cross-cutting references
│   ├── ENTITIES.md                   # Master entity definitions
│   ├── BUSINESS-RULES.md             # Formulas, calculations, constraints
│   ├── ACCESS-MATRIX.md              # Who sees/edits what
│   ├── GLOSSARY.md                   # Term definitions
│   └── TRACEABILITY.yaml             # Requirement-to-ticket traceability matrix
├── modules/                          # Module-wise specifications (13 modules)
│   └── {NN}-{module-name}/
│       ├── REQUIREMENTS.md           # What this module does + acceptance criteria
│       ├── SCHEMA.md                 # Entity fields for this module
│       ├── API.md                    # Endpoints
│       ├── SCREENS.md               # UI views and components
│       ├── DEPENDENCIES.md          # Upstream and downstream module dependencies
│       ├── JOBS.md                  # Background jobs (only if module has any)
│       └── mockups/                 # Interactive HTML mockups per screen (all 13 modules have these)
├── techstack/                        # Architecture decisions and stack docs
│   └── decisions/                    # 8 ADRs (001–008)
├── tickets/                          # JIRA-ready story breakdowns
│   └── phase-1/
│       ├── OVERVIEW.md               # Phase 1 sprint plan summary
│       ├── sprint-0-bootstrap.md
│       ├── sprint-1-auth.md
│       ├── sprint-2-data-foundation.md
│       ├── sprint-3-projects-allocations-be.md
│       ├── sprint-4-projects-allocations-fe.md
│       └── sprint-5-dashboards-worklog.md
├── scripts/                          # Utility scripts
│   └── check-traceability.py         # CI traceability check
├── mockups/                          # Theme selection previews (root-level)
│   ├── index.html                    # Review page for theme options
│   └── theme-preview-A/B/C.html      # Theme candidates (selected theme applied to module mockups)
├── submodules/                       # Git submodules
│   └── agentic-sdlc-skills-agents/   # Shared skills & agent definitions
├── .github/workflows/                # CI pipelines
│   ├── ci.yml                        # Lint → Test → Build → Deploy
│   └── traceability-check.yml        # Requirement coverage gate
├── .claude/                          # Claude Code config (commands, settings)
├── docker-compose.dev.yml            # Full stack: api, celery-worker, redis, postgres (no celery-beat yet)
├── CLAUDE.md                         # This file
├── ROADMAP.md                        # Phase-wise build plan with estimates
├── SPRINT-PLAN.md                    # Sprint breakdown with JIRA mappings
└── README.md                         # Project overview and setup guide
```

---

## Build Phases & Module Order

### Phase 1 — Foundation & Visibility
Build in this exact order (each module depends on the previous):

| Order | Module | Depends On | Key Entities |
|---|---|---|---|
| 1 | `01-auth-and-roles` | Nothing | Role, RolePermission, User |
| 2 | `04-resource-management` | Auth | Resource, ResourceTag |
| 3 | `02-client-management` | Auth | Client |
| 4 | `03-project-management` | Auth, Client, Resource | Project |
| 5 | `05-allocation-tracking` | Project, Resource | Assignment (core — without billing_rate) |
| 6 | `07-utilization-dashboards` | Assignment, Resource, Project | No new entities — reads from existing |
| 7 | `11-worklog` | Assignment, Project | Worklog |
| 8 | `13-audit-history` | All above | AuditLog |

### Phase 2 — Financial Engine
| Order | Module | Depends On | Key Entities |
|---|---|---|---|
| 9 | `08-financial-engine` | Resource, Assignment | Add: loaded_cost_monthly, billing_rate |
| 10 | `06-non-human-costs` | Project | NonHumanCost |
| 11 | `09-invoicing` | Project, Milestone | Milestone, Invoice |
| 12 | `10-bench-forecasting` | Resource, Assignment | No new entities — reads + computes |
| 13 | `07-utilization-dashboards` | Update | Add financial widgets to existing dashboards |

### Phase 3 — Intelligence & Alerts
| Order | Module | Depends On | Key Entities |
|---|---|---|---|
| 14 | `12-alerts` | All above | Alert, SystemConfig (full) |
| 15 | `13-audit-history` | Update | Add historical query UI, point-in-time reconstruction |
| 16 | Role-based access config UI | RolePermission | UserPermissionOverride (optional) |

---

## Current Build Status

> **Update this section as sprints complete.**

| Sprint | Status | What Was Built |
|---|---|---|
| Sprint 0 — Bootstrap | **Done** | Repo scaffold, backend/frontend project setup, Docker Compose, CI workflows, SQLite local dev, auth models + seed, shared base models/schemas/exceptions, traceability pipeline, JIRA tickets (80 issues) |
| Sprint 1 — Auth & Roles | **Done** | Login/logout, JWT auth, user CRUD, role management, protected routes, sidebar layout |
| Sprint 2 — Data Foundation | **Done** | Resource CRUD + access control + tags, Client CRUD + access control, shared access control utility, 31 integration tests, Resource List/Profile/Form UI, Client List/Detail/Form UI |
| Sprint 3 — Projects & Allocations BE | **Done** | Project CRUD + status transitions, Assignment CRUD + release + auto-release job, portfolio scoping (DM/PM), audit logging, 100+ tests |
| Sprint 4 — Projects & Allocations FE | **Done** | Project list/detail/form/edit, Assignment list/form/modal, My Assignments page (engineer), status transition UI, all mockup-matched |
| Sprint 5 — Dashboards & Worklog | **Done** | Company/DM/Availability dashboard APIs + UIs, Worklog model + CRUD API + validation, Worklog entry UI + project detail tab, E2E smoke tests (13), Phase 1 hardening |

**JIRA project:** VRIP on sspl-organisation.atlassian.net (80 issues, 10 epics).

---

## Coding Conventions

### General
- Backend: Python with type hints everywhere (FastAPI + Pydantic enforce this)
- Frontend: TypeScript strict mode
- Every function that touches business logic must reference the FSD section number in a comment: `# See FSD §7.3 — Projected Revenue` (Python) / `// See FSD §7.3 — Projected Revenue` (TS)
- No hardcoded magic numbers — use SystemConfig entity or environment variables
- All monetary calculations use the exact formulas from `shared/BUSINESS-RULES.md`

### Database
- Use UUID v4 for all primary keys (stored as CHAR(36) in SQLite, native UUID in Postgres)
- All tables have `created_at TIMESTAMP DEFAULT NOW()` and `updated_at TIMESTAMP`
- Soft delete via `is_active BOOLEAN DEFAULT true` — never hard delete user-facing entities
- AuditLog is append-only — no UPDATE or DELETE on this table ever
- Use database-level constraints for ENUMs, foreign keys, and unique constraints
- Index all foreign keys and status fields
- Local dev uses SQLite (auto-detected in `database.py`); Docker/prod uses PostgreSQL 16
- Write SQLAlchemy models that work on both — avoid Postgres-only syntax in models

### API
- RESTful endpoints following: `GET /api/{entity}`, `POST /api/{entity}`, `PUT /api/{entity}/:id`, `DELETE /api/{entity}/:id`
- Every endpoint must check access control via RolePermission before returning data
- Sensitive fields (loaded_cost_monthly, billing_rate, margins) must return `null` for unauthorized roles — not omit the field (keeps response shape consistent)
- All list endpoints support pagination: `?page=1&limit=20`
- All list endpoints support filtering by status: `?status=ACTIVE`
- Return consistent error format: `{ error: true, message: "...", field: "..." }`

### Frontend
- Component-per-feature: each module has its own component directory
- Use the SCREENS.md in each module folder as the component spec
- All monetary displays show INR by default with original currency in parentheses where applicable
- All percentage inputs are whole numbers (60, not 0.60)
- All tables support column sorting and at minimum status filtering
- Empty states must show a helpful message, not a blank screen
- Form validations must match FSD §11 exactly — same conditions, same error messages

### Access Control Implementation
- Middleware/decorator checks `RolePermission` table on every API call
- Read the `shared/ACCESS-MATRIX.md` for exact rules
- Scope filtering (ALL, OWN_PORTFOLIO, SELF_ONLY) is applied as a WHERE clause at the database query level, not post-fetch filtering
- Field-level restrictions: set restricted fields to `null` in the API response serializer

### Audit Logging
- Wrap all CREATE/UPDATE/DELETE operations in an audit-aware function
- Capture: entity_type, entity_id, action, field_name, old_value, new_value, changed_by, changed_at
- For UPDATE: log one row per changed field, not one row per save
- old_value and new_value are stored as JSON-serialized strings

---

## Implementation Workflow — Jira First

**When asked to implement any ticket, always invoke the `/implement-ticket` skill.** Do not implement tickets manually. The skill handles the full workflow: Jira fetch → context extraction → planning → implementation.

If for any reason the skill is unavailable, follow this fallback sequence:

1. **Fetch the Jira ticket** — Use Atlassian MCP (`getJiraIssue`) with the ticket key (e.g. VRIP-23). Read the full description including the context section.
2. **Extract implementation pointers** — The ticket description contains: mockup paths, module references, acceptance criteria, and dependencies.
3. **Read local files referenced by the ticket** — Open the mockup HTML, SCHEMA.md, API.md, SCREENS.md, etc. as pointed to by the ticket.
4. **Plan implementation** — Based on the Jira ticket + local files, plan the work.
5. **Implement** — Follow the module build steps below.

**Sprint and ticket context always comes from Jira, not from local `tickets/` files.** The local `tickets/phase-1/sprint-*.md` files are for Jira ticket creation only — never use them as implementation source.

---

## How to Build a Module

When I say "build module X" or you're working on a module folder, follow this process:

### Step 1: Read the Module Files
```
modules/{module-name}/
├── REQUIREMENTS.md    → Understand what this module does
├── SCHEMA.md          → Know the exact entity fields
├── API.md             → Know the endpoints to build
├── SCREENS.md         → Know the UI components to build
├── DEPENDENCIES.md    → Verify prerequisites exist
├── JOBS.md            → Background jobs to implement (if present)
└── mockups/*.html     → Interactive HTML mockups for each screen (visual reference)
```

Also read:
- `shared/ENTITIES.md` for any referenced entities from other modules
- `shared/ACCESS-MATRIX.md` for access control on this module's data
- `shared/BUSINESS-RULES.md` if this module involves calculations

**Do NOT use local ticket files (`tickets/phase-1/sprint-*.md`) for implementation context.** Those files exist only as a reference for Jira ticket creation. All implementation context comes from Jira ticket descriptions via the Atlassian MCP.

### Step 2: Build Backend
1. Database migration for any new tables/columns in SCHEMA.md
2. Entity/model definitions matching SCHEMA.md exactly
3. API endpoints from API.md with access control middleware
4. Business logic layer for calculations (reference BUSINESS-RULES.md)
5. Validation middleware matching FSD §11 rules
6. Background jobs from JOBS.md (if present) — scheduled and event-triggered
7. Audit logging for all write operations

### Step 2.5: Write & Run Backend Tests (MANDATORY — do NOT skip)

**Tests must pass before moving to frontend.** Write pytest integration tests for every endpoint built in Step 2. Place tests in `backend/tests/test_{module}/`.

Every endpoint must have tests covering:

1. **Happy path** — CRUD succeeds with valid data, returns correct shape
2. **Relationships** — Create/update with every FK populated AND with FK null. If entity has relationships (e.g. `reporting_manager_id`, `resource_id`, `dm_id`), test:
   - Create with relationship set
   - Update to add relationship
   - Update to change relationship
   - Update to remove relationship (set null)
   - Response includes nested relationship data (not just the FK ID)
3. **Access control** — Authorized role succeeds, unauthorized role gets 403, scope filtering returns correct subset
4. **Validation errors** — Missing required fields, duplicate unique fields, invalid FK references, self-referential violations (e.g. resource can't be own manager)
5. **Edge cases** — Empty lists, pagination boundaries, filter combinations, soft-delete behavior

**Run all tests:** `cd backend && python -m pytest` — all must pass before proceeding.

### Step 3: Build Frontend
1. **Fetch the Jira ticket description first** — use Atlassian MCP (`getJiraIssue`) to read the full ticket. The description has a context section with mockup paths, acceptance criteria, and implementation hints. Do not skip this.
2. **Open the mockup HTML** — before writing any component, open the mockup file referenced in the Jira ticket description. Extract exact colors, spacing, font sizes, icons, card wrappers, badges, and structural layout. Every component must visually match its mockup — do not approximate with generic Tailwind classes (e.g. `bg-blue-600`) when the mockup uses specific theme colors (e.g. `#FF4B2B`).
3. Components from SCREENS.md — use the module's `mockups/*.html` files as the pixel-level visual reference for layout, spacing, and interactions
4. API integration layer
5. Form validations (client-side, matching server-side rules)
6. Empty states, loading states, error states
7. Responsive layout

### Step 4: Verify
1. All REQUIREMENTS.md acceptance criteria met
2. All validations from FSD §11 implemented
3. Access control tested for each role
4. Audit log entries generated for all writes

---

## Module Dependencies — What NOT to Do

- Never import from a module that hasn't been built yet in the phase order
- Never create an entity that belongs to another module — reference it via the shared/ definitions
- Never hardcode role names — always query the Role table
- Never skip audit logging — even if it seems minor
- Never calculate margins or revenue differently than `shared/BUSINESS-RULES.md` — even if you think there's a better formula
- Never expose sensitive fields to unauthorized roles — even in development/testing

---

## Seed Data

On first deployment, the system needs:

### Roles (7 default)
CEO, CTO, DM (Delivery Manager), PM (Project Manager), FINANCE, HR, ENGINEER

### RolePermissions (105 rows)
One row per role × data_type combination. See `shared/ACCESS-MATRIX.md` for the full matrix. Seed script must generate all 105 rows.

### SystemConfig (7 default keys)
| Key | Default |
|---|---|
| alert.contract_expiry_days | 30 |
| alert.contract_expiry_urgent_days | 7 |
| alert.bench_threshold_days | 7 |
| alert.utilization_threshold_pct | 70 |
| system.working_days_per_month | 22 |
| system.working_hours_per_day | 8 |
| system.default_currency | INR |

### Admin User
Create one admin user with CEO role for initial access.

---

## Scheduled Jobs

| Job | Schedule | Module | Description |
|---|---|---|---|
| Auto-Release | Daily midnight IST | 05-allocation-tracking | Release assignments where end_date ≤ today. See FSD §8. |
| Contract Expiry Alert | Daily | 12-alerts | Check projects with contract_end_date approaching. |
| Bench Duration Alert | Daily | 12-alerts | Check resources on bench > threshold days. |
| Milestone Overdue Alert | Daily | 12-alerts | Check milestones past planned_delivery_date. |
| Utilization Alert | Weekly (Monday) | 12-alerts | Check company utilization < threshold. |
| Recurring Cost Processing | Monthly (1st) | 06-non-human-costs | Auto-create monthly entries for active recurring costs. |

---

## Testing Expectations

- Every API endpoint has at least one happy-path test and one access-control test
- Every validation rule from FSD §11 has a test that triggers it
- Every state machine transition has a test for allowed and disallowed transitions
- Every calculation from BUSINESS-RULES.md has a test with known input/output values
- The auto-release job has tests for: normal release, extension before release, already released

### Relationship & Serialization Tests (CRITICAL)
The most common class of bug in this codebase is: an endpoint works for simple cases but crashes when relationships are involved (e.g. async SQLAlchemy lazy-load errors, missing eager loads, null FK serialization). **Every entity with a FK must have tests that exercise the relationship through the full API round-trip:**

- **Create with FK set** → verify response includes nested object (not just FK ID)
- **Update to set FK** → verify response includes nested object
- **Update to null FK** → verify response has null (not crash)
- **GET detail with FK set** → verify nested object present
- **GET list with mixed FK values** → verify items with and without FK both serialize correctly
- **Invalid FK** → verify 400/404, not 500

If any test returns a 500, that is a test failure — 500s are never acceptable in tested code paths.

### E2E Tests (Playwright) — 3 Tiers

E2E tests live in `e2e/` at the repo root. Three tiers:

| Tier | Directory | Purpose | Runs in CI |
|------|-----------|---------|------------|
| **Ticket tests** | `e2e/tests/tickets/sprint-N/` | One spec per Jira ticket, one `test()` per AC item | Manual |
| **Integration tests** | `e2e/tests/integration/` | Cross-module flows (create→view→edit→deactivate, cross-role) | Manual |
| **Smoke tests** | `e2e/tests/smoke/` | Fast critical-path checks (<10s each) | Every push/PR |

**Generating tests:** Use the `/e2e-test-ticket` skill — it fetches the Jira ticket, reads AC, generates all 3 tiers. Example: `e2e VRIP-31` or `e2e sprint 2`.

**Running locally:**
```bash
cd e2e && npx playwright test                        # All tiers
cd e2e && npx playwright test --project=smoke        # Smoke only
cd e2e && npx playwright test --project=tickets      # Ticket tests only
cd e2e && npx playwright test --project=integration  # Integration only
cd e2e && npx playwright test tests/tickets/sprint-2/  # One sprint
cd e2e && npx playwright test --ui                   # Interactive UI
```

**CI:** Smoke tests run on every push/PR. Other tiers can be triggered via workflow_dispatch with `test_scope: tickets | integration | all`.

---

## Local Development

### Quick start (no Docker)
```bash
# Backend — SQLite, no infra needed
cd backend && python3 -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Frontend — proxies API to :8000
cd frontend && npm run dev
```
- Backend: http://localhost:8000 | Health: http://localhost:8000/api/v1/health
- Frontend: http://localhost:5173

### Full stack (Docker)
```bash
docker compose -f docker-compose.dev.yml up postgres redis -d   # infra
cd backend && python3 -m uvicorn app.main:app --reload          # API
cd frontend && npm run dev                                       # UI
```
- PostgreSQL: `localhost:5432` (ri_platform / devuser / devpass)
- Redis: `localhost:6379`

### Slash commands
Use `/dev-backend`, `/dev-frontend`, `/dev-infra`, or `/dev-all` to start services via Claude Code.

### Testing
```bash
cd backend && python -m pytest        # Backend tests
cd frontend && npx vitest             # Frontend tests
cd e2e && npx playwright test                        # All E2E tiers
cd e2e && npx playwright test --project=smoke        # Smoke only (runs in CI)
cd e2e && npx playwright test --project=tickets      # Ticket tests
cd e2e && npx playwright test --project=integration  # Integration tests
```

### Linting
Use `/lint` or see `.claude/commands/lint.md`.

---

## When In Doubt

1. Check `fsd/FSD.md` — it's the authoritative technical spec
2. Check the module's REQUIREMENTS.md — it has acceptance criteria
3. Check `shared/BUSINESS-RULES.md` — it has exact formulas
4. If still unclear, ask — don't assume

<!-- CODEGRAPH_START -->
## CodeGraph

In repositories indexed by CodeGraph (a `.codegraph/` directory exists at the repo root), reach for it BEFORE grep/find or reading files when you need to understand or locate code:

- **MCP tools** (when available): `codegraph_explore` answers most code questions in one call — the relevant symbols' verbatim source plus the call paths between them. `codegraph_node` returns one symbol's source + callers, or reads a whole file with line numbers. If the tools are listed but deferred, load them by name via tool search.
- **Shell** (always works): `codegraph explore "<symbol names or question>"` and `codegraph node <symbol-or-file>` print the same output.

If there is no `.codegraph/` directory, skip CodeGraph entirely — indexing is the user's decision.
<!-- CODEGRAPH_END -->
