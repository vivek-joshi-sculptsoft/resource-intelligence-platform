# Module 07: Utilization Dashboards — API Endpoints

All endpoints are read-only aggregations. No writes. Financial fields return `null` in Phase 1 and for unauthorized roles.

## Endpoints

### GET /api/dashboard/company
**Description:** Company-wide aggregated metrics.
**Auth:** CEO, CTO only (VIEW ALL)
**Scope:** ALL
**Response:**
```json
{
  "billable_utilization_pct": decimal,
  "total_active_resources": int,
  "bench_count": int,
  "bench_resources": [{ "id", "name", "designation", "days_on_bench" }],
  "shadow_count": int,
  "shadow_total_allocation_pct": int,
  "active_project_count": int,
  "active_projects_by_type": { "FIXED_PRICE": int, "TIME_AND_MATERIAL": int, "CLIENT_ONBOARDING": int },
  "upcoming_releases_30d": [{ "resource_name", "project_name", "end_date", "days_remaining" }],
  "overdue_milestones_count": int,         // Phase 2
  "overdue_milestones": [...],             // Phase 2
  "projected_revenue_inr": decimal,        // Phase 2 — null in Phase 1
  "actual_revenue_inr": decimal,           // Phase 2 — null in Phase 1
  "total_cost_inr": decimal               // Phase 2 — null in Phase 1
}
```

---

### GET /api/dashboard/dm
**Description:** Delivery manager's portfolio metrics.
**Auth:** DM (OWN_PORTFOLIO), CEO, CTO
**Scope:** OWN_PORTFOLIO for DM (projects where dm_id = current user)
**Response:**
```json
{
  "portfolio_utilization_pct": decimal,
  "active_project_count": int,
  "resource_count": int,
  "bench_count": int,
  "upcoming_releases_30d": [...],
  "delivery_delays": [...],               // Phase 2 milestone delays
  "projected_revenue_inr": decimal,       // Phase 2
  "total_cost_inr": decimal              // Phase 2
}
```

---

### GET /api/clients/:clientId/dashboard
**Description:** Client-level aggregated metrics (used by Module 02).
**Auth:** CEO, CTO; DM (own portfolio); Finance, HR
**Scope:** Per role
**Response:**
```json
{
  "active_resource_count": int,
  "active_project_count": int,
  "project_count_by_type": { ... },
  "total_monthly_billing_inr": decimal,   // Phase 2
  "total_cost_inr": decimal,             // Phase 2
  "aggregate_margin_inr": decimal,       // Phase 2 — restricted to CEO/CTO/Finance/DM(cfg)
  "aggregate_margin_pct": decimal        // Phase 2 — restricted
}
```

---

### GET /api/projects/:projectId/financials
**Description:** Project financial summary.
**Auth:** CEO, CTO, Finance (EDIT ALL); DM (OWN_PORTFOLIO, configurable)
**Scope:** OWN_PORTFOLIO for DM
**Response:**
```json
{
  "resource_cost_inr": decimal,           // Phase 2
  "non_human_cost_inr": decimal,          // Phase 2
  "total_cost_inr": decimal,             // Phase 2
  "projected_revenue_inr": decimal,       // Phase 2
  "actual_revenue_inr": decimal,          // Phase 2
  "projected_margin_inr": decimal,        // Phase 2
  "projected_margin_pct": decimal,        // Phase 2
  "actual_margin_inr": decimal,           // Phase 2
  "actual_margin_pct": decimal           // Phase 2
}
```

---

### GET /api/dashboard/availability
**Description:** Resource availability view — visible to ALL users.
**Auth:** All authenticated roles including Engineer
**Scope:** ALL (visibility of project names applies; financial fields excluded for Engineer)
**Response:**
```json
{
  "bench": [{ "id", "name", "designation", "technical_expertise", "days_on_bench", "tags" }],
  "partial": [{ "id", "name", "total_allocation_pct", "spare_capacity_pct", "projects": ["name"] }],
  "releasing_soon": [{ "name", "project_name", "allocation_pct", "end_date", "days_remaining" }],
  "fully_allocated": [{ "name", "total_allocation_pct", "projects": ["name"] }]
}
```
**Notes:** `?window=30|60|90` for releasing_soon filter.
