# Module 05: Allocation Tracking — Background Jobs & Async Processing

## Overview

This module runs a single daily scheduled job that automatically releases assignments whose `end_date` has passed. The auto-release job is the primary mechanism for ending time-bound assignments without manual intervention, and is critical for keeping utilization and bench metrics accurate.

## Job Summary

| Job | Type | Schedule / Trigger | Entities | Side Effects | Phase |
|---|---|---|---|---|---|
| Auto-Release Assignments | Scheduled | Daily midnight IST | Assignment | Alert (ASSIGNMENT_AUTO_RELEASED), AuditLog | Phase 1 |

---

## Scheduled Jobs

### Job: Auto-Release Assignments

> See FSD §8 and `shared/BUSINESS-RULES.md §8` for the canonical algorithm.

**Schedule**

| Attribute | Value |
|---|---|
| Cron Expression | `0 0 * * *` |
| Human Readable | Every day at 00:00 (midnight) |
| Timezone | Asia/Kolkata |

**What It Processes**

```sql
SELECT *
FROM assignment
WHERE status = 'ACTIVE'
  AND end_date IS NOT NULL
  AND end_date <= CURRENT_DATE;
```

**Processing Logic**

```pseudocode
FUNCTION auto_release_assignments():
    candidates = QUERY assignments WHERE status = 'ACTIVE'
                                     AND end_date IS NOT NULL
                                     AND end_date <= CURRENT_DATE

    FOR EACH assignment IN candidates:
        -- Update assignment status
        assignment.status = 'AUTO_RELEASED'
        assignment.released_at = assignment.end_date + TIME '23:59:59'
        SAVE assignment

        -- Look up project PM and DM
        project = LOOKUP project BY assignment.project_id
        pm_user = LOOKUP user BY project.pm_id
        dm_user = LOOKUP user BY project.dm_id

        -- Create alert for PM
        CREATE Alert(
            type: 'ASSIGNMENT_AUTO_RELEASED',
            severity: 'INFO',
            title: '{resource.name} auto-released from {project.name}',
            message: 'Assignment ended on {assignment.end_date}. Resource is now available for reallocation.',
            recipient_user_id: pm_user.id,
            entity_type: 'Assignment',
            entity_id: assignment.id
        )

        -- Create alert for DM (if different from PM)
        IF dm_user.id != pm_user.id:
            CREATE Alert(
                type: 'ASSIGNMENT_AUTO_RELEASED',
                severity: 'INFO',
                title: '{resource.name} auto-released from {project.name}',
                message: 'Assignment ended on {assignment.end_date}. Resource is now available for reallocation.',
                recipient_user_id: dm_user.id,
                entity_type: 'Assignment',
                entity_id: assignment.id
            )

        -- Audit log: one row per changed field
        INSERT INTO audit_log(
            entity_type: 'Assignment',
            entity_id: assignment.id,
            action: 'UPDATE',
            field_name: 'status',
            old_value: '"ACTIVE"',
            new_value: '"AUTO_RELEASED"',
            changed_by: 'SYSTEM',
            changed_at: NOW()
        )
        INSERT INTO audit_log(
            entity_type: 'Assignment',
            entity_id: assignment.id,
            action: 'UPDATE',
            field_name: 'released_at',
            old_value: 'null',
            new_value: '"end_date + 23:59:59"',
            changed_by: 'SYSTEM',
            changed_at: NOW()
        )

    LOG "Auto-release job completed. Processed {candidates.count} assignments."
```

**Side Effects**

| Side Effect | Details |
|---|---|
| Assignment status change | `ACTIVE` -> `AUTO_RELEASED`, `released_at` set to `end_date + 23:59:59` |
| Alert creation | One `ASSIGNMENT_AUTO_RELEASED` alert per recipient (PM and DM) per released assignment |
| Audit log entries | Two audit rows per released assignment: `status` change and `released_at` change. `changed_by = 'SYSTEM'` |
| Utilization recalculation | Downstream reads (Module 07) will reflect lower allocation for the resource |

**Error Handling**

| Scenario | Behavior |
|---|---|
| Single assignment fails to update | Log error with assignment ID, continue processing remaining assignments. Do not abort the batch. |
| Database connection lost | Retry with exponential backoff (3 attempts, 5s/15s/45s). If all retries fail, log CRITICAL error and alert ops. |
| Alert creation fails | Log warning. The assignment status update must still commit — alert failure is non-blocking. |
| Job already running (overlap) | Skip execution. Use a distributed lock or job-level mutex to prevent concurrent runs. |

**Idempotency**

Guard: The query filters on `status = 'ACTIVE'`. Once an assignment is processed, its status becomes `AUTO_RELEASED`, so re-running the job will not select it again. Safe to re-run after partial failure.

**Configuration**

No SystemConfig keys used. The job has a fixed schedule (daily midnight IST). The filtering condition (`end_date <= CURRENT_DATE`) is date-based and requires no configurable threshold.

**Testing**

- [ ] Normal release: assignment with `end_date = yesterday` and `status = ACTIVE` is auto-released
- [ ] `released_at` is set to `end_date + 23:59:59` (not `NOW()`)
- [ ] Alert created for PM with correct type, entity_type, and entity_id
- [ ] Alert created for DM with correct type, entity_type, and entity_id
- [ ] If PM and DM are the same user, only one alert is created (no duplicate)
- [ ] Audit log entries created: one for `status`, one for `released_at`, both with `changed_by = 'SYSTEM'`
- [ ] Extension before job runs: assignment with `end_date` extended to future is NOT processed
- [ ] Already released: assignment with `status = AUTO_RELEASED` or `RELEASED` is NOT processed
- [ ] No `end_date`: assignment with `end_date = NULL` is NOT processed
- [ ] Multiple assignments: job processes all qualifying assignments in a single run
- [ ] Partial failure: if one assignment fails, remaining assignments are still processed
- [ ] Idempotency: running the job twice on the same day produces the same result (no duplicates)
- [ ] `end_date = today`: assignment IS processed (end_date <= CURRENT_DATE includes today)

---

## Edge Cases

### Extension on Release Day

If the PM extends `end_date` before the job runs at midnight, the job skips that assignment because `end_date` is now in the future. If the job has already run and the assignment is `AUTO_RELEASED`, the PM cannot modify it — they must create a new assignment. This is by design (see FSD §8).

### Project Completion Cascade vs. Auto-Release

If a project is marked COMPLETED or CANCELLED (Module 03), all ACTIVE assignments are immediately released with `status = RELEASED`. The auto-release job will not pick these up because their status is already `RELEASED`, not `ACTIVE`. No conflict between the two mechanisms.
