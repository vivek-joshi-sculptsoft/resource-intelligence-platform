# Monitoring & Observability

## Error Tracking — Sentry

| Setting | Value |
|---------|-------|
| Provider | Sentry (free tier — 5K errors/month) |
| Frontend | `@sentry/react` — catches unhandled exceptions, component errors |
| Backend | `sentry-sdk[fastapi]` — catches unhandled exceptions, slow transactions |
| Celery | `sentry-sdk[celery]` — captures failed job errors |
| Environment tags | `production`, `local` |
| Alert threshold | Any new error type → Sentry notification |
| PII | Scrub email/name from error reports (Sentry data scrubbing) |

---

## Application Performance

**Sentry Performance** (included in free tier, limited):
- Track p95 API response times
- Identify slow endpoints (>500ms)
- Celery job duration tracking

**Key metrics to watch:**

| Metric | Target | Alert If |
|--------|--------|----------|
| API p95 latency | < 200ms | > 500ms sustained |
| API error rate | < 1% | > 5% in 5-minute window |
| Celery job failure rate | < 1% | Any job fails 3 consecutive times |
| DB query time (p95) | < 50ms | > 200ms sustained |

At MVP scale (20 users), Sentry Performance is sufficient. Upgrade to Datadog APM or New Relic if deeper tracing is needed.

---

## Logging

### Strategy

**Structured JSON logs** to stdout → captured by Docker → forwarded to CloudWatch Logs.

```python
import structlog

logger = structlog.get_logger()

logger.info("assignment_created",
    assignment_id=str(assignment.id),
    project_id=str(project.id),
    resource_id=str(resource.id),
    allocation_pct=assignment.allocation_pct
)
```

### Log Levels

| Level | Use |
|-------|-----|
| ERROR | Unhandled exceptions, failed jobs, data integrity issues |
| WARNING | Rate limit hit, deprecated endpoint called, near-limit thresholds |
| INFO | API requests, job completions, auth events (login/logout) |
| DEBUG | SQL queries (local only), detailed business logic steps |

### Log Aggregation

**AWS CloudWatch Logs** — Docker logs from EC2 shipped via CloudWatch agent.

| Log Group | Source |
|-----------|--------|
| `/ri-platform/api` | FastAPI container stdout |
| `/ri-platform/celery` | Celery worker + beat stdout |
| `/ri-platform/nginx` | Nginx access + error logs |

Retention: 30 days (configurable). Cost: negligible at this log volume.

---

## Infrastructure Metrics — CloudWatch

| Metric | Source | Alarm Threshold |
|--------|--------|----------------|
| CPU utilization | EC2 | > 80% sustained 5 min |
| Memory utilization | EC2 (CloudWatch agent) | > 85% |
| Disk usage | EC2 | > 80% |
| DB connections | RDS | > 80% of max (90 for t4g.micro) |
| DB CPU | RDS | > 80% sustained 5 min |
| DB free storage | RDS | < 2 GB |

CloudWatch alarms trigger SNS notifications → email to admin.

---

## Uptime Monitoring

**UptimeRobot** (free tier — 50 monitors):

| Monitor | Check | Interval |
|---------|-------|----------|
| API health | `GET /api/v1/health` → 200 | 5 min |
| Frontend | `GET /` → 200 | 5 min |

Alert via email on downtime. Upgrade to Better Uptime if status page is needed.

---

## Alerting Summary

| Severity | Channel | Examples |
|----------|---------|----------|
| Critical | Email (CloudWatch SNS) | EC2 down, RDS connection exhaustion, disk full |
| Error | Sentry notification | Unhandled exception, 500 errors |
| Warning | CloudWatch dashboard | High CPU, approaching limits |
| Info | Logs only | Normal operations, audit trail |

---

## Dashboard

CloudWatch dashboard with:
- EC2 CPU + memory (4-hour view)
- RDS connections + CPU (4-hour view)
- API 5xx error count (24-hour view)
- Celery job completion count (24-hour view)

One dashboard, checked once daily at MVP. Not the primary monitoring surface — Sentry is.

---

## Tracing

**Not needed at MVP.** Single monolith, single database. Request flows are linear (API → DB → response). Add OpenTelemetry if the architecture grows to multiple services.
