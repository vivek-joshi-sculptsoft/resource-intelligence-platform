# Module 10: Bench & Availability Forecasting

## Overview

Bench forecasting provides proactive visibility into resource availability. Anyone in the company — including engineers — can see who is on bench, who is partially available, and who will be free in the next 30/60/90 days. Bench cost calculations (daily/total cost per benched resource) are Phase 2. This module owns no new entities; it reads from Assignment and Resource.

## Phase

Phase 1 (availability view without cost). Phase 2 adds bench cost calculations.

## Dependencies

- Module 01 (Auth & Roles)
- Module 04 (Resource Management)
- Module 05 (Allocation Tracking)
- Module 08 (Financial Engine) — Phase 2 bench cost requires `loaded_cost_monthly`

---

## Features

### Feature: Current Bench List
**Description:** Resources with 0% total allocation.
**Acceptance Criteria:**
- [ ] List all resources with 0 ACTIVE assignments
- [ ] Show: name, designation, expertise, days on bench, tags
- [ ] Bench start = max(released_at) of last assignment, or date_of_joining if never assigned
- [ ] Phase 2: show daily bench cost and total bench cost per resource

### Feature: Upcoming Availability View
**Description:** Resources whose assignments end within a configurable window.
**Acceptance Criteria:**
- [ ] 30/60/90 day filter options
- [ ] Show: resource name, project name, allocation %, release date, days remaining
- [ ] Auto-release-aware: only shows assignments that will auto-release (has end_date set)
- [ ] Visible to all roles

### Feature: Partial Availability
**Description:** Resources with total allocation < 100%.
**Acceptance Criteria:**
- [ ] List resources with at least one ACTIVE assignment but total < 100%
- [ ] Show: name, total allocation %, spare capacity %, current project names

### Feature: Bench Cost Aggregation (Phase 2)
**Description:** Total cost of all benched resources.
**Acceptance Criteria:**
- [ ] Total bench cost INR = SUM(daily_bench_cost × days_on_bench) for all benched resources
- [ ] Individual bench cost per resource
- [ ] Visible only to CEO, CTO, Finance

### Feature: Early Release Tracking
**Description:** When a resource is released before their planned end_date.
**Acceptance Criteria:**
- [ ] Early release flagged in AuditLog when `released_at < end_date`
- [ ] Visible in resource's assignment history

---

## Validations

No entity writes in this module. Read-only.

---

## Business Rules

- Bench definition: 0 ACTIVE assignments — `shared/BUSINESS-RULES.md §7.6`
- Bench start computation: `shared/BUSINESS-RULES.md §7.6`
- Bench cost formulas: `shared/BUSINESS-RULES.md §7.6`
- Visibility: Resource availability visible to ALL users including engineers — PRD §4.8
- Financial data (bench cost): restricted to CEO, CTO, Finance — `shared/ACCESS-MATRIX.md` (`bench_data`)
