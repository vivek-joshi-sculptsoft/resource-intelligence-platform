# Phase 1 — Ticket Overview

## Configuration

| Setting | Value |
|---------|-------|
| Epic Grouping | One per module + DevOps bootstrap |
| Story Granularity | Medium (2-3 days per story) |
| Team | 1 developer + Claude Code (agentic) |
| Task Split | Backend + Frontend + DevOps/Infra sub-tasks |
| Sprint Length | 1 week |
| Velocity | ~20 SP/sprint (AI-assisted) |

## Epics (10 total)

| Epic | Module | Sprint | Stories | Story Points |
|------|--------|--------|---------|-------------|
| EP-0: Project Bootstrap & DevOps | — | 0 | 8 | 20 |
| EP-1: Authentication & Roles | 01-auth-and-roles | 1 | 9 | 25 |
| EP-2: Resource Management | 04-resource-management | 2 | 8 | 19 |
| EP-3: Client Management | 02-client-management | 2 | 7 | 14 |
| EP-4: Project Management | 03-project-management | 3–4 | 10 | 27 |
| EP-5: Allocation Tracking | 05-allocation-tracking | 3–4 | 10 | 30 |
| EP-6: Utilization Dashboards | 07-utilization-dashboards | 5 | 6 | 18 |
| EP-7: Worklog | 11-worklog | 5 | 6 | 13 |
| EP-8: Audit History (Phase 1 scope) | 13-audit-history | 0 | 1 | 3 |
| EP-9: Integration Testing & Polish | — | 5 | 2 | 4 |
| **Total** | | **6 sprints** | **67** | **173** |

## Sprint Plan Summary

| Sprint | Theme | Epics | SP | Deliverable |
|--------|-------|-------|---|-------------|
| 0 | Bootstrap | EP-0, EP-8 (table+wrapper) | 20 | Runnable project. `docker-compose up` boots everything with seeded DB. CI runs. |
| 1 | Auth & Security | EP-1 | 25 | Login works. RBAC enforced. User management. Role viewer. |
| 2 | Data Foundation | EP-2, EP-3 | 33 | Resources + Clients: full CRUD with access control and UI. |
| 3 | Projects & Allocations BE | EP-4, EP-5 (backend) | 30 | Projects with lifecycle. Assignments with 7 validations. Auto-release job. |
| 4 | Projects & Allocations FE | EP-5 (frontend), EP-4 (UI) | 27 | Full project detail. Assignment management. Resource profile. |
| 5 | Dashboards & Worklog | EP-6, EP-7, EP-9 | 35 | Utilization dashboards. Worklog entry. E2E tests. Phase 1 complete. |

## Ticket Files

| File | Sprint | Stories | SP |
|------|--------|---------|---|
| [sprint-0-bootstrap.md](sprint-0-bootstrap.md) | Sprint 0 — Project Bootstrap | 8 | 20 |
| [sprint-1-auth.md](sprint-1-auth.md) | Sprint 1 — Auth & Roles | 9 | 25 |
| [sprint-2-data-foundation.md](sprint-2-data-foundation.md) | Sprint 2 — Resources + Clients | 15 | 33 |
| [sprint-3-projects-allocations-be.md](sprint-3-projects-allocations-be.md) | Sprint 3 — Projects + Allocations BE | 11 | 30 |
| [sprint-4-projects-allocations-fe.md](sprint-4-projects-allocations-fe.md) | Sprint 4 — Projects + Allocations FE | 11 | 27 |
| [sprint-5-dashboards-worklog.md](sprint-5-dashboards-worklog.md) | Sprint 5 — Dashboards + Worklog + Polish | 14 | 35 |
| **Total** | **6 sprints** | **68** | **170** |

## Label Taxonomy

| Label | Meaning |
|-------|---------|
| `backend` | Python/FastAPI API, business logic, DB queries |
| `frontend` | React UI components, pages, forms |
| `devops` | Docker, CI/CD, deployment, infrastructure setup |
| `database` | Schema migrations, seed data, indexes |
| `testing` | Integration tests, E2E tests |
| `phase-1` | Phase 1 scope |
| `must-have` | Required for sprint deliverable |
| `nice-to-have` | Can defer without blocking sprint goal |
| `agentic` | Designed for Claude Code execution (self-contained context) |

## Agentic Development Standards

Every story follows these practices for Claude Code execution:

1. **Context Block** — Each story lists which spec files to read before starting
2. **Self-Contained Scope** — One Claude Code session can complete the story
3. **Verification Steps** — Testable acceptance criteria, not vague descriptions
4. **File References** — Explicit paths to create/modify
5. **CLAUDE.md Alignment** — All stories reference the build conventions in CLAUDE.md
