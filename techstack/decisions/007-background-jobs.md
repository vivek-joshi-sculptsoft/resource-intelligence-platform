# ADR-007: Background Jobs

**Status:** Accepted
**Date:** 2026-06-09
**Deciders:** Engineering Team

---

## Context

The platform requires 6 scheduled background jobs: daily auto-release of expired assignments, daily/weekly alert checks (contract expiry, bench duration, milestone overdue, utilization), and monthly recurring cost processing. Job volume is low (~10 jobs/day) but reliability matters — a missed auto-release leaves stale allocations in the system.

## Decision

> We will use **Celery 5.4 with Redis as broker and celery-beat for scheduling**.

## Rationale

- Python-native — runs in the same codebase, shares SQLAlchemy models and business logic
- Celery is battle-tested for scheduled + event-driven jobs with retry/dead-letter support
- Redis is already present as the application cache — doubles as the Celery broker at zero additional cost
- celery-beat provides cron-like scheduling without external dependencies (no AWS EventBridge or CloudWatch Events)
- Built-in retry with exponential backoff handles transient failures

## Alternatives Considered

| Alternative | Why Rejected |
|-------------|-------------|
| APScheduler (in-process) | Simpler but runs inside the API process — a crash loses the scheduler. No retry support. No separate worker for CPU-intensive jobs. |
| AWS SQS + Lambda | Serverless but adds cold start latency and splits the codebase (Lambda functions can't share SQLAlchemy models easily). Per-invocation pricing is more expensive than a Celery worker for scheduled jobs. |
| Temporal | Powerful for complex workflows but massive overhead for 6 simple cron jobs. Learning curve doesn't fit the timeline. |

## Consequences

**Positive:**
- One codebase for API and workers — `from app.modules.allocations.service import release_assignment` works identically in both
- Celery Flower provides a web dashboard for monitoring job status (optional, add when needed)
- Retry policy prevents silent failures

**Negative / Trade-offs:**
- Celery worker is a separate process — must be deployed and monitored alongside the API. Docker Compose handles this.
- Redis as broker has no message persistence across restarts. At 10 jobs/day, this is a non-issue — jobs re-run on next schedule.

**Neutral:**
- Can add event-driven tasks (e.g., "send alert on assignment create") without changing the job infrastructure.

## Review Trigger

Revisit if job volume exceeds 10K/day or if complex multi-step workflows are needed (consider Temporal at that point).
