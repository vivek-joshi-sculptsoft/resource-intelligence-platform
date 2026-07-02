# Phase 3 — Intelligence & Alerts | Sprint Plan

> Generated 2026-07-02 via `/jira-ticket-generator`. 3 epics, 10 stories, 35 SP, 2 sprints.
> Priority order per explicit request: Audit History + Role-Based Access Configuration before Alerts.

## Configuration

Reused from Phase 1/2 (no re-prompt — derived from existing VRIP-82/VRIP-87 tickets since the preference questionnaire went unanswered):

| Setting | Value |
|---|---|
| Epic Grouping | One epic per module-phase (matches EP-10…EP-14 pattern — Phase 3 additions get new epics, not reused Phase 1 ones) |
| Naming Convention | Numbered — `EP-{N} {Name}`, `S{sprint}-{seq}: {Action} {Subject}` |
| Description Format | Markdown — Context / AC / Out of Scope / Depends On |
| Team Structure | Full-stack per story — no sub-tasks created (Phase 2 breakdown not requested) |
| Sprint Length | 1 week, ~20-25 SP capacity (matches Sprint 6-9 actuals) |

## Scope Decision

**Role-Based Access Configuration (EP-16) covers RolePermission matrix editing only.** `UserPermissionOverride` (per-user exceptions), flagged as optional in `CLAUDE.md` Phase 3 build order (item 16), was explicitly deferred — not built. Add it as a follow-up story under EP-16 if needed later.

## Epics

| Epic Key | Name | Module | Stories | SP |
|----------|------|--------|---------|-----|
| VRIP-114 | EP-15 Audit History — Viewer & Historical Queries | 13-audit-history | 4 | 18 |
| VRIP-115 | EP-16 Role-Based Access Configuration | 01-auth-and-roles | 1 | 5 |
| VRIP-116 | EP-17 Alerts & Notifications | 12-alerts | 6 | 17 |

---

## Sprint 10: Audit History + Role-Based Access Config (23 SP)

| Key | Story | Epic | Size | Pts | Priority | Labels |
|-----|-------|------|------|-----|----------|--------|
| VRIP-117 | S10-01: Implement Audit Log Query API — filters, scoping, pagination | EP-15 | L | 5 | High | backend |
| VRIP-118 | S10-02: Build Audit Log Viewer UI — full history browser with filters | EP-15 | M | 3 | Medium | frontend |
| VRIP-119 | S10-03: Add Change History panel to entity detail views | EP-15 | L | 5 | Medium | frontend |
| VRIP-120 | S10-04: Implement Point-in-Time Reconstruction — API and admin view | EP-15 | L | 5 | Low | backend, frontend |
| VRIP-121 | S10-05: Build RolePermission Matrix Viewer & Editor | EP-16 | L | 5 | High | backend, frontend |

### Sprint 10 Dependencies
```
VRIP-117 (query API) → VRIP-118 (viewer UI)
                     → VRIP-119 (history panel)
                     → VRIP-120 (point-in-time reconstruction)
VRIP-121: no Phase 3 blockers (depends on Phase 1 Access Control Middleware, done)
```

**Deliverable:** CEO/CTO/DM/PM can query and browse full audit history, inline change history appears on Assignment/Project/Resource/Milestone/Invoice detail pages, past entity states can be reconstructed, and CEO/CTO can edit the RolePermission matrix without a deploy.

---

## Sprint 11: Alerts & Notifications (17 SP)

| Key | Story | Epic | Size | Pts | Priority | Labels |
|-----|-------|------|------|-----|----------|--------|
| VRIP-122 | S11-01: Implement Alert entity and shared alert creation service | EP-17 | S | 2 | High | backend, database |
| VRIP-123 | S11-02: Implement daily scheduled alert jobs — Contract Expiry, Bench Duration, Milestone Overdue | EP-17 | L | 5 | High | backend, infrastructure |
| VRIP-124 | S11-03: Implement weekly Utilization Drop job and Over-Allocation / Auto-Release event alerts | EP-17 | M | 3 | Medium | backend, infrastructure |
| VRIP-125 | S11-04: Build Alert Notification Panel — bell icon, unread count, mark read/dismiss | EP-17 | M | 3 | Medium | frontend |
| VRIP-126 | S11-05: Build Alert List Page — full history with filters and bulk actions | EP-17 | S | 2 | Low | frontend |
| VRIP-127 | S11-06: Build SystemConfig Admin UI — edit alert thresholds and system settings | EP-17 | S | 2 | Medium | backend, frontend |

### Sprint 11 Dependencies
```
VRIP-122 (Alert entity + service) → VRIP-123 (daily jobs)
                                  → VRIP-124 (weekly job + event alerts)
                                  → VRIP-125 (notification panel)
                                  → VRIP-126 (alert list page)
VRIP-127: independent (SystemConfig CRUD, no Alert entity dependency)
```

**Deliverable:** All 6 alert types fire (4 scheduled, 2 event-triggered), users see unread alerts via bell + full list page, CEO/CTO can tune thresholds via SystemConfig UI.

---

## Cross-Sprint Dependency Chain (Critical Path)

```
Sprint 10: VRIP-117 (Audit Query API) ──┬→ VRIP-118 (Viewer UI)
                                        ├→ VRIP-119 (History panel)
                                        └→ VRIP-120 (Point-in-time)
Sprint 10: VRIP-121 (RolePermission editor) — independent, Phase 1 middleware only

Sprint 11: VRIP-122 (Alert entity) ──┬→ VRIP-123 (daily jobs)
                                     ├→ VRIP-124 (weekly job + events)
                                     ├→ VRIP-125 (notification bell)
                                     └→ VRIP-126 (alert list page)
Sprint 11: VRIP-127 (SystemConfig UI) — independent
```

No cross-sprint blockers between Sprint 10 and Sprint 11 — Alerts (EP-17) does not depend on Audit History (EP-15) or RBAC Config (EP-16). Sprints were sequenced this way purely on priority, not a hard dependency.

## Jira Sprint IDs

Sprint 10 and Sprint 11 do not exist as Jira sprints yet — same gap as Sprint 6-9 had (sprint creation is UI-only, see `techstack/decisions/` and the Atlassian MCP notes). All 11 stories above carry `sprint-10` / `sprint-11` labels so they're identifiable regardless. Once the sprints are created on the VRIP board, assign issues via the sprint field (`customfield_10020`).

## Issue Links

`Blocks` links were created for every dependency listed above (e.g. VRIP-117 blocks VRIP-118/119/120; VRIP-122 blocks VRIP-123/124/125/126).
