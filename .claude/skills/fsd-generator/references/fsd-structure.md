# FSD Structure & Section Guide

Sections are assembled dynamically based on what the PRD contains. The guiding question: "Does the PRD produce meaningful implementation content for this section?" If yes, include it. If not, skip.

---

## Always Include

These sections appear in every FSD:

| Section | Purpose | Naming |
|---|---|---|
| Introduction | What this FSD covers, which PRD version it's based on, notation guide | "Introduction & Scope" |
| Entity Definitions | Field-level specs for every data entity | Named per entity: "User", "Project", "Order" |
| Entity Relationships | Cardinality table showing how entities connect | "Entity Relationships" |
| Validation Rules | Exact conditions, error messages, hard vs soft | "Validation Rules" |
| Phase-wise Build Guide | Entity/field/feature mapping per phase | "Phase-wise Implementation Guide" |

## Include When Relevant

| Section | Include When... | Naming |
|---|---|---|
| ER Diagram | Always when >3 entities (visual comprehension) | "ER Diagram" |
| DFD | System has distinct processes with clear data flows | "Data Flow Diagram" |
| State Machines | Any entity has a multi-step lifecycle | "State Machines & Lifecycles" |
| Calculations | Financial formulas, utilization rates, derived metrics | "Calculations & Business Logic" |
| Scheduled Jobs | System has timed processes (auto-release, alerts, cleanup) | "Scheduled Job Logic" or name the specific job |
| View Specifications | Multiple user roles with different dashboards | "View Specifications" |
| Access Control | Role-based restrictions on data visibility | "Access Control Rules" |
| Alert Specifications | System generates proactive notifications | "Alert Specifications" |
| Audit & History | Changes need to be tracked for reconstruction | "Audit & History" |
| Edge Cases | Complex entity interactions with non-obvious outcomes | "Edge Cases & Error Handling" |
| API Contracts | System exposes APIs to external consumers | "API Specifications" |
| Integration Specs | System connects to external services | "Integration Specifications" |
| Search & Filtering | Complex search/filter requirements | "Search & Query Specifications" |
| File Handling | System processes uploads, generates documents | "File Processing" |
| Notification Logic | Email, SMS, push notification rules | "Notification Specifications" |

---

## Entity Definition Format

Each entity gets a collapsible panel (HTML) or sub-section (Word):

```
Entity Name [tag: Core/System/Optional/Phase 2]
  Brief description (1 sentence)
  Field definition table:
    Field | Type | Constraints | Notes
  Callout boxes for:
    - Critical constraints
    - Computed field formulas  
    - Related business rules
  Join tables (if any)
```

---

## Formatting

### Formula Block
Monospace, colored background, stands out from body text.
```
Revenue per Assignment = billability_pct / 100 × working_days × 8 × billing_rate
```

### State Flow Visual
Inline state boxes with arrows:
```
[PLANNED] → [DELIVERED] → [APPROVED] → [INVOICED] → [PAID]
```

### Callout Types
- **Info (blue)**: Key architectural decisions, notation explanations
- **Warning (yellow)**: Constraints, edge cases, backward transitions
- **Success (green)**: Design rationale, "why we chose this" explanations  
- **Danger (red)**: Critical edge cases, data loss risks
- **Purple**: Calculation notes, formula context

### Tags on Entities
- `Core` — Central to the system, Phase 1
- `System` — Infrastructure (audit, config, alerts)
- `Optional` — Can be disabled (worklog)
- `Financial` — Phase 2 typically
- `Phase N` — Explicit phase assignment

---

## Quality Checklist

Before delivering the FSD:

- [ ] Every entity from the PRD has a field-level definition
- [ ] Every relationship has cardinality documented
- [ ] Every lifecycle entity has a state machine with transitions, triggers, and side effects
- [ ] Every calculation has an explicit formula with field references
- [ ] Every validation has a condition AND an error message
- [ ] Every sensitive field has access restrictions documented
- [ ] The phase guide maps every entity, field, and feature to a specific phase
- [ ] Edge cases cover entity deactivation, cascading deletes, and concurrent modification
- [ ] The ER diagram matches the entity definitions (no orphan entities, no missing relationships)
- [ ] Cross-references between sections use correct section numbers
- [ ] A developer reading only this FSD (without the PRD) can build the system
- [ ] Computed fields specify whether they're calculated on-read or stored
- [ ] Scheduled jobs specify timing, retry logic, and failure handling
- [ ] The notation section explains all conventions used (*, FK, PK, Computed, etc.)
