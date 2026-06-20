# Deployment Plan — Render (Backend) + Vercel (Frontend) for Testing

**Purpose:** Stand up a free, publicly-reachable test deployment of SculptNexus. Not a production cutover — current AWS setup stays untouched. This is the execution checklist for `FREE-HOSTING-FEASIBILITY.md`, scoped to backend + frontend only (DB is Supabase, covered briefly in Phase 1).

**How to use this file:** Run phases in order in a fresh Claude Code session. Each phase has a goal, exact steps, and a verification check before moving on. Steps marked **[MANUAL]** require a human in a browser (account creation, dashboard clicks, copying secrets) — Claude Code cannot do these. Steps marked **[CLAUDE]** can be executed directly (file edits, git commands, curl checks).

**Architecture decision baked into this plan:** the frontend will proxy `/api/*` to the Render backend via a Vercel rewrite, so the browser sees everything as same-origin. This matters because `backend/app/modules/auth/router.py:35` sets auth cookies with `samesite="strict"` — a direct cross-origin call from `*.vercel.app` to `*.onrender.com` would silently drop the cookie and break login. **Do not skip the rewrite step and call the Render URL directly from the frontend** unless you also change `samesite` to `"none"` (see Phase 4 fallback note).

---

## Phase 0 — Prerequisites

**[MANUAL]**
1. Create a free [Render](https://render.com) account, connect your GitHub account, grant access to this repo (private repo — Render needs explicit repo access, not just org access).
2. Create a free [Vercel](https://vercel.com) account, connect the same GitHub account/repo.
3. Create a free [Supabase](https://supabase.com) account, new project in region `ap-south-1` (Mumbai/Singapore — pick whichever Supabase offers closest to your users). Note the project's database password at creation time — it's only shown once.

**Verify:** You can see the empty repo listed as importable in both Render's and Vercel's dashboards.

---

## Phase 1 — Database (Supabase)

**[MANUAL]**
1. In the Supabase project dashboard, go to **Project Settings → Database**.
2. Copy the **connection string** under "Connection pooling" (Transaction mode, port `6543`) — NOT the direct connection (port 5432). Render's free tier and serverless-style connections need the pooler.
3. It looks like:
   ```
   postgresql://postgres.<project-ref>:<password>@aws-0-<region>.pooler.supabase.com:6543/postgres
   ```
4. Convert it to the SQLAlchemy async driver format (swap `postgresql://` → `postgresql+asyncpg://`):
   ```
   postgresql+asyncpg://postgres.<project-ref>:<password>@aws-0-<region>.pooler.supabase.com:6543/postgres
   ```
   Save this as `SUPABASE_DATABASE_URL` somewhere safe (password manager / local `.env.supabase`, not committed to git).

**[CLAUDE]** — run migrations and seed data against Supabase from your local machine:

```bash
cd backend
export DATABASE_URL="postgresql+asyncpg://postgres.<project-ref>:<password>@aws-0-<region>.pooler.supabase.com:6543/postgres"
python3 -m alembic upgrade head
```

Then seed roles, permissions, system config, and the admin user (there's no standalone CLI seed command — `seed_all` only auto-runs for SQLite in `app/main.py`'s lifespan — so invoke it directly):

```bash
DATABASE_URL="postgresql+asyncpg://postgres.<project-ref>:<password>@aws-0-<region>.pooler.supabase.com:6543/postgres" python3 -c "
import asyncio
from app.database import async_session_factory
from app.modules.auth.seed import seed_all

async def main():
    async with async_session_factory() as session:
        await seed_all(session)
        await session.commit()

asyncio.run(main())
"
```

**Verify:**
```bash
DATABASE_URL="postgresql+asyncpg://...supabase..." python3 -c "
import asyncio
from sqlalchemy import select, func
from app.database import async_session_factory
from app.modules.auth.models import Role, User

async def main():
    async with async_session_factory() as session:
        roles = (await session.execute(select(func.count()).select_from(Role))).scalar()
        users = (await session.execute(select(func.count()).select_from(User))).scalar()
        print(f'roles={roles} users={users}')

asyncio.run(main())
"
```
Expect `roles=7 users=1` (or more, if seed creates more). Note the seeded admin email/password from `seed.py` — you'll need it to log in once deployed.

---

## Phase 2 — Backend on Render

**[MANUAL]**
1. In Render dashboard: **New → Web Service** → select this GitHub repo.
2. Configuration:
   | Field | Value |
   |---|---|
   | Name | `sculptnexus-api` (or similar) |
   | Region | Singapore (closest free-tier region to India) |
   | Branch | `main` |
   | Root Directory | `backend` |
   | Runtime | Docker |
   | Dockerfile Path | `backend/Dockerfile` (Render auto-detects since Root Directory is `backend`, so just `Dockerfile`) |
   | Instance Type | Free |
3. Render will use the existing `ENTRYPOINT ["./startup.sh"]` / `CMD ["api"]` from `backend/Dockerfile:19-20` — no Docker changes needed. This runs `uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 2` (see `backend/startup.sh:6`).
4. **Health Check Path:** `/api/v1/health` (already implemented at `backend/app/main.py:84-91`, now also reports scheduler status).
5. Set environment variables (Render dashboard → Environment):

   | Key | Value | Notes |
   |---|---|---|
   | `DATABASE_URL` | the Supabase pooler URL from Phase 1 | |
   | `SCHEDULER_BACKEND` | `apscheduler` | default — no Redis needed on Render |
   | `JWT_SECRET_KEY` | generate: `openssl rand -hex 32` | |
   | `JWT_REFRESH_SECRET_KEY` | generate: `openssl rand -hex 32` (different value) | |
   | `CORS_ORIGINS` | `["https://<your-vercel-app>.vercel.app"]` | exact Vercel URL from Phase 3 — comes after Phase 3, see note below |
   | `DEBUG` | `false` | **important** — flips cookie `secure` flag to `True` (`backend/app/modules/auth/router.py:36`); Render serves HTTPS so this is required for cookies to be sent at all |
   | `SENTRY_DSN` | leave empty | optional, skip for a test deploy |

   **Chicken-and-egg note on `CORS_ORIGINS`:** you don't have the Vercel URL yet at this point. Deploy with a placeholder (`["https://placeholder.vercel.app"]`) now, then come back and update it after Phase 3 gives you the real Vercel domain. Render redeploys automatically on env var change.

6. Click **Create Web Service**. Wait for the build + deploy to finish (first build can take 3-5 minutes).

**Verify:**
```bash
curl https://<your-render-app>.onrender.com/api/v1/health
```
Expect:
```json
{"status": "healthy", "version": "0.1.0", "scheduler": "apscheduler", "scheduler_running": true, "scheduled_jobs": ["auto-release-assignments", "process-recurring-costs"]}
```
If `scheduler_running` is `false` or the request times out, check Render's build logs for startup errors (most likely a bad `DATABASE_URL` — Supabase pooler connections fail loudly if the password or project ref is wrong).

---

## Phase 3 — Frontend on Vercel

**[CLAUDE]** — create `vercel.json` at the repo root (Vercel needs to know the frontend lives in `frontend/` and that `/api/*` should proxy to Render):

```json
{
  "buildCommand": "cd frontend && npm install && npm run build",
  "outputDirectory": "frontend/dist",
  "rewrites": [
    { "source": "/api/(.*)", "destination": "https://<your-render-app>.onrender.com/api/$1" },
    { "source": "/(.*)", "destination": "/index.html" }
  ]
}
```

Replace `<your-render-app>` with the actual Render service hostname from Phase 2. The second rewrite rule is required for the React Router SPA — without it, refreshing on a deep link like `/projects/123` returns a 404 from Vercel's static file server instead of falling through to `index.html`.

Commit this file:
```bash
git add vercel.json
git commit -m "Add Vercel config: SPA build + API proxy to Render"
```

**[MANUAL]**
1. In Vercel dashboard: **Add New → Project** → select this GitHub repo.
2. Vercel should auto-detect the `vercel.json` at root and use its `buildCommand`/`outputDirectory`. If the import wizard asks for a "Root Directory," leave it at the repo root (not `frontend/`) since `vercel.json` already handles the `cd frontend`.
3. No environment variables needed on the frontend — the API base URL in `frontend/src/shared/lib/axios.ts:4` is the relative path `/api/v1`, which the rewrite resolves to Render.
4. Click **Deploy**. Wait for build to finish (~1-2 minutes for a Vite build).
5. Note the deployed URL, e.g. `https://sculptnexus-xyz123.vercel.app`.

**[MANUAL] — close the loop from Phase 2:**
6. Go back to Render → Environment → update `CORS_ORIGINS` to `["https://sculptnexus-xyz123.vercel.app"]` (the real URL). Render redeploys automatically.

**Verify:**
```bash
curl -I https://<your-vercel-app>.vercel.app/api/v1/health
```
Expect `HTTP/2 200` and the same JSON body as the direct Render health check in Phase 2 — confirming the rewrite proxy works.

---

## Phase 4 — End-to-End Smoke Test

**[MANUAL]** — open `https://<your-vercel-app>.vercel.app` in a browser:

1. **Login** with the seeded admin credentials from Phase 1: `admin@ri-platform.com` / `ChangeMe123!` (`backend/app/modules/auth/seed.py:236-250`). Change this password immediately if this deployment will be shared with anyone beyond yourself.
2. Confirm the dashboard loads with data (resources, clients, projects — likely empty on a fresh Supabase DB, but the page itself should render without auth redirect loops).
3. Open browser DevTools → Application → Cookies. Confirm `access_token` and `refresh_token` cookies are set on the Vercel domain with `Secure` and `SameSite=Strict` flags — this confirms the proxy is working same-origin.
4. Create a test Client and Project to confirm writes hit Supabase correctly.
5. Check Render logs (Dashboard → Logs) for any 500s or DB connection errors during the above.

**Fallback if cookies don't appear / login silently fails:**
This means the browser treated the request as cross-origin despite the rewrite (can happen if `vercel.json` rewrite isn't matching, or if you bypassed the proxy and pointed the frontend directly at the Render URL). Debugging order:
1. Confirm Network tab shows requests going to `/api/v1/...` on the **Vercel** domain, not directly to `onrender.com`.
2. If you intentionally want direct cross-origin calls instead of the proxy, you must change `backend/app/modules/auth/router.py:35` from `"samesite": "strict"` to `"samesite": "none"` (requires `secure=True`, which `DEBUG=false` already gives you) and redeploy Render. This is a real code change — confirm with the user before making it, since it weakens CSRF protection slightly and is unrelated to the original request scope.

---

## Phase 5 — Known Limitations of This Test Deployment

| Limitation | Impact | Mitigation |
|---|---|---|
| Render free tier sleeps after 15 min idle | First request after idle takes 30-50s (cold start) | Acceptable for testing. For persistent uptime, add an UptimeRobot monitor pinging `/api/v1/health` every 5 min (see `FREE-HOSTING-FEASIBILITY.md`) — skip for a short-lived test |
| Supabase free project pauses after 7 days inactivity | First DB query after pause takes ~5-10s to wake | Self-heals; only matters if the test deploy sits untouched for a week |
| No automated DB backups on Supabase free tier | Test data loss is low-stakes here | Not a concern for a test deployment — do not put real client/financial data in it |
| `SCHEDULER_BACKEND=apscheduler` means scheduled jobs (auto-release, recurring costs) run inside the single Render instance | If Render restarts the instance near midnight IST, a job run could be skipped that day | Low-stakes for testing; both jobs are idempotent on next run (see `backend/app/jobs/scheduler.py`) |

---

## Rollback / Teardown

This deployment is fully additive — it does not touch the AWS production setup, local dev SQLite, or the `main` branch's runtime behavior (`SCHEDULER_BACKEND` still defaults to `apscheduler` locally too, which was already shipped and tested separately).

To tear down:
1. Render dashboard → service → Settings → Delete Web Service.
2. Vercel dashboard → project → Settings → Delete Project.
3. Supabase dashboard → project → Settings → Delete Project (or just leave it — free tier, auto-pauses after a week of inactivity anyway).
4. `git rm vercel.json` if you don't want to keep the config checked in (recommend keeping it — harmless, and reusable for the next test or for the real free-hosting migration described in `FREE-HOSTING-FEASIBILITY.md`).

---

## Open Items for the User (not resolvable by Claude Code alone)

- [ ] Render account created and repo access granted **[MANUAL]**
- [ ] Vercel account created and repo access granted **[MANUAL]**
- [ ] Supabase project created, password saved **[MANUAL]**
- [ ] Decide whether this test deployment should use a custom domain (not covered here — both Render and Vercel support free custom domains if needed later)
- [ ] Decide if/when to add UptimeRobot keepalive (only needed if this test deploy needs to stay warm for demo purposes beyond a quick check)
