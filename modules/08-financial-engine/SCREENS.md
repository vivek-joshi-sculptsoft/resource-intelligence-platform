# Module 08: Financial Engine — Screen Specifications

This module does not introduce new standalone screens. It adds financial data and widgets to screens owned by other modules.

---

## Updates to Existing Screens

### Resource Profile (Module 04) — Financial Field Added
**Route:** `/resources/:id`
**Audience addition:** CEO, CTO, Finance can now see and edit `loaded_cost_monthly`

**New component added to resource profile:**
- Loaded Cost (Monthly INR) field — displayed and editable only to CEO/CTO/Finance
- Located in a "Cost" section or alongside profile fields
- Edit inline or via edit form

---

## Screen: Project Financials Tab (within Project Detail)
**Route:** `/projects/:id` → Financials tab
**Audience:** CEO, CTO, Finance; DM (configurable for margin)
**Layout:** Summary metrics row + resource cost breakdown table.

### Components
- Summary row: Total Cost | Projected Revenue | Projected Margin % | Actual Revenue | Actual Margin %
- Resource Cost Breakdown table
- Non-Human Cost total (link to costs tab)
- Missing data warnings (resources without loaded cost, assignments without billing rate)

### Data Displayed

| Field | Source | Notes |
|---|---|---|
| Resource Cost INR | §7.2 formula | |
| Non-Human Cost INR | §7.2 formula | Sum of amount_inr for project |
| Total Cost INR | §7.2 formula | Resource + Non-Human |
| Projected Revenue INR | §7.3 formula | |
| Actual Revenue INR | §7.4 formula | Sum of approved/paid invoice amount_inr |
| Projected Margin INR / % | §7.5 formula | |
| Actual Margin INR / % | §7.5 formula | |

### Resource Cost Breakdown Table

| Resource | Allocation % | Loaded Cost/Mo | Cost Contribution |
|---|---|---|---|
| Name | 60% | ₹X | ₹Y |

### Actions
- Missing cost warning: "3 resources are missing loaded cost" → link to resource profiles
- Hover/click info icon on each KPI card → tooltip with formula, meaning, and purpose (see Info Tooltips below)

### Info Tooltips

Same pattern as the Company Dashboard (`modules/07-utilization-dashboards/SCREENS.md`): each KPI card shows an info icon (`lucide-react` `Info`) next to its label; hovering/clicking opens a tooltip with three parts: **Formula**, **What it means**, **Why it matters**. Applies to the 4 KPI cards (Total Cost, Projected Revenue, Actual Revenue, Projected Margin) plus the Actual Margin line item in the Revenue vs Cost card, which is not its own KPI card. Tooltip text shown to end users does not reference internal doc paths (e.g. `BUSINESS-RULES.md`) — those references are kept in this spec table only, for engineering traceability.

| Card | Formula | What it means | Why it matters |
|---|---|---|---|
| Total Cost | `Resource Cost + Non-Human Cost` — `shared/BUSINESS-RULES.md §7.2` | Combined cost of staffing and non-human expenses for the project | Baseline against which revenue and margin are measured |
| Projected Revenue | `SUM(billability_pct / 100 × working_days × working_hours × billing_rate)` for non-shadow ACTIVE assignments, converted to INR — `shared/BUSINESS-RULES.md §7.3` | Expected billable revenue for the project based on current assignments and rates | Forecasts whether the engagement is on track to be profitable |
| Actual Revenue | `SUM(invoice.amount_inr)` where status ∈ {APPROVED, PAID} — `shared/BUSINESS-RULES.md §7.4` | Revenue actually invoiced and recognized to date | Source of truth for billed revenue, independent of allocation assumptions |
| Projected Margin | `Projected Revenue (INR) − Total Project Cost` — `shared/BUSINESS-RULES.md §7.5` | Forecasted profitability of the project before invoicing | Early warning signal for underpriced or over-resourced engagements |
| Actual Margin (to date) | `Actual Revenue (INR) − Total Project Cost` — `shared/BUSINESS-RULES.md §7.5` | Realized profitability based on invoiced revenue to date | Tracks whether actual delivery is matching or missing the projected margin |

### Empty State
"Financial data is not yet available. Ensure resources have loaded costs and assignments have billing rates."

### Access Restrictions
Tab only visible to CEO, CTO, Finance, and DM with configurable margin access.

---

## Updates to Company Dashboard (Module 07)

**Phase 2 additions to `/dashboard`:**
- Revenue Summary widget: Projected Revenue vs Actual Revenue (INR bar/comparison)
- Total Company Cost widget
- Company Margin widget
- Bench Cost widget

All Phase 2 financial widgets are restricted to CEO and CTO.
