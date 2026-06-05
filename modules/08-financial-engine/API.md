# Module 08: Financial Engine — API Endpoints

All calculation endpoints are read-only aggregations. Write operations for `loaded_cost_monthly` and `billing_rate` are handled by Module 04 and Module 05 endpoints respectively.

## Endpoints

### GET /api/projects/:projectId/financials
**Description:** Full financial breakdown for a project.
**Auth:** CEO, CTO, Finance (VIEW ALL); DM (OWN_PORTFOLIO, configurable for margin). Reference `shared/ACCESS-MATRIX.md` (`project_margin`, `ctc_loaded_cost`, `billing_rates`).
**Scope:** OWN_PORTFOLIO for DM
**Response:**
```json
{
  "resource_cost_inr": decimal | null,
  "non_human_cost_inr": decimal | null,
  "total_cost_inr": decimal | null,
  "projected_revenue_inr": decimal | null,
  "actual_revenue_inr": decimal | null,
  "projected_margin_inr": decimal | null,
  "projected_margin_pct": decimal | null,
  "actual_margin_inr": decimal | null,
  "actual_margin_pct": decimal | null,
  "resource_cost_breakdown": [{
    "resource_name": string,
    "allocation_pct": int,
    "loaded_cost_monthly": decimal | null,
    "cost_contribution_inr": decimal | null
  }],
  "missing_costs": ["resource_name"],       // resources where loaded_cost is null
  "missing_rates": ["resource_name"]        // assignments where billing_rate is null
}
```
**Notes:** Returns `null` for calculations where inputs are missing (e.g., a resource has no loaded_cost_monthly). Lists affected resources in `missing_costs` / `missing_rates`.

---

### GET /api/clients/:clientId/financials
**Description:** Client-level financial aggregation.
**Auth:** CEO, CTO, Finance; DM (OWN_PORTFOLIO, configurable)
**Scope:** Per role
**Response:**
```json
{
  "total_resource_cost_inr": decimal | null,
  "total_non_human_cost_inr": decimal | null,
  "total_cost_inr": decimal | null,
  "total_projected_revenue_inr": decimal | null,
  "total_actual_revenue_inr": decimal | null,
  "projected_margin_inr": decimal | null,
  "projected_margin_pct": decimal | null,
  "actual_margin_inr": decimal | null,
  "actual_margin_pct": decimal | null,
  "per_project": [{ "project_id", "project_name", "total_cost_inr", "projected_revenue_inr", "actual_revenue_inr" }]
}
```

---

### GET /api/dashboard/financials
**Description:** Company-wide financial summary.
**Auth:** CEO, CTO, Finance only
**Scope:** ALL
**Response:**
```json
{
  "total_resource_cost_inr": decimal | null,
  "total_non_human_cost_inr": decimal | null,
  "total_cost_inr": decimal | null,
  "total_projected_revenue_inr": decimal | null,
  "total_actual_revenue_inr": decimal | null,
  "total_projected_margin_inr": decimal | null,
  "total_actual_margin_inr": decimal | null,
  "bench_cost_inr": decimal | null,
  "bench_cost_breakdown": [{ "resource_name", "days_on_bench", "daily_cost_inr", "total_bench_cost_inr" }]
}
```

---

### GET /api/resources/:resourceId/bench-cost
**Description:** Bench cost for a specific resource.
**Auth:** CEO, CTO, Finance only
**Response:**
```json
{
  "days_on_bench": int,
  "daily_bench_cost_inr": decimal | null,
  "total_bench_cost_inr": decimal | null,
  "bench_start_date": date
}
```
**Notes:** `daily_bench_cost_inr = loaded_cost_monthly / 22`. Null if no loaded_cost_monthly set.
