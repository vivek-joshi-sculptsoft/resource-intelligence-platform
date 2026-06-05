# Module 06: Non-Human Costs — Screen Specifications

## Screen: Non-Human Costs Tab (within Project Detail)
**Route:** `/projects/:id` → Non-Human Costs tab
**Audience:** CEO, CTO, DM (own portfolio), PM (own portfolio), Finance
**Layout:** Table with action bar above.

### Components
- Cost table (see data below)
- "Add Cost" button
- Category filter dropdown: All / AI Tools / Cloud Infra / Devices / License / Other
- Recurring filter toggle
- Summary row: total INR, one-time total, recurring monthly total

### Data Displayed

| Field | Source | Notes |
|---|---|---|
| Date | NonHumanCost.cost_date | Formatted date |
| Description | NonHumanCost.description | |
| Category | NonHumanCost.category | Pill badge |
| Amount | NonHumanCost.amount + currency | e.g., "$200 USD" |
| Exchange Rate | NonHumanCost.exchange_rate | Hidden if INR |
| Amount INR | NonHumanCost.amount_inr | "₹16,700" |
| Recurring | NonHumanCost.is_recurring + recurring_end_date | "Monthly until Dec 2026" or "One-time" |
| Added By | created_by.name | |

### Actions
- Add Cost → open create form (modal or inline)
- Click row → edit form
- Delete → confirmation dialog → DELETE endpoint

### Empty State
"No costs recorded yet. Add your first cost entry."

### Access Restrictions
HR and Engineer have no access to this tab.

---

## Screen: Cost Create / Edit Form
**Route:** Modal within `/projects/:id`
**Audience:** CEO, CTO, DM (own portfolio), PM (own portfolio), Finance
**Layout:** Form in modal.

### Components
- Description input (required)
- Category dropdown (required): AI Tools / Cloud Infra / Devices / Third-Party License / Other
- Amount input (required, positive number)
- Currency dropdown (default INR): INR, USD, EUR, GBP, + others
- Exchange Rate input (auto-set to 1.0 and disabled when INR; required positive for others)
- INR Preview field: live-computed `amount × exchange_rate` — read-only, updates as user types
- Date picker: "Cost Date" (required)
- Recurring toggle
- Recurring End Date picker (shown only when recurring is on; required)

### Validation Messages
- "Cost amount must be positive"
- "Exchange rate must be positive"
- "Recurring costs must have an end date"
- "Recurring end date must be after cost date"

### Actions
- Save → POST (create) or PUT (edit) → update cost list
- Cancel → close modal

### Empty State
N/A.

### Access Restrictions
Only accessible to authorized roles. Not shown to HR or Engineer.
