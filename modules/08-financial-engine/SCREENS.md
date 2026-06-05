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
