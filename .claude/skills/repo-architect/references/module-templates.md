# Module File Templates

Every module folder contains up to 6 files. JOBS.md is only created for modules that own background/scheduled jobs. Use these templates exactly — consistency across modules is critical for Claude Code to process them reliably.

---

## REQUIREMENTS.md

```markdown
# {Module Name}

## Overview
{1-2 sentences: what this module does and who uses it.}

## Phase
{1, 2, or 3}

## Dependencies
{List of module folders that must be built before this one, with what's needed from each.}
- `01-auth-and-roles` — User authentication, role checking middleware
- `04-resource-management` — Resource entity for FK references

## User Roles
{Which roles interact with this module and how.}
| Role | Access |
|---|---|
| PM | Can create/edit assignments for own projects |
| DM | Can view all assignments in their portfolio |

## Features

### Feature: {Feature Name}
**Description:** {What it does in 1-2 sentences}
**User:** {Which role uses this}
**Acceptance Criteria:**
- [ ] {Specific, testable criterion}
- [ ] {Another criterion}
- [ ] {Include happy path AND edge cases}

### Feature: {Next Feature}
...

## Validations
{All validation rules from FSD that apply to this module.}

| Rule | Condition | Error Message | Type |
|---|---|---|---|
| {Name} | {Exact condition} | "{Exact error message}" | Hard block / Warning |

## Business Rules
{Reference specific formulas from shared/BUSINESS-RULES.md}
- Utilization calculation: see shared/BUSINESS-RULES.md §7.1
- Cost calculation: see shared/BUSINESS-RULES.md §7.2

## State Machines
{If this module has entities with lifecycles, include the state flow and transition table.}

```
[STATE_A] → [STATE_B] → [STATE_C]
```

| From | To | Trigger | Who | Side Effects |
|---|---|---|---|---|
```

---

## SCHEMA.md

```markdown
# {Module Name} — Schema

## Entities Owned by This Module

### {Entity Name}
{One sentence description.}

| Field | Type | Constraints | Notes |
|---|---|---|---|
| id* | UUID | PK | |
| {field}* | {type} | {constraints} | {notes} |

**Phase notes:**
- Phase 1: All fields except {field_x}
- Phase 2: Add {field_x}

**Indexes:**
- {index description}

**Unique constraints:**
- {constraint description}

### {Another Entity}
...

## Entities Referenced (not owned)

These entities are owned by other modules. This module reads them via FK.

### {Entity Name} (owned by module {NN-name})
Fields used by this module:
| Field | Type | Used For |
|---|---|---|
| id | UUID | FK reference |
| name | STRING(255) | Display in UI |
| {field} | {type} | {how this module uses it} |

Full definition: see shared/ENTITIES.md
```

---

## API.md

```markdown
# {Module Name} — API Endpoints

Base path: `/api/{resource}`

## Endpoints

### GET /api/{resource}
**Description:** List all {resources} with pagination and filters
**Auth:** {Roles that can access}
**Scope:** {ALL / OWN_PORTFOLIO / SELF_ONLY} — see shared/ACCESS-MATRIX.md
**Query Parameters:**
| Param | Type | Default | Description |
|---|---|---|---|
| page | integer | 1 | Page number |
| limit | integer | 20 | Items per page |
| status | string | — | Filter by status |
| {filter} | {type} | — | {description} |
**Response:**
```json
{
  "data": [...],
  "pagination": { "page": 1, "limit": 20, "total": 100 }
}
```
**Field restrictions:** {fields that return null for certain roles}

### GET /api/{resource}/:id
**Description:** Get single {resource} by ID
**Auth:** {Roles}
**Scope:** {scope rule}
**Response:** Full entity object
**Field restrictions:** {list}

### POST /api/{resource}
**Description:** Create new {resource}
**Auth:** {Roles}
**Request Body:**
| Field | Type | Required | Notes |
|---|---|---|---|
| {field} | {type} | Yes/No | {notes} |
**Validations:** {list from FSD §11}
**Side Effects:**
- {Audit log entry}
- {Alert trigger if applicable}
**Response:** Created entity with id

### PUT /api/{resource}/:id
**Description:** Update {resource}
**Auth:** {Roles}
**Request Body:** Same as POST (partial update allowed)
**Validations:** {list}
**Side Effects:**
- {Audit log: one entry per changed field}
**Response:** Updated entity

### DELETE /api/{resource}/:id
**Description:** Soft delete (set is_active = false)
**Auth:** {Roles — usually admin only}
**Validations:** {e.g., "Cannot deactivate client with active projects"}
**Side Effects:**
- {Cascading effects}
- {Audit log}
**Response:** 204 No Content

### POST /api/{resource}/:id/{action}
**Description:** {Special action, e.g., "release assignment", "transition milestone status"}
**Auth:** {Roles}
**Request Body:** {if needed}
**Validations:** {state machine rules}
**Side Effects:** {state change effects}
```

---

## SCREENS.md

```markdown
# {Module Name} — Screen Specifications

## Screen: {Screen Name}
**Route:** `/{path}`
**Audience:** {Roles that see this screen}
**Purpose:** {One sentence}

### Layout
{Describe the page layout: header, sidebar, main content area, tabs if any}

### Components

#### {Component Name}
**Type:** Table / Form / Card / Widget / Chart
**Data source:** `GET /api/{endpoint}`
**Fields displayed:**
| Field | Label | Format | Notes |
|---|---|---|---|
| name | Name | Text | Linked to detail view |
| allocation_pct | Allocation | {N}% | Color-coded if >100% |

**Actions:**
| Action | Label | Trigger | Confirmation |
|---|---|---|---|
| Create | + Add {Entity} | Opens create form | None |
| Edit | Edit icon | Opens edit form | None |
| Delete | Delete icon | Soft delete | "Are you sure?" dialog |

**Sorting:** Default by {field} {asc/desc}. Sortable columns: {list}.
**Filtering:** {filter controls}
**Pagination:** 20 items per page, standard pagination controls.

**Empty State:**
"{Helpful message when no data exists yet. e.g., 'No resources assigned to this project. Click + Add to assign a resource.'}"

**Access Restrictions:**
- Engineers: {what's hidden}
- PM: {what's hidden}
- See shared/ACCESS-MATRIX.md for full rules

#### {Next Component}
...

## Screen: {Next Screen}
...
```

---

## DEPENDENCIES.md

```markdown
# {Module Name} — Dependencies

## Must Be Built Before This Module

| Module | What's Needed | Why |
|---|---|---|
| `01-auth-and-roles` | User model, auth middleware, role checking | Every API endpoint needs authentication |
| `04-resource-management` | Resource entity | Assignments reference resources via FK |
| `03-project-management` | Project entity | Assignments belong to projects |

## Modules That Depend on This Module

| Module | What They Need |
|---|---|
| `07-utilization-dashboards` | Reads assignment data for utilization calculations |
| `08-financial-engine` | Adds billing_rate to assignments in Phase 2 |

## Shared References Used
- `shared/ENTITIES.md` — Entity field definitions
- `shared/BUSINESS-RULES.md` — {specific formulas used}
- `shared/ACCESS-MATRIX.md` — Access rules for {entity}
```

---


## JOBS.md (for modules with any background processing)

Create this file for any module that has scheduled jobs, event-triggered async processing, or user-initiated bulk operations. If a module has none of these, skip this file.

```markdown
# {Module Name} — Background Jobs & Async Processing

## Overview
{1-2 sentences: what background processing this module needs and why.}

## Job Summary

| Job | Type | Schedule / Trigger | Entities | Side Effects | Phase |
|---|---|---|---|---|---|
| {Name} | Scheduled | Daily midnight | {entity} | Alerts, audit | {1/2/3} |
| {Name} | Event-triggered | On {event} | {entity} | State cascade | {1/2/3} |
| {Name} | Bulk | User-initiated | {entity} | Export file | {1/2/3} |

---

## Scheduled Jobs

Jobs that run on a cron schedule, independent of user actions.

### Job: {Job Name}

**Schedule**

| Attribute | Value |
|---|---|
| Cron Expression | `0 0 * * *` |
| Human Readable | Daily at midnight IST |
| Timezone | Asia/Kolkata |
| Estimated Duration | < 30 seconds for typical load |

**What It Processes**

```sql
SELECT * FROM {entity}
WHERE status = 'ACTIVE'
  AND {condition} <= CURRENT_DATE
```

Expected volume: {N} records per run (typical), {N} max.

**Processing Logic**

```
FOR EACH record matching query:
  1. Validate pre-conditions
  2. Update state: {entity}.status = '{new_status}'
  3. Set metadata: {entity}.{field} = {value}
  4. Create side effects:
     a. Alert -> type: {TYPE}, recipients: [{roles}]
     b. AuditLog -> entity_type, action: UPDATE
  5. Update related entities if needed
```

**Side Effects**

| Side Effect | Details |
|---|---|
| State change | {entity}.status -> {new_status} |
| Alert created | Type: {ALERT_TYPE}, Recipients: {roles} |
| Audit logged | entity_type: {type}, action: UPDATE |
| Related entities | {cascading changes} |

**Error Handling**

| Scenario | Behavior |
|---|---|
| Single record fails | Log error with record ID, skip to next. Do NOT abort batch. |
| All records fail | Log critical. Alert system admin. |
| Job crashes mid-run | Partial completion is safe. Re-run picks up remaining. |
| Database timeout | Retry after 5 min. Max 3 retries. |

**Idempotency**

Guard: Only processes records where {condition changes after processing}.
Example: Auto-release processes status = 'ACTIVE'. After processing, status = 'AUTO_RELEASED', so re-run skips it.

**Concurrency & Race Conditions**

| Scenario | Behavior |
|---|---|
| Two instances overlap | Use row lock (SELECT FOR UPDATE SKIP LOCKED) or distributed lock |
| User modifies record during job | Job re-reads before processing. Skips if condition no longer matches. |
| User modifies after job processes | User change takes precedence. Both changes in audit log. |

**Configuration**

| SystemConfig Key | Default | Controls |
|---|---|---|
| {config_key} | {default} | {what it does} |

**Monitoring**

| Event | Level | Message |
|---|---|---|
| Started | INFO | "{job} started. Querying records..." |
| Record processed | DEBUG | "{job} processed {entity} {id}" |
| Record skipped | DEBUG | "{job} skipped {entity} {id}: condition no longer met" |
| Record failed | ERROR | "{job} failed for {entity} {id}: {error}" |
| Completed | INFO | "{job} done. Processed: {N}, Skipped: {N}, Failed: {N}" |
| Aborted | CRITICAL | "{job} aborted: {error}" |

**Testing**

- [ ] Processes matching records correctly
- [ ] Skips non-matching records
- [ ] Zero matching records = no error, logs "0 processed"
- [ ] Idempotent: re-run same result
- [ ] Single failure does not abort batch
- [ ] Side effects fire (alerts, audit, cascades)
- [ ] Race condition: user change before processing -> job skips
- [ ] Race condition: user change after processing -> both preserved
- [ ] Config values from SystemConfig, not hardcoded
- [ ] Performance OK at max volume

---

## Event-Triggered Background Jobs

Async operations that fire in response to a user action or system event. The triggering request returns immediately. Background work happens asynchronously.

### Trigger: {Event Name}

**When It Fires**

| Attribute | Value |
|---|---|
| Source Event | {user action or system event that triggers this} |
| Source Entity | {which entity change fires it} |
| Condition | {specific condition, e.g., "project.status changed to CANCELLED"} |
| Timing | Async: fires after the triggering transaction commits |

**Why Async**

{Why this cannot be synchronous:}
- {e.g., "Releasing 20 assignments would make the cancel API too slow"}
- {e.g., "Alert creation for multiple recipients should not block user's save"}
- {e.g., "Margin recalculation queries multiple tables, too heavy for inline"}

**Processing Logic**

```
ON {event_name}:
  Input: {entity_id}, {changed_fields}, {user_id}

  1. Load related data
  2. Process changes
  3. Create side effects (alerts, audit, status cascades)
  4. Update related entities
```

**Side Effects**

| Effect | Details |
|---|---|
| {Effect 1} | {what happens} |
| {Effect 2} | {what happens} |

**Error Handling**

| Scenario | Behavior |
|---|---|
| Background job fails | Triggering action is NOT rolled back. Queue for retry. |
| Retry exhausted (3x) | Alert system admin. Log to failed_jobs with full context. |
| Duplicate event | Must be idempotent. Check if work already done before processing. |

**Retry Strategy**

| Attribute | Value |
|---|---|
| Max Retries | 3 |
| Backoff | Exponential: 10s, 30s, 90s |
| Dead Letter | After max retries, log to failed_jobs table |

**Implementation Options**

Choose based on tech stack:
- **In-process (simple):** Fire after response sent. No persistence. Lost on crash. OK for non-critical.
- **Queue (recommended):** Push to BullMQ / Celery / SQS. Worker processes. Survives crashes. Retry built in.
- **DB-backed (middle ground):** Insert into pending_jobs table. Worker polls. Simple, reliable.

**Testing**

- [ ] Event fires the background job
- [ ] API returns immediately (does not wait)
- [ ] Background processes correctly
- [ ] Duplicate event handled idempotently
- [ ] Failure does not roll back trigger
- [ ] Retry works on transient failures
- [ ] Dead letter captures permanent failures

### Common Event Triggers Checklist

{Check which apply to this module:}

| Event | Background Work |
|---|---|
| Entity created | Initialize related data, send notification |
| Status changed | Cascade to related entities, fire alerts, recalculate aggregates |
| Entity deactivated | Release references, clean up, notify stakeholders |
| Bulk change | Recalculate aggregates across affected entities |
| Financial event (invoice/cost) | Recalculate margins, update dashboards |
| Threshold crossed | Fire alert (utilization drop, bench duration) |
| Assignment released | Update availability, check bench threshold, notify |

---

## Bulk / Long-Running Operations

User-initiated operations too slow for synchronous response. API accepts the request, returns a job ID. User polls for completion or gets notified.

### Operation: {Operation Name}

**Trigger**

| Attribute | Value |
|---|---|
| Initiated By | {role} |
| API Endpoint | POST /api/{resource}/bulk-{action} |
| Estimated Duration | {range, e.g., "2-30 seconds"} |
| Max Data Volume | {e.g., "12 months × 50 projects"} |

**Why Async**

{e.g., "Exporting all invoice data involves joins, currency conversion, and CSV generation."}

**API Flow**

```
1. Client:  POST /api/{resource}/bulk-{action}
            Body: { filters, options }

2. Server:  Validate input
            Create job: { id, status: PENDING, params }
            Enqueue background processing
            Return: { job_id, status: "PENDING" }

3. Worker:  Process the operation
            Update job: { status: PROCESSING, progress_pct: N }
            On complete: { status: COMPLETED, result_url }
            On fail: { status: FAILED, error }

4. Client:  GET /api/jobs/{job_id}   (poll every 2-5s)
            Returns: { status, progress_pct, result_url, error }
```

**Job Record Schema**

| Field | Type | Notes |
|---|---|---|
| id | UUID | PK |
| type | STRING | Operation name |
| status | ENUM | PENDING, PROCESSING, COMPLETED, FAILED |
| params | JSON | Input parameters |
| progress_pct | INTEGER | 0-100 |
| total_items | INTEGER | Total to process |
| processed_items | INTEGER | Done so far |
| result_url | STRING | Download link (for exports) |
| error | TEXT | Error message if FAILED |
| created_by | FK -> User | Who initiated |
| created_at | TIMESTAMP | When started |
| completed_at | TIMESTAMP | When finished |

**Testing**

- [ ] API returns immediately with job_id
- [ ] Polling returns accurate status and progress
- [ ] Completed jobs have result (file URL or summary)
- [ ] Failed jobs have clear error
- [ ] Concurrent bulk ops don't interfere
- [ ] Cleanup: old completed jobs cleaned after N days
```
