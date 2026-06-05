# Access Control Matrix

> Extracted from FSD §10 (Access Control Rules) and PRD §6 (Role-Based Access Matrix).
> Every API endpoint must check access against this file. See `ENTITIES.md §2.2` for RolePermission entity definition.

---

## Scope Rules (FSD §10)

| Role | Project Scope | Resource Scope |
|---|---|---|
| CEO, CTO | All projects | All resources |
| Finance | All (financial data only) | All (cost data only) |
| DM | `project.dm_id = current user` | Resources on DM's projects |
| PM | `project.pm_id = current user` | Resources on PM's projects |
| HR | All (profiles only) | All (profiles, no financials) |
| Engineer | Own ACTIVE assignments | Self + availability view (all) |

Scope is enforced as a **WHERE clause at database query level**, not post-fetch filtering.

---

## Field-Level Restrictions (FSD §10)

| Field | Visible To | Enforcement |
|---|---|---|
| `loaded_cost_monthly` | CEO, CTO, Finance | API returns `null` for others |
| `billing_rate` | CEO, CTO, Finance, DM (configurable) | API returns `null` if restricted |
| `billability_pct` | CEO, CTO, Finance, DM, PM | Hidden from HR and Engineer |
| `is_shadow` | CEO, CTO, Finance, DM, PM | Hidden from HR and Engineer |
| All margin fields | CEO, CTO, Finance, DM (configurable) | Computed fields omitted |
| `exchange_rate` | CEO, CTO, Finance | Write access: Finance only |

> **Sensitive-field rule:** Restricted fields return `null` — they are NOT omitted from the response (keeps response shape consistent).

---

## Runtime Access Check Algorithm (FSD §2.2)

1. Get `user.role_id`.
2. Look up `RolePermission` where `role_id = user.role_id AND data_type = <requested data type>`.
3. `NONE` → HTTP 403 or omit field. `VIEW` → read-only. `EDIT` → full access.
4. Apply `scope`: `ALL` = no filter, `OWN_PORTFOLIO` = filter by DM/PM assignment, `SELF_ONLY` = filter by own `resource_id`.
5. If `is_configurable = true`, check for user-level override (Phase 3).

---

## Full RolePermission Seed Data (105 rows)

7 roles × 15 data types.

**Legend:** `access_level` = NONE / VIEW / EDIT · `scope` = ALL / OWN_PORTFOLIO / SELF_ONLY · `cfg` = is_configurable

### CEO (15 rows)

| data_type | access_level | scope | cfg |
|---|---|---|---|
| client_profiles | EDIT | ALL | false |
| project_details | EDIT | ALL | false |
| resource_profiles | EDIT | ALL | false |
| allocation | EDIT | ALL | false |
| billability | EDIT | ALL | false |
| billing_rates | VIEW | ALL | false |
| ctc_loaded_cost | VIEW | ALL | false |
| project_margin | VIEW | ALL | false |
| non_human_costs | EDIT | ALL | false |
| shadow_assignments | VIEW | ALL | false |
| resource_availability | VIEW | ALL | false |
| bench_data | VIEW | ALL | false |
| invoicing | VIEW | ALL | false |
| worklogs | VIEW | ALL | false |
| alerts | VIEW | ALL | false |

### CTO (15 rows)

| data_type | access_level | scope | cfg |
|---|---|---|---|
| client_profiles | EDIT | ALL | false |
| project_details | EDIT | ALL | false |
| resource_profiles | EDIT | ALL | false |
| allocation | EDIT | ALL | false |
| billability | EDIT | ALL | false |
| billing_rates | VIEW | ALL | false |
| ctc_loaded_cost | VIEW | ALL | false |
| project_margin | VIEW | ALL | false |
| non_human_costs | EDIT | ALL | false |
| shadow_assignments | VIEW | ALL | false |
| resource_availability | VIEW | ALL | false |
| bench_data | VIEW | ALL | false |
| invoicing | VIEW | ALL | false |
| worklogs | VIEW | ALL | false |
| alerts | VIEW | ALL | false |

### DM — Delivery Manager (15 rows)

| data_type | access_level | scope | cfg |
|---|---|---|---|
| client_profiles | VIEW | OWN_PORTFOLIO | false |
| project_details | EDIT | OWN_PORTFOLIO | false |
| resource_profiles | VIEW | OWN_PORTFOLIO | false |
| allocation | VIEW | OWN_PORTFOLIO | false |
| billability | VIEW | OWN_PORTFOLIO | false |
| billing_rates | VIEW | OWN_PORTFOLIO | true |
| ctc_loaded_cost | NONE | ALL | false |
| project_margin | VIEW | OWN_PORTFOLIO | true |
| non_human_costs | EDIT | OWN_PORTFOLIO | false |
| shadow_assignments | VIEW | OWN_PORTFOLIO | false |
| resource_availability | VIEW | ALL | false |
| bench_data | VIEW | ALL | false |
| invoicing | NONE | ALL | false |
| worklogs | VIEW | OWN_PORTFOLIO | false |
| alerts | VIEW | OWN_PORTFOLIO | false |

### PM — Project Manager (15 rows)

| data_type | access_level | scope | cfg |
|---|---|---|---|
| client_profiles | VIEW | OWN_PORTFOLIO | false |
| project_details | EDIT | OWN_PORTFOLIO | false |
| resource_profiles | VIEW | OWN_PORTFOLIO | false |
| allocation | EDIT | OWN_PORTFOLIO | false |
| billability | EDIT | OWN_PORTFOLIO | false |
| billing_rates | NONE | ALL | false |
| ctc_loaded_cost | NONE | ALL | false |
| project_margin | NONE | ALL | false |
| non_human_costs | EDIT | OWN_PORTFOLIO | false |
| shadow_assignments | VIEW | OWN_PORTFOLIO | false |
| resource_availability | VIEW | ALL | false |
| bench_data | NONE | ALL | false |
| invoicing | NONE | ALL | false |
| worklogs | VIEW | OWN_PORTFOLIO | false |
| alerts | VIEW | OWN_PORTFOLIO | false |

### FINANCE (15 rows)

| data_type | access_level | scope | cfg |
|---|---|---|---|
| client_profiles | VIEW | ALL | false |
| project_details | VIEW | ALL | false |
| resource_profiles | VIEW | ALL | false |
| allocation | VIEW | ALL | false |
| billability | VIEW | ALL | false |
| billing_rates | VIEW | ALL | false |
| ctc_loaded_cost | VIEW | ALL | false |
| project_margin | VIEW | ALL | false |
| non_human_costs | EDIT | ALL | false |
| shadow_assignments | VIEW | ALL | false |
| resource_availability | VIEW | ALL | false |
| bench_data | VIEW | ALL | false |
| invoicing | EDIT | ALL | false |
| worklogs | NONE | ALL | false |
| alerts | VIEW | ALL | false |

### HR (15 rows)

| data_type | access_level | scope | cfg |
|---|---|---|---|
| client_profiles | VIEW | ALL | false |
| project_details | VIEW | ALL | false |
| resource_profiles | EDIT | ALL | false |
| allocation | VIEW | ALL | false |
| billability | NONE | ALL | false |
| billing_rates | NONE | ALL | false |
| ctc_loaded_cost | NONE | ALL | false |
| project_margin | NONE | ALL | false |
| non_human_costs | NONE | ALL | false |
| shadow_assignments | NONE | ALL | false |
| resource_availability | VIEW | ALL | false |
| bench_data | VIEW | ALL | false |
| invoicing | NONE | ALL | false |
| worklogs | NONE | ALL | false |
| alerts | VIEW | ALL | false |

### ENGINEER (15 rows)

| data_type | access_level | scope | cfg |
|---|---|---|---|
| client_profiles | NONE | ALL | false |
| project_details | NONE | ALL | false |
| resource_profiles | VIEW | SELF_ONLY | false |
| allocation | VIEW | SELF_ONLY | false |
| billability | NONE | ALL | false |
| billing_rates | NONE | ALL | false |
| ctc_loaded_cost | NONE | ALL | false |
| project_margin | NONE | ALL | false |
| non_human_costs | NONE | ALL | false |
| shadow_assignments | NONE | ALL | false |
| resource_availability | VIEW | ALL | false |
| bench_data | VIEW | ALL | false |
| invoicing | NONE | ALL | false |
| worklogs | EDIT | SELF_ONLY | false |
| alerts | NONE | ALL | false |

---

## Alert Recipients Quick Reference (FSD §12)

| Alert Type | Recipients |
|---|---|
| CONTRACT_EXPIRY | DM (OWN_PORTFOLIO), CTO, CEO |
| BENCH_DURATION | DM (OWN_PORTFOLIO), CTO, HR |
| OVER_ALLOCATION | DM (OWN_PORTFOLIO), PM (OWN_PORTFOLIO) |
| MILESTONE_OVERDUE | PM (OWN_PORTFOLIO), DM (OWN_PORTFOLIO) |
| UTILIZATION_DROP | CTO, CEO |
| ASSIGNMENT_AUTO_RELEASED | PM (OWN_PORTFOLIO), DM (OWN_PORTFOLIO) |
