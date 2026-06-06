# Module 06: Non-Human Costs — Background Jobs & Async Processing

## Overview

This module runs a single monthly scheduled job that automatically generates new cost entries for active recurring costs (e.g., monthly cloud subscriptions, ongoing license fees). The job ensures recurring expenses are tracked each month without manual re-entry, feeding accurate cost data into the financial engine (Module 08).

## Job Summary

| Job | Type | Schedule / Trigger | Entities | Side Effects | Phase |
|---|---|---|---|---|---|
| Recurring Cost Processing | Scheduled | Monthly, 1st of each month at midnight IST | NonHumanCost | AuditLog | Phase 2 |

---

## Scheduled Jobs

### Job: Recurring Cost Processing

**Schedule**

| Attribute | Value |
|---|---|
| Cron Expression | `0 0 1 * *` |
| Human Readable | Every 1st of the month at 00:00 (midnight) |
| Timezone | Asia/Kolkata |

**What It Processes**

```sql
SELECT *
FROM non_human_cost
WHERE is_recurring = true
  AND cost_date <= CURRENT_DATE
  AND recurring_end_date >= CURRENT_DATE;
```

> This selects all recurring cost templates whose recurrence window includes the current date. `cost_date` is the original start date of the recurring cost, and `recurring_end_date` is when recurrence stops.

**Processing Logic**

```pseudocode
FUNCTION process_recurring_costs():
    current_month_start = FIRST_DAY_OF(CURRENT_MONTH)  -- e.g., 2026-07-01

    candidates = QUERY non_human_cost
                 WHERE is_recurring = true
                   AND cost_date <= CURRENT_DATE
                   AND recurring_end_date >= CURRENT_DATE

    created_count = 0

    FOR EACH parent_cost IN candidates:

        -- Idempotency check: skip if entry for this month already exists
        existing = QUERY non_human_cost
                   WHERE project_id = parent_cost.project_id
                     AND description = parent_cost.description
                     AND category = parent_cost.category
                     AND cost_date = current_month_start
                     AND amount = parent_cost.amount
                     AND currency = parent_cost.currency
        IF existing IS NOT EMPTY:
            LOG "Skipping duplicate for project {parent_cost.project_id}, cost '{parent_cost.description}' for {current_month_start}"
            CONTINUE

        -- Create new monthly cost entry
        new_cost = CREATE NonHumanCost(
            id: NEW UUID,
            project_id: parent_cost.project_id,
            description: parent_cost.description,
            category: parent_cost.category,
            amount: parent_cost.amount,
            currency: parent_cost.currency,
            exchange_rate: parent_cost.exchange_rate,
            amount_inr: parent_cost.amount * parent_cost.exchange_rate,
            cost_date: current_month_start,
            is_recurring: false,           -- Generated entries are one-time snapshots
            recurring_end_date: NULL,
            created_by: 'SYSTEM'
        )

        -- Audit log
        INSERT INTO audit_log(
            entity_type: 'NonHumanCost',
            entity_id: new_cost.id,
            action: 'CREATE',
            field_name: NULL,
            old_value: NULL,
            new_value: JSON_SERIALIZE(new_cost),
            changed_by: 'SYSTEM',
            changed_at: NOW()
        )

        created_count = created_count + 1

    LOG "Recurring cost processing completed. Created {created_count} entries from {candidates.count} recurring templates."
```

**Side Effects**

| Side Effect | Details |
|---|---|
| New NonHumanCost rows | One new cost entry per active recurring template, with `cost_date = 1st of current month` and `is_recurring = false` |
| Audit log entries | One `CREATE` audit row per generated cost entry, with `changed_by = 'SYSTEM'` |
| Financial recalculation | Downstream reads (Module 08) will include these new entries in Total Project Cost for the current month |

**Error Handling**

| Scenario | Behavior |
|---|---|
| Single cost entry fails to create | Log error with parent cost ID and project ID, continue processing remaining recurring costs. Do not abort the batch. |
| Database connection lost | Retry with exponential backoff (3 attempts, 5s/15s/45s). If all retries fail, log CRITICAL error and alert ops. |
| Parent project is COMPLETED/CANCELLED | Still generate the entry if within the recurrence window. The recurring cost was agreed upon regardless of project status. Finance can delete if no longer applicable. |
| Exchange rate stale | Use the exchange rate from the parent recurring cost template. If Finance needs to update the rate, they edit the parent template before the 1st. |
| Job runs late (e.g., 2nd of month) | Still uses `FIRST_DAY_OF(CURRENT_MONTH)` as `cost_date`. Idempotency guard prevents duplicates if manually triggered after a late run. |

**Idempotency**

Guard: Before creating each entry, the job checks if a cost entry with the same `project_id`, `description`, `category`, `cost_date` (1st of current month), `amount`, and `currency` already exists. If found, the entry is skipped. This makes the job safe to re-run manually or after partial failure.

**Configuration**

No SystemConfig keys used. The schedule is fixed (1st of each month). The recurrence window is determined by the `cost_date` and `recurring_end_date` fields on each recurring cost entry.

**Testing**

- [ ] Normal processing: active recurring cost generates a new entry on the 1st with correct fields
- [ ] Generated entry has `cost_date = 1st of current month`
- [ ] Generated entry has `is_recurring = false` (it is a one-time snapshot)
- [ ] Generated entry has `amount_inr = amount * exchange_rate` (recomputed)
- [ ] All fields copied correctly: `project_id`, `description`, `category`, `amount`, `currency`, `exchange_rate`
- [ ] `created_by = 'SYSTEM'` on generated entries
- [ ] Audit log entry created for each generated cost with `action = 'CREATE'` and `changed_by = 'SYSTEM'`
- [ ] Idempotency: running the job twice in the same month does NOT create duplicate entries
- [ ] Expired recurring cost: `recurring_end_date < CURRENT_DATE` is NOT processed
- [ ] Future recurring cost: `cost_date > CURRENT_DATE` is NOT processed (recurrence hasn't started yet)
- [ ] Multiple recurring costs: job processes all qualifying templates in a single run
- [ ] Partial failure: if one entry fails, remaining entries are still processed
- [ ] Multi-currency: recurring costs in USD, EUR, etc. are processed correctly with their exchange rates
- [ ] Edge: recurring cost where `recurring_end_date = CURRENT_DATE` IS processed (inclusive boundary)
- [ ] Edge: recurring cost where `cost_date = CURRENT_DATE` IS processed (inclusive boundary)
