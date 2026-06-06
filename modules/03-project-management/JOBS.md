# Module 03: Project Management — Background Jobs & Async Processing

## Overview

This module has no scheduled jobs. It has one event-triggered background process: when a project's status changes to COMPLETED or CANCELLED, all ACTIVE assignments on that project are immediately released. This cascade ensures resource availability is updated in real time and prevents orphaned allocations on closed projects.

## Job Summary

| Job | Type | Schedule / Trigger | Entities | Side Effects | Phase |
|---|---|---|---|---|---|
| Project Completion Cascade | Event-triggered | Project status changed to COMPLETED or CANCELLED | Assignment, AuditLog | Assignment release, audit logging | Phase 1 |

---

## Event-Triggered Background Jobs

### Trigger: Project Status Change to COMPLETED or CANCELLED

> See FSD §6.4 and `shared/BUSINESS-RULES.md §8 — Project Completion Cascade`.

**When It Fires**

| Attribute | Value |
|---|---|
| Event | Project UPDATE where `status` field changes |
| Condition | New status is `COMPLETED` or `CANCELLED` |
| Source Module | Module 03 (Project Management) — project status update endpoint |
| Execution | Synchronous — runs within the same transaction as the project status update |

**Processing Logic**

```pseudocode
FUNCTION on_project_status_change(project, old_status, new_status):
    IF new_status NOT IN ('COMPLETED', 'CANCELLED'):
        RETURN  -- Only cascade on completion or cancellation

    -- Find all ACTIVE assignments on this project
    active_assignments = QUERY assignments
                         WHERE project_id = project.id
                           AND status = 'ACTIVE'

    IF active_assignments IS EMPTY:
        LOG "No active assignments to release for project {project.id}."
        RETURN

    current_time = NOW()

    FOR EACH assignment IN active_assignments:
        old_assignment_status = assignment.status  -- Always 'ACTIVE'

        -- Release the assignment
        assignment.status = 'RELEASED'
        assignment.released_at = current_time
        SAVE assignment

        -- Audit log: status change
        INSERT INTO audit_log(
            entity_type: 'Assignment',
            entity_id: assignment.id,
            action: 'UPDATE',
            field_name: 'status',
            old_value: '"ACTIVE"',
            new_value: '"RELEASED"',
            changed_by: CURRENT_USER.id,
            changed_at: current_time
        )

        -- Audit log: released_at change
        INSERT INTO audit_log(
            entity_type: 'Assignment',
            entity_id: assignment.id,
            action: 'UPDATE',
            field_name: 'released_at',
            old_value: 'null',
            new_value: '"' + current_time + '"',
            changed_by: CURRENT_USER.id,
            changed_at: current_time
        )

    LOG "Project {project.id} status changed to {new_status}. Released {active_assignments.count} active assignments."
```

**Side Effects**

| Side Effect | Details |
|---|---|
| Assignment status change | All ACTIVE assignments on the project set to `status = 'RELEASED'`, `released_at = NOW()` |
| Audit log entries | Two audit rows per released assignment: `status` change and `released_at` change. `changed_by` = the user who changed the project status. |
| Utilization recalculation | Downstream reads (Module 07) will reflect reduced allocation for all affected resources |
| Bench impact | Resources with no remaining ACTIVE assignments after this cascade become "on bench" and may trigger bench duration alerts (Module 12, Phase 3) |
| New assignments blocked | After COMPLETED or CANCELLED, no new assignments can be created on this project (enforced by Module 05 validation: "Cannot create assignment on a non-active project") |

**Error Handling**

| Scenario | Behavior |
|---|---|
| Single assignment fails to release | Log error with assignment ID. Continue processing remaining assignments. The project status change should still commit. |
| Transaction failure | If the cascade is in the same transaction as the project update, the entire operation rolls back (project status reverts too). This prevents inconsistent state where a project is COMPLETED but assignments are still ACTIVE. |
| No active assignments | No error. Log info message and proceed. The project status change completes normally. |
| Assignment already RELEASED/AUTO_RELEASED | Not selected by the query (filters on `status = 'ACTIVE'`). No action needed. |

**Idempotency**

Guard: The query filters on `status = 'ACTIVE'`. If the cascade runs again (e.g., due to a retry), assignments already set to `RELEASED` will not be selected. The operation is naturally idempotent.

**Configuration**

No SystemConfig keys used. The cascade is hardcoded to fire on COMPLETED and CANCELLED transitions as defined in FSD §6.4.

**Testing**

- [ ] All ACTIVE assignments released when project status changes to COMPLETED
- [ ] All ACTIVE assignments released when project status changes to CANCELLED
- [ ] Released assignments have `status = 'RELEASED'` (not `AUTO_RELEASED` -- that is for the daily job only)
- [ ] Released assignments have `released_at = NOW()` (not end_date-based)
- [ ] Audit log created for each released assignment with `changed_by` = the user who changed the project status
- [ ] Audit log has two rows per assignment: one for `status`, one for `released_at`
- [ ] Already RELEASED or AUTO_RELEASED assignments are NOT affected
- [ ] No error when project has zero active assignments
- [ ] New assignments cannot be created after project is COMPLETED (validation in Module 05)
- [ ] New assignments cannot be created after project is CANCELLED (validation in Module 05)
- [ ] Status change to ON_HOLD does NOT trigger cascade (only COMPLETED and CANCELLED)
- [ ] Status change from ON_HOLD to ACTIVE does NOT trigger cascade
- [ ] Transaction atomicity: if cascade fails, project status change also rolls back
- [ ] Multiple resources released: each resource's utilization updated correctly downstream
