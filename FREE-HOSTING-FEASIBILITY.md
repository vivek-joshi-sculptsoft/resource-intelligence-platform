# Free Hosting Feasibility Analysis

**Date:** 2026-06-20
**Current Architecture:** AWS (EC2 t3.small + RDS + S3/CloudFront) — ~$36/month
**Goal:** Host the entire SculptNexus platform for $0/month

---

## Current Stack Components

| Component | Current | Role |
|-----------|---------|------|
| Frontend | S3 + CloudFront | React SPA static hosting |
| Backend | EC2 (uvicorn) | FastAPI API server |
| Database | RDS PostgreSQL 16 | Primary data store (currently 364KB in dev) |
| Redis | EC2 (Docker) | Celery broker only — not used for API caching |
| Celery Worker | EC2 (Docker) | 2 scheduled jobs: auto-release (daily), recurring costs (monthly) |
| Celery Beat | Planned | Scheduler — not yet deployed |

---

## Proposed Free Architecture

```
                    ┌─────────────────┐
                    │   Vercel (Free)  │
                    │   React SPA      │
                    │   CDN + SSL      │
                    └────────┬────────┘
                             │ API calls
                             ▼
                    ┌─────────────────┐       ┌──────────────────┐
                    │  Render (Free)   │──────▶│ Supabase (Free)  │
                    │  FastAPI + Jobs  │       │ PostgreSQL 16    │
                    │  APScheduler     │       │ 500MB storage    │
                    └────────┬────────┘       └──────────────────┘
                             │
                    ┌────────▼────────┐
                    │ UptimeRobot     │
                    │ (Free keepalive)│
                    └─────────────────┘
```

---

## Component-by-Component Analysis

### 1. Frontend — Vercel Free Tier ✅ PERFECT FIT

| Metric | Free Tier Limit | Our Usage |
|--------|-----------------|-----------|
| Bandwidth | 100 GB/month | ~1-2 GB (30 users, internal tool) |
| Build minutes | 6,000/month | ~50/month (few deploys) |
| Deployments | Unlimited | Fine |
| Custom domains | Yes | Fine |
| SSL | Automatic | Fine |
| Preview deploys | Yes (per PR) | Bonus feature |

**Verdict:** React SPA on Vercel is the gold standard for free frontend hosting. No issues whatsoever.

**Migration effort:** Minimal — add `vercel.json`, configure build command, set env vars for API URL.

```json
{
  "buildCommand": "cd frontend && npm run build",
  "outputDirectory": "frontend/dist",
  "rewrites": [{ "source": "/(.*)", "destination": "/index.html" }]
}
```

---

### 2. Backend — Two Options Evaluated

#### Option A: Render Free Tier ⚠️ VIABLE WITH WORKAROUND

| Metric | Free Tier Limit | Our Usage |
|--------|-----------------|-----------|
| RAM | 512 MB | FastAPI + APScheduler fits easily |
| CPU | 0.1 vCPU (shared) | Sufficient for 30 users |
| Bandwidth | 100 GB/month | ~5-10 GB |
| Sleep after inactivity | 15 minutes | **Problem — see below** |
| Build minutes | 500/month | ~30/month |
| Persistent disk | None | Not needed (DB is external) |

**The sleep problem:** Render free instances spin down after 15 minutes of no inbound requests. Cold start takes 30-50 seconds for a Python app.

**Workaround — UptimeRobot keepalive:**
- [UptimeRobot](https://uptimerobot.com) (free: 50 monitors, 5-minute intervals) pings a `/health` endpoint every 5 minutes
- Keeps the instance warm 24/7
- Widely used — hundreds of production apps do this
- **Risk:** Render's ToS technically discourages this, but it's not enforced for small apps. If they crack down, the fallback is their $7/month Starter tier.

**Migration effort:** Medium — add `render.yaml`, Dockerfile already exists, point `DATABASE_URL` to Supabase.

#### Option B: Vercel Serverless Functions ❌ NOT RECOMMENDED

| Issue | Impact |
|-------|--------|
| 10-second execution timeout (free tier) | Complex queries or batch operations will fail |
| Cold starts (1-5 seconds) | Violates your "no cold start" requirement |
| No persistent process | Cannot run APScheduler or any in-process background jobs |
| Stateless functions | No WebSocket, no in-memory state between requests |
| Python runtime is Beta | Less mature than Node.js support |

Vercel serverless *can* run FastAPI, but it's fundamentally wrong for this use case: an internal CRUD app with background jobs, 30 concurrent users, and a need for fast responses.

#### Verdict: Render Free + UptimeRobot

---

### 3. Database — Supabase Free Tier ✅ STRONG FIT

| Metric | Free Tier Limit | Our Usage |
|--------|-----------------|-----------|
| Database storage | 500 MB | Current: 364 KB. Even at full production with 30 users, unlikely to exceed 50 MB in year 1 |
| Monthly active users | 50,000 | 30 |
| API requests | Unlimited | Fine |
| Bandwidth | 5 GB/month | ~1-2 GB |
| Realtime connections | 200 concurrent | Not needed |
| Edge functions | 500K invocations | Not needed |
| Auth | 50K MAU | Not using Supabase Auth (we have our own JWT) |
| Projects | 2 active | Need only 1 |
| Backups | None (free tier) | **Risk — see mitigations** |

**Connection approach:** Direct PostgreSQL connection via Supavisor pooler (port 6543) — works with SQLAlchemy async.

```
DATABASE_URL=postgresql+asyncpg://postgres.[project-ref]:[password]@aws-0-ap-south-1.pooler.supabase.com:6543/postgres
```

**Pause policy:** Free projects pause after 7 days of inactivity. With 30 daily users, this will never trigger. If it does somehow (holidays), any request auto-wakes it in ~5 seconds.

**No backups on free tier — mitigations:**
1. Schedule a weekly `pg_dump` via GitHub Actions → store in repo as artifact (free for private repos, 500MB limit)
2. Or use Supabase CLI: `supabase db dump` on a cron
3. Data volume is tiny (~50MB max in year 1), so even manual backups are feasible

**Migration effort:** Low — change `DATABASE_URL` env var. SQLAlchemy models already work on PostgreSQL. Run Alembic migrations against Supabase.

**Important change (post May 30, 2026):** New Supabase projects require explicit Postgres grants for PostgREST. Since we use direct SQL via SQLAlchemy (not PostgREST), this doesn't affect us.

---

### 4. Background Jobs — APScheduler as the default, Celery kept as an opt-in ✅ CLEAN SOLUTION

> **Implemented 2026-06-20.** The scheduler backend is now configurable via `SCHEDULER_BACKEND` (`apscheduler` default, `celery` optional). `app/jobs/celery_app.py` was left untouched — see [ADR-007 update](techstack/decisions/007-background-jobs.md). The free-tier deployment below runs with `SCHEDULER_BACKEND=apscheduler`, which eliminates the Redis dependency entirely for that environment.

**Current state:** 2 Celery tasks, both purely scheduled (no event-driven / async task queue usage):

| Job | Schedule | Complexity |
|-----|----------|------------|
| `auto_release_assignments` | Daily midnight IST | Simple DB query + update |
| `process_recurring_costs` | Monthly 1st | Simple DB query + insert |

**Why APScheduler works here:**
- Both jobs are cron-scheduled, not queued from API requests
- Both complete in <1 second (simple DB operations on small dataset)
- No need for distributed workers (single instance)
- No need for task retry queues (DB transactions handle consistency)
- APScheduler runs in-process with FastAPI — zero additional infrastructure

**APScheduler replacement code:**

```python
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

scheduler = AsyncIOScheduler(timezone="Asia/Kolkata")

@app.on_event("startup")
async def start_scheduler():
    scheduler.add_job(
        auto_release_assignments,
        CronTrigger(hour=0, minute=0),
        id="auto-release",
    )
    scheduler.add_job(
        process_recurring_costs,
        CronTrigger(hour=0, minute=0, day_of_month=1),
        id="recurring-costs",
    )
    scheduler.start()
```

**Future jobs (Phase 2-3):** The 4 remaining planned jobs (contract expiry alert, bench duration alert, milestone overdue alert, utilization alert) are all the same pattern — scheduled DB reads → conditional notifications. APScheduler handles all of them.

**What we lose:**
- Task result backend (Celery stores results in Redis) — not currently used by any API
- Distributed scaling (multiple workers) — unnecessary at 30 users
- Task retry with exponential backoff — can add manually if needed, but these jobs are idempotent

**Verdict:** Celery is overengineered for this workload. APScheduler is the right tool.

---

### 5. Redis — ELIMINATE ✅

**Current usage:** Celery broker only. Not used for:
- API response caching
- Session storage (JWT is stateless)
- Rate limiting
- Pub/sub

**With Celery removed, Redis has zero purpose.** Eliminating it removes an entire infrastructure dependency.

**If caching is needed later:** Upstash Redis free tier (256MB, 500K commands/month) can be added in minutes with zero code changes — just set `REDIS_URL` to an Upstash endpoint.

---

## Migration Complexity Assessment

| Task | Effort | Risk |
|------|--------|------|
| Deploy frontend to Vercel | 1-2 hours | Low — standard SPA deploy |
| Create Supabase project + migrate schema | 2-3 hours | Low — Alembic handles it |
| Replace Celery with APScheduler | 3-4 hours | Low — only 2 simple jobs |
| Remove Redis dependency from config | 30 min | None |
| Deploy backend to Render | 2-3 hours | Low — Dockerfile exists |
| Set up UptimeRobot keepalive | 15 min | None |
| Update CORS + env vars | 30 min | Low |
| Set up backup cron (GitHub Actions) | 1 hour | Low |
| E2E testing on new infra | 2-3 hours | Medium — integration testing |
| **Total** | **~1.5-2 days** | **Low overall** |

---

## Risk Matrix

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| Render enforces anti-keepalive policy | Low | High — 30-50s cold starts | Upgrade to Render Starter ($7/mo) or move to Koyeb |
| Supabase free project pauses | Very Low (30 daily users) | Medium — 5s wake-up | Self-heals on next request; UptimeRobot monitors it |
| Supabase 500MB limit hit | Very Low (years away) | Medium | Upgrade to Pro ($25/mo) or archive old audit logs |
| Render 512MB RAM insufficient | Low | Medium — OOM crashes | Optimize queries; upgrade to Starter ($7/mo) |
| APScheduler misses a job run (app restart during cron window) | Low | Low — jobs are idempotent | Add missed-job detection on startup |
| No DB backups, data loss | Low | High | GitHub Actions weekly pg_dump (see above) |
| Vercel bandwidth exceeded | Very Low | Low — billing starts | Monitor usage; 100GB is enormous for 30 users |

---

## Cost Comparison

| Component | Current (AWS) | Proposed (Free) | Fallback (Minimal Paid) |
|-----------|--------------|-----------------|------------------------|
| Frontend hosting | ~$3 (S3+CF) | $0 (Vercel) | $0 |
| Backend server | ~$15 (EC2) | $0 (Render free) | $7 (Render Starter) |
| Database | ~$13 (RDS) | $0 (Supabase free) | $25 (Supabase Pro) |
| Redis | ~$0 (on EC2) | $0 (eliminated) | $0 (Upstash free) |
| Monitoring | ~$5 (Sentry) | $0 (Sentry free tier: 5K errors/mo) | $0 |
| **Total** | **~$36/month** | **$0/month** | **$7-32/month** |

---

## What Changes in Code

### Already Done
1. **`backend/app/config.py`** — Added `SCHEDULER_BACKEND` (default `apscheduler`). `CELERY_BROKER_URL`/`CELERY_RESULT_BACKEND` kept for the opt-in Celery path.
2. **`backend/app/jobs/scheduler.py`** — New APScheduler implementation. `celery_app.py` untouched.
3. **`backend/app/main.py`** — Scheduler startup/shutdown wired into the FastAPI lifespan, conditional on `SCHEDULER_BACKEND`.
4. **`docker-compose.dev.yml`** — `redis` and `celery-worker` moved behind a `celery` Compose profile — not started by default.
5. **`backend/pyproject.toml`** — Added `apscheduler`. `celery`/`redis` deps kept for the opt-in path.

### Still To Do For Free Hosting
6. **Render deployment** — set `SCHEDULER_BACKEND=apscheduler` (the default) in Render's env vars — no Redis service needed there.
7. **`frontend/`** — Update API base URL to point to the Render backend.

### No Change Needed
- All SQLAlchemy models (already PostgreSQL-compatible)
- All API endpoints
- All business logic
- All tests (run against SQLite locally, PostgreSQL in CI/prod)
- Auth (JWT is stateless, works anywhere)
- Alembic migrations (already PostgreSQL-compatible)

---

## Deployment Architecture

### Production (Free Tier)

```
GitHub (private repo)
  │
  ├──▶ Vercel (auto-deploy on push)
  │     └── Frontend SPA (React + Vite)
  │         └── https://sculptnexus.vercel.app
  │
  ├──▶ Render (auto-deploy on push)
  │     └── Backend API (FastAPI + APScheduler)
  │         └── https://sculptnexus-api.onrender.com
  │
  └──▶ GitHub Actions
        └── Weekly DB backup (pg_dump → artifact)

Supabase (ap-south-1 Mumbai region)
  └── PostgreSQL 16
      └── Direct connection via Supavisor pooler

UptimeRobot (external)
  └── Pings /api/v1/health every 5 minutes
```

### Local Dev (no change)

```
SQLite (default) — no Docker needed
uvicorn --reload + Vite dev server
```

---

## Supabase Setup Notes

1. **Create project** in `ap-south-1` (Mumbai) — matches current AWS region, lowest latency for India-based team
2. **Use connection pooler** (port 6543, transaction mode) — required for serverless-style connections; Render free tier may recycle connections
3. **Do NOT use Supabase Auth, Storage, or Edge Functions** — we only need the raw PostgreSQL database
4. **Run Alembic migrations** against Supabase to create all tables:
   ```bash
   DATABASE_URL="postgresql+asyncpg://..." alembic upgrade head
   ```
5. **Run seed script** to populate roles, permissions, system config, and admin user

---

## Alternatives Considered and Rejected

| Platform | Why Rejected |
|----------|-------------|
| **Vercel (backend)** | 10s timeout, cold starts, no persistent process for scheduled jobs |
| **Fly.io** | No longer offers a free tier (removed in 2025) |
| **Railway** | Not truly free — $5 one-time credit + $1/month ongoing credit |
| **Koyeb** | Scale-to-zero on free tier causes cold starts |
| **Google Cloud Run** | Always-on min-instances cost money; free tier has cold starts |
| **AWS Lambda** | Cold starts, 15-minute timeout, complex FastAPI adapter needed |
| **Neon (DB)** | Good alternative to Supabase, but Supabase has broader free limits and Mumbai region |
| **PlanetScale (DB)** | MySQL-based — would require rewriting all SQLAlchemy models |

---

## Recommendation

**Go with: Vercel (FE) + Render (BE) + Supabase (DB) + APScheduler (jobs)**

This is the most practical free architecture for a 30-user internal tool. The only real risk is Render's keepalive policy, and even if that fails, the $7/month Starter tier is the cheapest possible fallback — still saving $29/month vs current AWS setup.

### Immediate Next Steps
1. Create Supabase project (Mumbai region)
2. Replace Celery with APScheduler (3-4 hours of code changes)
3. Deploy backend to Render with Supabase connection
4. Deploy frontend to Vercel
5. Set up UptimeRobot monitor
6. Set up GitHub Actions backup cron
7. Verify E2E on new infra
8. Decommission AWS resources

---

*Sources: Vercel, Supabase, Render, and Upstash pricing pages (June 2026)*
