# Business Rules — Canonical Calculations & Formulas

> **Single source of truth** for all monetary and utilization calculations.
> Extracted from FSD §7 (Calculations), FSD §8 (Auto-Release), and FSD §11 (Designation Resolution).
> Never calculate margins, revenue, cost, or utilization differently than defined here — even if a "better" formula seems possible.

All constants (working_days_per_month = 22, working_hours_per_day = 8, etc.) come from the **SystemConfig** entity — no hardcoded magic numbers.

---

## 7.1 Resource Utilization

```
Total Allocation (resource)    = SUM(allocation_pct) across all ACTIVE assignments
Billable Allocation (resource) = SUM(billability_pct) where is_shadow = false
Utilization Rate (resource)    = Billable Allocation / 100 × 100%
Company Utilization            = SUM(all billable alloc) / (active_resource_count × 100) × 100%
```

---

## 7.2 Project Cost (Monthly)

```
Resource Cost        = SUM(loaded_cost_monthly × allocation_pct / 100) for all ACTIVE assignments
Non-Human Cost (INR) = SUM(amount_inr for one-time in month) + SUM(amount_inr for active recurring)
Total Project Cost   = Resource Cost + Non-Human Cost
```

> Shadow resources contribute to **cost** but NOT to projected revenue.

---

## 7.3 Projected Revenue (Monthly)

```
Per Assignment            = billability_pct / 100 × working_days × 8 × billing_rate
Project Projected Revenue = SUM(per-assignment) for non-shadow ACTIVE assignments
Projected Revenue INR     = Projected Revenue × latest_exchange_rate (or 1.0 if INR)
```

- `working_days` default = 22 (SystemConfig `system.working_days_per_month`).
- `8` = working hours per day (SystemConfig `system.working_hours_per_day`).

---

## 7.4 Actual Revenue

```
Actual Revenue (project, period) = SUM(invoice.amount_inr) where status ∈ {APPROVED, PAID}
```

Source of truth for financial reporting. **Not** calculated from allocation.

---

## 7.5 Margin

```
Projected Margin = Projected Revenue (INR) − Total Project Cost
Actual Margin    = Actual Revenue (INR) − Total Project Cost
Margin %         = Margin / Revenue × 100
```

- **Client-level:** sum across all the client's projects.
- **Company-level:** sum across all projects.

---

## 7.6 Bench Cost

```
Daily Bench Cost = loaded_cost_monthly / 22
Total Bench Cost = Daily Cost × days_on_bench
```

> **Bench start** = max(released_at) of last assignment, or `date_of_joining` if never assigned.
> Bench = resource with 0% total allocation (0 ACTIVE assignments).

---

## 7.7 Exchange Rate Conversion

```
amount_inr = amount × exchange_rate
```

- Exchange rate = 1 unit of billing currency = X INR.
- **Manually entered** at invoice/cost entry time. Never auto-fetched.
- Auto-set to **1.0** for INR (field disabled in UI).

---

## 8. Auto-Release Logic

Scheduled daily job (midnight IST). Processes all assignments where `end_date ≤ today` and `status = ACTIVE`.

```
FOR EACH assignment WHERE status = 'ACTIVE' AND end_date IS NOT NULL AND end_date <= TODAY:
    SET assignment.status = 'AUTO_RELEASED'
    SET assignment.released_at = end_date + '23:59:59'
    CREATE alert(type: 'ASSIGNMENT_AUTO_RELEASED', recipients: [PM, DM])
    INSERT INTO audit_log(...)
```

> **Edge Case: Extension on Release Day**
> If the PM extends `end_date` before the job runs, the job skips that assignment (end_date is now in the future). If the job already ran, the PM must create a new assignment (released assignments cannot be modified).

### Manual Release (FSD §6.1)

| Transition | Trigger | Side Effects |
|---|---|---|
| ACTIVE → RELEASED | PM manually releases | Set released_at = now(). Recalculate total allocation. If before end_date, log as early release. |
| ACTIVE → AUTO_RELEASED | Daily job: end_date ≤ today | Set released_at = end_date midnight. Fire alert to PM and DM. Recalculate total allocation. |

### Project Completion Cascade (FSD §6.4)

When a project becomes COMPLETED or CANCELLED: all ACTIVE assignments are auto-released. No new assignments can be created.

---

## 11. Designation Resolution (Fallback Rule)

> **Fallback Rule**
> When displaying a resource's role on a project: use `assignment.project_designation` if set, else `resource.designation`. Same for expertise (`assignment.project_expertise` → `resource.technical_expertise`). **All views, search, and filters must respect this fallback order.**

---

## Cross-References (PRD §5 / §4.7)

```
Total Project Cost = Resource Costs (Loaded Cost × Allocation %) + Non-Human Costs (INR)
```

| Term | Definition |
|---|---|
| Projected Revenue | billability % × billing rate × working days, converted to INR. Expected income before invoicing. |
| Actual Revenue | Invoice amount entered during invoicing (original currency × manual exchange rate = INR). Source of truth. |
| Projected Margin | Projected Revenue − Total Cost (resource + non-human + shadow). |
| Actual Margin | Actual Revenue (invoice INR) − Total Cost. |
| Utilization Rate | Billable allocation ÷ total available capacity, as a percentage. |
