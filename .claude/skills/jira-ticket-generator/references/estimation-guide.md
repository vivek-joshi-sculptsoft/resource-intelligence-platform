# Estimation Guide

## Sizing Framework

Every story is sized based on three dimensions: scope, complexity, and uncertainty.

### Scope — How much code?

| Signal | Low | Medium | High |
|---|---|---|---|
| Entity field count | < 8 fields | 8-15 fields | > 15 fields |
| API endpoint count | 1-3 | 4-7 | 8+ |
| UI component count | 1-2 | 3-5 | 6+ |
| Validation rule count | 0-2 | 3-5 | 6+ |

### Complexity — How hard?

| Signal | Simple | Moderate | Complex |
|---|---|---|---|
| Data model | Single entity, no FKs | 1-2 FKs, simple joins | Multiple FKs, self-refs, computed fields |
| Business logic | Straightforward CRUD | Conditional rules, formulas | State machines, multi-step workflows |
| Access control | Single role or public | 2-3 roles with scoping | Field-level restrictions, configurable |
| UI interactions | Static display, simple forms | Dropdowns, filters, sorting | Live previews, drag-drop, charts |

### Uncertainty — How clear?

| Signal | Clear | Some Gaps | Ambiguous |
|---|---|---|---|
| Requirements | Detailed AC in REQUIREMENTS.md | AC exists but has edge cases | Vague description only |
| Dependencies | All prerequisites built | Some prerequisites in progress | Prerequisites not started |
| Domain knowledge | Team knows this pattern | Similar but not identical pattern | New territory |

### Size Matrix

| Scope | Complexity | Uncertainty | Size | Points | Days |
|---|---|---|---|---|---|
| Low | Simple | Clear | XS | 1 | <1 |
| Low | Simple-Moderate | Clear | S | 2 | 1-2 |
| Medium | Moderate | Clear | M | 3 | 2-3 |
| Medium | Complex | Clear | L | 5 | 3-5 |
| High | Complex | Clear | L | 5 | 3-5 |
| High | Complex | Some gaps | XL | 8 | 5-8 |
| Any | Any | Ambiguous | Spike first | — | — |

### Common Estimation Mistakes

**Under-estimating:**
- "Simple CRUD" with 7 validations, role-based access, and audit logging → not simple, M not S
- "Just a dashboard" with 7 widgets, 3 aggregation levels, and drill-down → L not M
- "Add a field" that changes a calculation, affects 3 dashboards, and needs migration → M not XS

**Over-estimating:**
- Seed data script for well-defined data → XS, not M
- Adding a filter to an existing list → XS, not S
- Soft delete when the flag already exists → XS

---

## Example Estimations

### Example: Assignment CRUD (module 05)
- 14 fields including 2 FKs, 2 date fields, computed designation
- 7 validation rules
- State machine (ACTIVE/RELEASED/AUTO_RELEASED)
- Role-based access with field restrictions
- Audit logging
- **Assessment:** High scope, Complex, Clear requirements
- **Size: L (5 points, 3-5 days)**

### Example: Client CRUD (module 02)
- 9 fields, no state machine
- 1 validation (can't deactivate with active projects)
- Simple access control
- **Assessment:** Low-Medium scope, Simple, Clear
- **Size: M (3 points, 2-3 days)** — bumped from S because it includes list + detail + form UI

### Example: Company Dashboard (module 07)
- 7 widgets with aggregation queries
- Role-scoped data
- No write operations
- **Assessment:** High scope (many widgets), Moderate complexity, Clear
- **Size: L (5 points, 3-5 days)**

### Example: Auto-release scheduled job (module 05)
- Processes assignments daily
- State change + alert creation + audit logging
- Idempotency needed
- Edge case: extension on release day
- **Assessment:** Medium scope, Complex, Clear
- **Size: M (3 points, 2-3 days)**
