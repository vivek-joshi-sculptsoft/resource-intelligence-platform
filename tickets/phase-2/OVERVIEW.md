# Phase 2 — Financial Engine | Sprint Plan

> Generated 2026-06-15. 5 epics, 23 stories, 65 SP, 4 sprints.

## Epics

| Epic Key | Name | Stories | SP |
|----------|------|---------|-----|
| VRIP-82 | EP-10 Financial Engine | 7 | 18 |
| VRIP-83 | EP-11 Non-Human Costs | 4 | 12 |
| VRIP-84 | EP-12 Invoicing | 6 | 20 |
| VRIP-85 | EP-13 Bench Forecasting | 2 | 5 |
| VRIP-86 | EP-14 Dashboard Financial Updates | 4 | 10 |

---

## Sprint 6: Financial Foundation (16 SP)

| Key | Story | Epic | Size | Pts | Labels |
|-----|-------|------|------|-----|--------|
| VRIP-87 | S6-01: Activate loaded_cost_monthly field on Resource | EP-10 | S | 2 | database, backend, frontend |
| VRIP-88 | S6-02: Activate billing_rate field on Assignment | EP-10 | S | 2 | database, backend, frontend |
| VRIP-89 | S6-03: NonHumanCost database schema | EP-11 | XS | 1 | database |
| VRIP-90 | S6-04: NonHumanCost CRUD API — validations, access control, multi-currency | EP-11 | L | 5 | backend |
| VRIP-91 | S6-05: NonHumanCost list view and form UI | EP-11 | M | 3 | frontend |
| VRIP-92 | S6-06: Recurring cost processing scheduled job | EP-11 | M | 3 | backend, infrastructure |

### Sprint 6 Dependencies
```
VRIP-89 (schema) → VRIP-90 (CRUD) → VRIP-91 (UI)
                                    → VRIP-92 (job)
VRIP-87, VRIP-88: no Phase 2 blockers (depend on Phase 1 done)
```

---

## Sprint 7: Invoicing (20 SP)

| Key | Story | Epic | Size | Pts | Labels |
|-----|-------|------|------|-----|--------|
| VRIP-93 | S7-01: Milestone and Invoice database schema | EP-12 | S | 2 | database |
| VRIP-94 | S7-02: Milestone CRUD API with lifecycle transitions | EP-12 | L | 5 | backend |
| VRIP-95 | S7-03: Invoice CRUD API with lifecycle transitions and multi-currency | EP-12 | L | 5 | backend |
| VRIP-96 | S7-04: Milestone list view and transition UI | EP-12 | M | 3 | frontend |
| VRIP-97 | S7-05: Invoice list view and form UI | EP-12 | M | 3 | frontend |
| VRIP-98 | S7-06: Outstanding receivables view | EP-12 | S | 2 | frontend, backend |

### Sprint 7 Dependencies
```
VRIP-93 (schema) → VRIP-94 (milestone CRUD) → VRIP-95 (invoice CRUD) → VRIP-97 (invoice UI)
                                              → VRIP-96 (milestone UI)  → VRIP-98 (receivables)
```

---

## Sprint 8: Calculations & Bench (15 SP)

| Key | Story | Epic | Size | Pts | Labels |
|-----|-------|------|------|-----|--------|
| VRIP-99 | S8-01: Project financials API — cost, revenue, and margin calculations | EP-10 | L | 5 | backend |
| VRIP-100 | S8-02: Client and company financials APIs | EP-10 | M | 3 | backend |
| VRIP-101 | S8-03: Resource bench cost API | EP-10 | S | 2 | backend |
| VRIP-102 | S8-04: Bench cost and availability API enhancements | EP-13 | M | 3 | backend |
| VRIP-103 | S8-05: Availability view — bench cost and financial field updates | EP-13 | S | 2 | frontend |

### Sprint 8 Dependencies
```
VRIP-87 (S6) + VRIP-88 (S6) + VRIP-90 (S6) + VRIP-95 (S7) → VRIP-99 (project financials)
VRIP-99 → VRIP-100 (client/company financials)
VRIP-87 (S6) → VRIP-101 (bench cost)
VRIP-87 (S6) → VRIP-102 (bench APIs) → VRIP-103 (availability UI)
```

---

## Sprint 9: Dashboard Updates & Polish (14 SP)

| Key | Story | Epic | Size | Pts | Labels |
|-----|-------|------|------|-----|--------|
| VRIP-104 | S9-01: Project financials tab UI | EP-10 | M | 3 | frontend |
| VRIP-105 | S9-02: Resource profile — loaded cost section UI update | EP-10 | XS | 1 | frontend |
| VRIP-106 | S9-03: Company dashboard — financial widgets | EP-14 | M | 3 | backend, frontend |
| VRIP-107 | S9-04: DM dashboard — financial widgets | EP-14 | S | 2 | backend, frontend |
| VRIP-108 | S9-05: Client dashboard — financial aggregation | EP-14 | S | 2 | backend, frontend |
| VRIP-109 | S9-06: Phase 2 integration testing and hardening | EP-14 | M | 3 | testing |

### Sprint 9 Dependencies
```
VRIP-99 (S8) → VRIP-104 (financials tab UI)
VRIP-87 (S6) → VRIP-105 (resource profile cost)
VRIP-99 (S8) + VRIP-100 (S8) → VRIP-106 (company dashboard)
VRIP-99 (S8) → VRIP-107 (DM dashboard)
VRIP-100 (S8) → VRIP-108 (client dashboard)
All S6-S8 → VRIP-109 (integration testing)
```

---

## Cross-Sprint Dependency Chain (Critical Path)

```
S6: VRIP-87 (loaded_cost) ──┐
S6: VRIP-88 (billing_rate) ─┤
S6: VRIP-90 (NHC CRUD) ─────┤
S7: VRIP-95 (Invoice CRUD) ─┴→ S8: VRIP-99 (Project Financials) → S8: VRIP-100 (Client/Co Financials)
                                         │                                    │
                                         ├→ S9: VRIP-104 (Financials tab)     ├→ S9: VRIP-108 (Client dashboard)
                                         ├→ S9: VRIP-106 (Company dashboard)
                                         └→ S9: VRIP-107 (DM dashboard)
```

The critical path runs: loaded_cost + billing_rate + NHC + Invoices → Project Financials → Dashboard widgets.
