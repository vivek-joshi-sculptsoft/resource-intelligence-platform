# Module 12: Alerts — Background Jobs & Async Processing

## Overview

This module manages six background jobs: four scheduled jobs that run on fixed intervals to detect conditions requiring attention (contract expiry, bench duration, milestone overdue, utilization drop), and two event-triggered jobs that fire in response to specific user or system actions (over-allocation on assignment save, auto-release from Module 05). All jobs create Alert rows — one per recipient per event — and all respect the de-duplication rule to avoid flooding users with repeat notifications.

## Job Summary

| Job | Type | Schedule / Trigger | Entities | Side Effects | Phase |
|---|---|---|---|---|---|
| Contract Expiry Check | Scheduled | Daily midnight IST | Project, Alert | Alert creation | Phase 3 |
| Bench Duration Check | Scheduled | Daily midnight IST | Resource, Assignment, Alert | Alert creation | Phase 3 |
| Milestone Overdue Check | Scheduled | Daily midnight IST | Milestone, Alert | Alert creation | Phase 3 |
| Utilization Drop Check | Scheduled | Weekly, Monday midnight IST | Assignment, Resource, Alert | Alert creation | Phase 3 |
| Over-Allocation Warning | Event-triggered | On assignment save | Assignment, Alert | Alert creation | Phase 3 |
| Assignment Auto-Released | Event-triggered | From Module 05 auto-release job | Assignment, Alert | Alert creation | Phase 3 |

---

## Scheduled Jobs

### Job: Contract Expiry Check

**Schedule**

| Attribute | Value |
|---|---|
| Cron Expression | `0 0 * * *` |
| Human Readable | Every day at 00:00 (midnight) |
| Timezone | Asia/Kolkata |

**What It Processes**

```sql
-- WARNING level: contract expiring within 30 days (but more than 7 days away)
SELECT p.*
FROM project p
WHERE p.type IN ('TIME_AND_MATERIAL', 'CLIENT_ONBOARDING')
  AND p.status = 'ACTIVE'
  AND p.contract_end_date IS NOT NULL
  AND p.contract_end_date <= CURRENT_DATE + INTERVAL (SELECT value FROM system_config WHERE key = 'alert.contract_expiry_days') DAY
  AND p.contract_end_date > CURRENT_DATE + INTERVAL (SELECT value FROM system_config WHERE key = 'alert.contract_expiry_urgent_days') DAY;

-- CRITICAL level: contract expiring within 7 days (or already expired)
SELECT p.*
FROM project p
WHERE p.type IN ('TIME_AND_MATERIAL', 'CLIENT_ONBOARDING')
  AND p.status = 'ACTIVE'
  AND p.contract_end_date IS NOT NULL
  AND p.contract_end_date <= CURRENT_DATE + INTERVAL (SELECT value FROM system_config WHERE key = 'alert.contract_expiry_urgent_days') DAY;
```

**Processing Logic**

```pseudocode
FUNCTION check_contract_expiry():
    warning_days = SystemConfig.get('alert.contract_expiry_days')      -- default: 30
    urgent_days  = SystemConfig.get('alert.contract_expiry_urgent_days') -- default: 7

    -- Find projects with expiring contracts
    projects_warning = QUERY projects
                       WHERE type IN ('TIME_AND_MATERIAL', 'CLIENT_ONBOARDING')
                         AND status = 'ACTIVE'
                         AND contract_end_date IS NOT NULL
                         AND contract_end_date <= TODAY + warning_days
                         AND contract_end_date > TODAY + urgent_days

    projects_critical = QUERY projects
                        WHERE type IN ('TIME_AND_MATERIAL', 'CLIENT_ONBOARDING')
                          AND status = 'ACTIVE'
                          AND contract_end_date IS NOT NULL
                          AND contract_end_date <= TODAY + urgent_days

    -- Determine recipients: DM (of each project), CTO, CEO
    cto_users = QUERY users WHERE role.code = 'CTO'
    ceo_users = QUERY users WHERE role.code = 'CEO'

    FOR EACH project IN projects_warning:
        days_remaining = project.contract_end_date - TODAY
        recipients = [project.dm_id] + cto_users + ceo_users
        recipients = DEDUPLICATE(recipients)

        FOR EACH recipient IN recipients:
            -- De-duplication: skip if unread alert of same type+entity exists
            existing = QUERY alert
                       WHERE type = 'CONTRACT_EXPIRY'
                         AND entity_type = 'Project'
                         AND entity_id = project.id
                         AND recipient_user_id = recipient.id
                         AND is_read = false
            IF existing IS NOT EMPTY:
                CONTINUE

            CREATE Alert(
                type: 'CONTRACT_EXPIRY',
                severity: 'WARNING',
                title: '{project.name} contract expires in {days_remaining} days',
                message: 'Contract end date: {project.contract_end_date}. Review for renewal or extension.',
                recipient_user_id: recipient.id,
                entity_type: 'Project',
                entity_id: project.id
            )

    FOR EACH project IN projects_critical:
        days_remaining = project.contract_end_date - TODAY
        recipients = [project.dm_id] + cto_users + ceo_users
        recipients = DEDUPLICATE(recipients)

        FOR EACH recipient IN recipients:
            existing = QUERY alert
                       WHERE type = 'CONTRACT_EXPIRY'
                         AND entity_type = 'Project'
                         AND entity_id = project.id
                         AND recipient_user_id = recipient.id
                         AND is_read = false
            IF existing IS NOT EMPTY:
                CONTINUE

            CREATE Alert(
                type: 'CONTRACT_EXPIRY',
                severity: 'CRITICAL',
                title: '{project.name} contract expires in {days_remaining} days',
                message: 'URGENT: Contract end date: {project.contract_end_date}. Immediate action required.',
                recipient_user_id: recipient.id,
                entity_type: 'Project',
                entity_id: project.id
            )

    LOG "Contract expiry check completed. Checked {projects_warning.count + projects_critical.count} projects."
```

**Side Effects**

| Side Effect | Details |
|---|---|
| Alert creation | One `CONTRACT_EXPIRY` alert per recipient per project. Severity: `WARNING` at 30-day threshold, `CRITICAL` at 7-day threshold. |
| No entity mutations | This job is read-only against Project. Only writes to Alert. |

**Error Handling**

| Scenario | Behavior |
|---|---|
| Single project fails | Log error with project ID, continue processing remaining projects. |
| SystemConfig key missing | Fall back to hardcoded defaults: `warning_days = 30`, `urgent_days = 7`. Log warning about missing config. |
| Recipient user not found | Skip that recipient. Log warning. |
| Job overlap | Use distributed lock to prevent concurrent runs. |

**Idempotency**

Guard: Before creating each alert, the job checks for an existing unread alert with the same `type = 'CONTRACT_EXPIRY'`, `entity_id = project.id`, and `recipient_user_id`. If found, the alert is skipped. Once a user reads or dismisses the alert, a new one can be created on the next run if the condition still holds.

**Configuration**

| SystemConfig Key | Default | Description |
|---|---|---|
| `alert.contract_expiry_days` | 30 | Days before contract end to trigger WARNING alert |
| `alert.contract_expiry_urgent_days` | 7 | Days before contract end to trigger CRITICAL alert |

**Testing**

- [ ] WARNING alert created when contract expires within 30 days but more than 7 days away
- [ ] CRITICAL alert created when contract expires within 7 days
- [ ] CRITICAL alert created when contract has already expired (end_date in past)
- [ ] Alerts sent to DM, CTO, and CEO
- [ ] No alert for FIXED_PRICE projects (only T&M and ONBOARDING)
- [ ] No alert for non-ACTIVE projects
- [ ] No alert for projects without `contract_end_date`
- [ ] De-duplication: no new alert if unread alert of same type+entity exists for recipient
- [ ] New alert created after user reads previous alert and condition still holds
- [ ] SystemConfig overrides: changing threshold values affects which projects are flagged
- [ ] Days remaining displayed correctly in alert title

---

### Job: Bench Duration Check

**Schedule**

| Attribute | Value |
|---|---|
| Cron Expression | `0 0 * * *` |
| Human Readable | Every day at 00:00 (midnight) |
| Timezone | Asia/Kolkata |

**What It Processes**

```sql
-- Resources with zero ACTIVE assignments for more than threshold days
SELECT r.*,
       COALESCE(
           (SELECT MAX(a.released_at) FROM assignment a WHERE a.resource_id = r.id AND a.status IN ('RELEASED', 'AUTO_RELEASED')),
           r.date_of_joining
       ) AS bench_start_date
FROM resource r
WHERE r.is_active = true
  AND NOT EXISTS (
      SELECT 1 FROM assignment a
      WHERE a.resource_id = r.id AND a.status = 'ACTIVE'
  )
  AND CURRENT_DATE - COALESCE(
      (SELECT MAX(a.released_at) FROM assignment a WHERE a.resource_id = r.id AND a.status IN ('RELEASED', 'AUTO_RELEASED')),
      r.date_of_joining
  ) > (SELECT CAST(value AS INTEGER) FROM system_config WHERE key = 'alert.bench_threshold_days');
```

**Processing Logic**

```pseudocode
FUNCTION check_bench_duration():
    threshold_days = SystemConfig.get('alert.bench_threshold_days')  -- default: 7

    -- Find resources on bench longer than threshold
    benched_resources = QUERY resources
                        WHERE is_active = true
                          AND has_zero_active_assignments()

    FOR EACH resource IN benched_resources:
        -- Calculate bench start date
        last_release = MAX(released_at) FROM assignments WHERE resource_id = resource.id
                                                           AND status IN ('RELEASED', 'AUTO_RELEASED')
        bench_start = last_release ?? resource.date_of_joining
        days_on_bench = TODAY - bench_start

        IF days_on_bench <= threshold_days:
            CONTINUE

        -- Determine recipients: DM (resource's reporting DM), CTO, HR
        -- DM determined by resource's last project DM or organizational DM
        recipients = DEDUPLICATE([resource.dm_id, cto_users, hr_users])

        FOR EACH recipient IN recipients:
            -- De-duplication
            existing = QUERY alert
                       WHERE type = 'BENCH_DURATION'
                         AND entity_type = 'Resource'
                         AND entity_id = resource.id
                         AND recipient_user_id = recipient.id
                         AND is_read = false
            IF existing IS NOT EMPTY:
                CONTINUE

            CREATE Alert(
                type: 'BENCH_DURATION',
                severity: 'WARNING',
                title: '{resource.name} on bench for {days_on_bench} days',
                message: 'Resource has been unallocated since {bench_start}. Consider reassignment.',
                recipient_user_id: recipient.id,
                entity_type: 'Resource',
                entity_id: resource.id
            )

    LOG "Bench duration check completed. Found {benched_resources.count} benched resources."
```

**Side Effects**

| Side Effect | Details |
|---|---|
| Alert creation | One `BENCH_DURATION` alert per recipient per benched resource. Severity: `WARNING`. |
| No entity mutations | Read-only against Resource and Assignment. Only writes to Alert. |

**Error Handling**

| Scenario | Behavior |
|---|---|
| Single resource fails | Log error with resource ID, continue processing remaining resources. |
| SystemConfig key missing | Fall back to hardcoded default: `threshold_days = 7`. Log warning. |
| Resource has no date_of_joining and no assignments | Skip resource. Log warning. |
| Job overlap | Use distributed lock. |

**Idempotency**

Guard: Before creating each alert, the job checks for an existing unread alert with the same `type = 'BENCH_DURATION'`, `entity_id = resource.id`, and `recipient_user_id`. If found, the alert is skipped.

**Configuration**

| SystemConfig Key | Default | Description |
|---|---|---|
| `alert.bench_threshold_days` | 7 | Number of days on bench before triggering alert |

**Testing**

- [ ] Alert created when resource has 0 ACTIVE assignments for > 7 days
- [ ] No alert when resource has been on bench for exactly 7 days (must exceed threshold)
- [ ] No alert when resource has at least one ACTIVE assignment
- [ ] No alert for inactive resources (`is_active = false`)
- [ ] Bench start = `MAX(released_at)` of last released assignment
- [ ] Bench start = `date_of_joining` if resource has never been assigned
- [ ] Alerts sent to DM, CTO, and HR
- [ ] De-duplication: no new alert if unread alert of same type+entity exists for recipient
- [ ] SystemConfig override: changing `alert.bench_threshold_days` adjusts which resources are flagged
- [ ] Days on bench displayed correctly in alert title and message

---

### Job: Milestone Overdue Check

**Schedule**

| Attribute | Value |
|---|---|
| Cron Expression | `0 0 * * *` |
| Human Readable | Every day at 00:00 (midnight) |
| Timezone | Asia/Kolkata |

**What It Processes**

```sql
SELECT m.*, p.pm_id, p.dm_id
FROM milestone m
JOIN project p ON m.project_id = p.id
WHERE m.planned_delivery_date < CURRENT_DATE
  AND m.status = 'PLANNED';
```

**Processing Logic**

```pseudocode
FUNCTION check_milestone_overdue():
    overdue_milestones = QUERY milestones
                         WHERE planned_delivery_date < TODAY
                           AND status = 'PLANNED'
                         JOIN project ON milestone.project_id = project.id

    FOR EACH milestone IN overdue_milestones:
        days_overdue = TODAY - milestone.planned_delivery_date
        project = milestone.project

        -- Recipients: PM and DM of the project
        recipients = DEDUPLICATE([project.pm_id, project.dm_id])

        FOR EACH recipient IN recipients:
            -- De-duplication
            existing = QUERY alert
                       WHERE type = 'MILESTONE_OVERDUE'
                         AND entity_type = 'Milestone'
                         AND entity_id = milestone.id
                         AND recipient_user_id = recipient.id
                         AND is_read = false
            IF existing IS NOT EMPTY:
                CONTINUE

            CREATE Alert(
                type: 'MILESTONE_OVERDUE',
                severity: 'WARNING',
                title: 'Milestone "{milestone.name}" overdue by {days_overdue} days',
                message: 'Project: {project.name}. Planned delivery: {milestone.planned_delivery_date}. Update milestone status or revise timeline.',
                recipient_user_id: recipient.id,
                entity_type: 'Milestone',
                entity_id: milestone.id
            )

    LOG "Milestone overdue check completed. Found {overdue_milestones.count} overdue milestones."
```

**Side Effects**

| Side Effect | Details |
|---|---|
| Alert creation | One `MILESTONE_OVERDUE` alert per recipient per overdue milestone. Severity: `WARNING`. |
| No entity mutations | Read-only against Milestone and Project. Only writes to Alert. |

**Error Handling**

| Scenario | Behavior |
|---|---|
| Single milestone fails | Log error with milestone ID, continue processing remaining milestones. |
| Project lookup fails | Skip milestone. Log error. |
| Job overlap | Use distributed lock. |

**Idempotency**

Guard: Before creating each alert, the job checks for an existing unread alert with the same `type = 'MILESTONE_OVERDUE'`, `entity_id = milestone.id`, and `recipient_user_id`. If found, the alert is skipped.

**Configuration**

No SystemConfig keys used. The condition is simply `planned_delivery_date < TODAY AND status = 'PLANNED'` — no configurable threshold.

**Testing**

- [ ] Alert created when `planned_delivery_date < TODAY` and `status = 'PLANNED'`
- [ ] No alert when `planned_delivery_date = TODAY` (not yet overdue)
- [ ] No alert when milestone status is not `PLANNED` (e.g., `DELIVERED`, `INVOICED`)
- [ ] Alerts sent to PM and DM of the project
- [ ] If PM and DM are the same user, only one alert is created
- [ ] De-duplication: no new alert if unread alert of same type+entity exists for recipient
- [ ] Days overdue displayed correctly in alert title
- [ ] Deep-link entity_type = 'Milestone' and entity_id set correctly

---

### Job: Utilization Drop Check

**Schedule**

| Attribute | Value |
|---|---|
| Cron Expression | `0 0 * * 1` |
| Human Readable | Every Monday at 00:00 (midnight) |
| Timezone | Asia/Kolkata |

**What It Processes**

```sql
-- Calculate company-wide billable utilization
-- Formula: SUM(billable allocation) / (active_resource_count * 100) * 100
-- See shared/BUSINESS-RULES.md §7.1

SELECT
    COALESCE(SUM(a.billability_pct), 0) AS total_billable_allocation,
    (SELECT COUNT(*) FROM resource r WHERE r.is_active = true) AS active_resource_count
FROM assignment a
JOIN resource r ON a.resource_id = r.id
WHERE a.status = 'ACTIVE'
  AND a.is_shadow = false
  AND r.is_active = true;
```

**Processing Logic**

```pseudocode
FUNCTION check_utilization_drop():
    threshold_pct = SystemConfig.get('alert.utilization_threshold_pct')  -- default: 70

    -- Calculate company utilization per BUSINESS-RULES.md §7.1
    total_billable = SUM(billability_pct) FROM assignments
                     WHERE status = 'ACTIVE' AND is_shadow = false
    active_count = COUNT(resources WHERE is_active = true)

    IF active_count = 0:
        LOG "No active resources. Skipping utilization check."
        RETURN

    company_utilization = (total_billable / (active_count * 100)) * 100

    IF company_utilization >= threshold_pct:
        LOG "Company utilization at {company_utilization}%, above threshold {threshold_pct}%. No alert needed."
        RETURN

    -- Recipients: CTO, CEO
    recipients = DEDUPLICATE(cto_users + ceo_users)

    FOR EACH recipient IN recipients:
        -- De-duplication
        existing = QUERY alert
                   WHERE type = 'UTILIZATION_DROP'
                     AND entity_type IS NULL
                     AND recipient_user_id = recipient.id
                     AND is_read = false
        IF existing IS NOT EMPTY:
            CONTINUE

        CREATE Alert(
            type: 'UTILIZATION_DROP',
            severity: 'WARNING',
            title: 'Company utilization at {company_utilization}% (threshold: {threshold_pct}%)',
            message: 'Billable utilization has dropped below the configured threshold. {active_count} active resources with {total_billable}% total billable allocation.',
            recipient_user_id: recipient.id,
            entity_type: NULL,
            entity_id: NULL
        )

    LOG "Utilization drop check completed. Company utilization: {company_utilization}%."
```

**Side Effects**

| Side Effect | Details |
|---|---|
| Alert creation | One `UTILIZATION_DROP` alert per recipient (CTO, CEO). Severity: `WARNING`. No entity_type/entity_id (company-wide metric). |
| No entity mutations | Read-only against Assignment and Resource. Only writes to Alert. |

**Error Handling**

| Scenario | Behavior |
|---|---|
| No active resources | Skip check, log info message. Do not create a misleading alert. |
| SystemConfig key missing | Fall back to hardcoded default: `threshold_pct = 70`. Log warning. |
| Calculation error | Log error. Do not create alert with incorrect data. |
| Job overlap | Use distributed lock. |

**Idempotency**

Guard: Before creating each alert, the job checks for an existing unread alert with `type = 'UTILIZATION_DROP'` and the same `recipient_user_id`. Since this is a company-wide metric (no specific entity), the de-duplication uses `entity_type IS NULL`. Once the user reads the alert, a new one can be created on the next Monday run if utilization is still below threshold.

**Configuration**

| SystemConfig Key | Default | Description |
|---|---|---|
| `alert.utilization_threshold_pct` | 70 | Company utilization % below which a warning is triggered |

**Testing**

- [ ] Alert created when company utilization < 70%
- [ ] No alert when company utilization >= 70%
- [ ] No alert when company utilization = exactly 70% (threshold is "below", not "at or below")
- [ ] Utilization calculated per BUSINESS-RULES.md §7.1 formula
- [ ] Shadow assignments excluded from billable calculation
- [ ] Inactive resources excluded from active_resource_count
- [ ] Alerts sent to CTO and CEO only
- [ ] De-duplication: no new alert if unread `UTILIZATION_DROP` alert exists for recipient
- [ ] entity_type and entity_id are NULL (company-wide alert, no specific entity)
- [ ] SystemConfig override: changing `alert.utilization_threshold_pct` adjusts the threshold
- [ ] Edge: zero active resources does not trigger alert or cause division by zero
- [ ] Runs only on Mondays

---

## Event-Triggered Background Jobs

### Trigger: Over-Allocation Warning

**When It Fires**

| Attribute | Value |
|---|---|
| Event | Assignment CREATE or UPDATE (save) |
| Condition | After save, the resource's total allocation across all ACTIVE assignments exceeds 100% |
| Source Module | Module 05 (Allocation Tracking) |
| Execution | Synchronous — runs as part of the assignment save transaction or immediately after |

**Processing Logic**

```pseudocode
FUNCTION on_assignment_saved(assignment):
    -- Calculate total allocation for the resource
    total_allocation = SUM(allocation_pct)
                       FROM assignments
                       WHERE resource_id = assignment.resource_id
                         AND status = 'ACTIVE'

    IF total_allocation <= 100:
        RETURN  -- No over-allocation

    resource = LOOKUP resource BY assignment.resource_id
    project  = LOOKUP project BY assignment.project_id

    -- Recipients: PM who saved the assignment, DM of the project
    saving_user = CURRENT_USER
    dm_user = LOOKUP user BY project.dm_id
    recipients = DEDUPLICATE([saving_user, dm_user])

    FOR EACH recipient IN recipients:
        -- De-duplication: check for existing unread over-allocation alert for this resource
        existing = QUERY alert
                   WHERE type = 'OVER_ALLOCATION'
                     AND entity_type = 'Resource'
                     AND entity_id = resource.id
                     AND recipient_user_id = recipient.id
                     AND is_read = false
        IF existing IS NOT EMPTY:
            CONTINUE

        CREATE Alert(
            type: 'OVER_ALLOCATION',
            severity: 'WARNING',
            title: '{resource.name} is at {total_allocation}% allocation',
            message: 'Total allocation exceeds 100% after assignment to {project.name}. Allocation: {total_allocation}%.',
            recipient_user_id: recipient.id,
            entity_type: 'Resource',
            entity_id: resource.id
        )
```

**Side Effects**

| Side Effect | Details |
|---|---|
| Alert creation | One `OVER_ALLOCATION` alert per recipient. Severity: `WARNING`. Entity: Resource (the over-allocated resource). |
| No blocking | Over-allocation is a soft warning — the assignment save is NOT prevented. |

**Error Handling**

| Scenario | Behavior |
|---|---|
| Alert creation fails | Log warning. The assignment save must still succeed — alert failure is non-blocking. |
| Resource or project lookup fails | Log error. Skip alert creation. Assignment save still succeeds. |

**Idempotency**

Guard: De-duplication check for unread alert of same `type = 'OVER_ALLOCATION'` and `entity_id = resource.id` per recipient. If the user reads/dismisses the alert and saves another over-allocating assignment, a new alert is created.

**Testing**

- [ ] Alert created when resource total allocation > 100% after assignment save
- [ ] No alert when total allocation <= 100%
- [ ] Alert shows correct total allocation percentage
- [ ] Alert sent to PM who saved and DM of the project
- [ ] If PM and DM are the same user, only one alert
- [ ] De-duplication: no new alert if unread `OVER_ALLOCATION` alert for same resource exists
- [ ] Assignment save succeeds even if alert creation fails (non-blocking)
- [ ] Fires on both CREATE and UPDATE of assignment
- [ ] Does not fire on assignment release (status change to RELEASED/AUTO_RELEASED)

---

### Trigger: Assignment Auto-Released

**When It Fires**

| Attribute | Value |
|---|---|
| Event | Module 05 auto-release job processes an assignment |
| Condition | Assignment status changed from `ACTIVE` to `AUTO_RELEASED` by the daily job |
| Source Module | Module 05 (Allocation Tracking) — auto-release job |
| Execution | Inline within the Module 05 auto-release job processing loop |

> **Note:** This alert type is defined in Module 12 (Alerts) but is triggered by Module 05's auto-release job. The alert creation logic lives in Module 05's job implementation. See `modules/05-allocation-tracking/JOBS.md` for the full processing details.

**Processing Logic**

```pseudocode
-- This runs inside Module 05's auto-release job FOR EACH loop
FUNCTION create_auto_release_alert(assignment):
    resource = LOOKUP resource BY assignment.resource_id
    project  = LOOKUP project BY assignment.project_id

    -- Recipients: PM and DM of the project
    pm_user = LOOKUP user BY project.pm_id
    dm_user = LOOKUP user BY project.dm_id
    recipients = DEDUPLICATE([pm_user, dm_user])

    FOR EACH recipient IN recipients:
        CREATE Alert(
            type: 'ASSIGNMENT_AUTO_RELEASED',
            severity: 'INFO',
            title: '{resource.name} auto-released from {project.name}',
            message: 'Assignment ended on {assignment.end_date}. Resource is now available for reallocation.',
            recipient_user_id: recipient.id,
            entity_type: 'Assignment',
            entity_id: assignment.id
        )
```

**Side Effects**

| Side Effect | Details |
|---|---|
| Alert creation | One `ASSIGNMENT_AUTO_RELEASED` alert per recipient (PM, DM). Severity: `INFO`. |

**Error Handling**

| Scenario | Behavior |
|---|---|
| Alert creation fails | Log warning. The assignment status update must still commit — alert failure is non-blocking. See Module 05 JOBS.md for full error handling. |

**Idempotency**

Guard: The auto-release job in Module 05 only processes `ACTIVE` assignments. Once processed, the assignment becomes `AUTO_RELEASED` and will not be selected again. Therefore, duplicate alerts cannot be created by re-running the job.

**Testing**

- [ ] Alert created with type `ASSIGNMENT_AUTO_RELEASED` and severity `INFO`
- [ ] Alert sent to PM and DM of the project
- [ ] If PM and DM are the same user, only one alert
- [ ] Alert entity_type = 'Assignment' and entity_id = the released assignment's ID
- [ ] Alert title and message include resource name, project name, and end date
- [ ] Alert creation failure does not block the assignment status update
