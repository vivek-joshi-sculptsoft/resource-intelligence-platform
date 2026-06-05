# Glossary

> Combined from PRD §10 (business terms) and FSD §1 (notation guide).

---

## FSD §1 — Notation Guide

| Notation | Meaning |
|---|---|
| `*` after field name | Required field |
| STRING(n) | Variable-length string, max n characters |
| INTEGER | Whole number |
| DECIMAL(p,s) | Decimal with p total digits and s decimal places |
| DATE | Calendar date (YYYY-MM-DD) |
| TIMESTAMP | Date + time (auto-managed) |
| BOOLEAN | true / false |
| ENUM | Fixed set of allowed string values |
| FK | Foreign Key — references another entity's PK |
| TEXT | Unlimited-length string |
| PK | Primary Key |
| UK | Unique Key |
| DECIMAL(15,2) | All monetary amounts use this type |
| INTEGER (0–100) | All percentage fields use this type |

---

## Business Terms (PRD §10)

| Term | Definition |
|---|---|
| FP | Fixed Price — project with fixed scope, budget, timeline, milestone-based delivery |
| T&M | Time & Material — billed based on resource hours consumed |
| CTC | Cost to Company — total annual compensation of an employee |
| Loaded Cost | CTC plus overhead (seat, licenses, management). True per-resource cost. Used for all cost calculations. |
| DM | Delivery Manager — oversees a project portfolio and resource allocation decisions |
| PM | Project Manager — manages individual project execution and planning |
| Bench | State where a resource has zero project allocation (0% total allocation) |
| Shadow Resource | Working on a project but not billed to the client. Allocation > 0%, Billability = 0%. Tracked for true margin. |
| Projected Revenue | Expected revenue calculated from billability % × billing rate × working days, converted to INR. What you expect to earn before invoicing. |
| Actual Revenue | The invoice amount entered during invoicing. What the client actually pays. Source of truth for reporting. |
| Projected Margin | Projected Revenue − Total Cost (resource + non-human + shadow). Forecast profitability. |
| Actual Margin | Actual Revenue (invoice INR) − Total Cost. True profitability after invoicing. |
| INR | Indian Rupee — the standard currency for all internal reporting |
| Exchange Rate | Manually entered conversion rate from billing currency to INR at invoice/cost entry time. Not auto-fetched. |
| Worklog | Optional daily hours logged by employees per project. Not connected to billing. |
| Auto-Release | System automatically removes allocation when assignment end date is reached |
| Non-Human Cost | Project expenses for tools, cloud, devices, or licenses — not resource salaries |
| Allocation % | Percentage of a resource's total monthly capacity consumed by a specific project. Set once, carries forward automatically until changed or end date reached. |
| Billability % | Percentage of time on a project billed to the client. Independent of allocation. Can be lower than allocation but never higher. |
| Utilization Rate | Billable allocation ÷ total available capacity, as a percentage |

---

## System-Specific Terms

| Term | Definition |
|---|---|
| OWN_PORTFOLIO | Scope limiting a DM or PM to data for their own assigned projects only |
| SELF_ONLY | Scope limiting an Engineer to their own resource data and worklogs |
| Recurring Allocation | Allocation set once and auto-carried forward month after month — no monthly re-entry needed |
| Designation Resolution | Fallback rule: display `project_designation` if set, else `resource.designation`. Same for expertise. |
| Soft Delete | Entities are marked `is_active = false` rather than hard-deleted from the database |
| SystemConfig | Key-value store for configurable thresholds (bench days, utilization %, working days) — no hardcoded magic numbers |
| AuditLog | Immutable append-only log of every field change across tracked entities |
| Point-in-Time Reconstruction | Replaying AuditLog backwards to reconstruct entity state as of any past date |
