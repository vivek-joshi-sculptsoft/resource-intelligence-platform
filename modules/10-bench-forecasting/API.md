# Module 10: Bench & Availability Forecasting — API Endpoints

All endpoints are read-only.

## Endpoints

### GET /api/bench
**Description:** List all resources currently on bench (0 ACTIVE assignments).
**Auth:** All authenticated roles. Bench cost fields (Phase 2) restricted to CEO/CTO/Finance.
**Scope:** ALL
**Response:**
```json
[{
  "id", "name", "designation", "technical_expertise", "tags": ["string"],
  "days_on_bench": int,
  "bench_start_date": date,
  "daily_bench_cost_inr": decimal | null,   // Phase 2; null for unauthorized roles
  "total_bench_cost_inr": decimal | null    // Phase 2; null for unauthorized roles
}]
```
**Notes:** `days_on_bench` always shown. Cost fields null in Phase 1 and for unauthorized roles.

---

### GET /api/bench/summary
**Description:** Aggregated bench stats for the company dashboard widget.
**Auth:** All authenticated roles. Cost fields restricted.
**Scope:** ALL
**Response:**
```json
{
  "bench_count": int,
  "total_bench_cost_inr": decimal | null,  // Phase 2
  "resources": [{ "name", "days_on_bench" }]
}
```

---

### GET /api/availability/upcoming
**Description:** Resources with assignment end_dates within a configurable window.
**Auth:** All authenticated roles.
**Scope:** ALL
**Response:**
```json
[{
  "resource": { "id", "name", "designation" },
  "project": { "id", "name" },
  "allocation_pct": int,
  "end_date": date,
  "days_remaining": int
}]
```
**Notes:** `?window=30|60|90` — default 30 days.

---

### GET /api/availability/partial
**Description:** Resources with total allocation < 100% (at least one active assignment).
**Auth:** All authenticated roles.
**Scope:** ALL
**Response:**
```json
[{
  "id", "name", "designation",
  "total_allocation_pct": int,
  "spare_capacity_pct": int,
  "projects": [{ "id", "name" }]
}]
```
