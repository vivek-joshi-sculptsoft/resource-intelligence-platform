# Module 06: Non-Human Costs — API Endpoints

## Endpoints

### GET /api/projects/:projectId/costs
**Description:** List all non-human cost entries for a project.
**Auth:** CEO, CTO, DM (own portfolio), PM (own portfolio), Finance. HR and Engineer have no access. Reference `shared/ACCESS-MATRIX.md` (`non_human_costs`).
**Scope:** OWN_PORTFOLIO for DM/PM
**Response:** Paginated array:
```json
[{
  "id", "description", "category", "amount", "currency", "exchange_rate",
  "amount_inr", "cost_date", "is_recurring", "recurring_end_date",
  "created_by": { "id", "name" }, "created_at"
}]
```
**Notes:** `?category=AI_TOOLS&is_recurring=true`

---

### POST /api/projects/:projectId/costs
**Description:** Add a non-human cost entry.
**Auth:** CEO, CTO, DM (own portfolio), PM (own portfolio), Finance
**Scope:** OWN_PORTFOLIO for DM/PM
**Request Body:**
```json
{
  "description": "string*",
  "category": "AI_TOOLS|CLOUD_INFRA|DEVICES|THIRD_PARTY_LICENSE|OTHER *",
  "amount": "decimal* > 0",
  "currency": "string* ISO 4217",
  "exchange_rate": "decimal > 0 (auto 1.0 for INR)",
  "cost_date": "date*",
  "is_recurring": "boolean default false",
  "recurring_end_date": "date (required if recurring)"
}
```
**Validations:** All 5 FSD §11 NonHumanCost validations.
**Notes:** `amount_inr` computed server-side. Audit logged.

---

### GET /api/projects/:projectId/costs/:id
**Description:** Get a specific cost entry.
**Auth:** Same as list endpoint.
**Response:** Full cost object.

---

### PUT /api/projects/:projectId/costs/:id
**Description:** Update a cost entry.
**Auth:** CEO, CTO, DM (own portfolio), PM (own portfolio), Finance
**Scope:** OWN_PORTFOLIO for DM/PM
**Request Body:** Any subset of cost fields.
**Validations:** All 5 validations re-applied.
**Notes:** `amount_inr` recomputed on save. Audit logged.

---

### DELETE /api/projects/:projectId/costs/:id
**Description:** Delete a cost entry.
**Auth:** CEO, CTO, DM (own portfolio), PM (own portfolio), Finance
**Scope:** OWN_PORTFOLIO for DM/PM
**Response:** `{ "success": true }`
**Notes:** Audit logged.

---

### GET /api/projects/:projectId/costs/summary
**Description:** Aggregated cost summary for a project.
**Auth:** Same as list; Finance restricted fields apply.
**Response:**
```json
{
  "total_inr": decimal,
  "by_category": { "AI_TOOLS": decimal, "CLOUD_INFRA": decimal, ... },
  "one_time_inr": decimal,
  "recurring_monthly_inr": decimal
}
```

---

### POST /api/jobs/recurring-costs
**Description:** Monthly job (1st of each month) that generates cost entries for active recurring costs.
**Auth:** Internal/admin only
**Response:** `{ "generated_count": int }`
**Notes:** For each active recurring cost where `cost_date <= today <= recurring_end_date`, creates a new cost entry with `cost_date = first of current month`.
