# DevOps — CI/CD, Docker, Deployment

## Version Control

**Git** with **trunk-based development**.

| Convention | Rule |
|------------|------|
| Main branch | `main` — always deployable |
| Feature branches | `feat/{module}-{description}` (e.g., `feat/auth-jwt-login`) |
| Bug fixes | `fix/{description}` |
| Branch lifetime | Short-lived — merge within 1-2 days |
| Merge strategy | Squash merge to main |

No GitFlow — overkill for 1-2 devs. Feature branches merge directly to main.

---

## CI/CD Pipeline

**GitHub Actions** — runs on every push to main and on PRs.

### Pipeline Stages

```
PR opened / push to main
    │
    ├── 1. Lint (parallel)
    │   ├── Frontend: eslint + tsc --noEmit
    │   └── Backend: ruff check + mypy
    │
    ├── 2. Test (parallel)
    │   ├── Frontend: vitest run
    │   └── Backend: pytest (with test PostgreSQL via service container)
    │
    ├── 3. Build (parallel)
    │   ├── Frontend: vite build → dist/
    │   └── Backend: docker build
    │
    └── 4. Deploy (main branch only)
        ├── Frontend: aws s3 sync dist/ + CloudFront invalidation
        └── Backend: docker push to ECR → SSH deploy on EC2
```

### Deploy Step (Backend)

```bash
# On EC2 (triggered by GitHub Actions via SSH)
docker compose pull
docker compose up -d --remove-orphans
docker compose exec api alembic upgrade head
```

---

## Containerization

### Docker Setup

**Backend Dockerfile** (multi-stage):

```dockerfile
# Stage 1: Build
FROM python:3.12-slim AS builder
WORKDIR /app
COPY pyproject.toml .
RUN pip install --no-cache-dir .

# Stage 2: Runtime
FROM python:3.12-slim
WORKDIR /app
COPY --from=builder /usr/local/lib/python3.12/site-packages /usr/local/lib/python3.12/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin
COPY app/ app/
COPY alembic/ alembic/
COPY alembic.ini .
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "2"]
```

### Docker Compose (Production)

Default — `SCHEDULER_BACKEND=apscheduler` in `.env`, scheduled jobs run inside the API process:

```yaml
services:
  nginx:
    image: nginx:alpine
    ports: ["443:443", "80:80"]
    volumes: ["./nginx.conf:/etc/nginx/nginx.conf"]
    depends_on: [api]

  api:
    image: ${ECR_REPO}/ri-platform-api:latest
    env_file: .env
    expose: ["8000"]
```

Optional — set `SCHEDULER_BACKEND=celery` in `.env` and add these services:

```yaml
  celery-worker:
    image: ${ECR_REPO}/ri-platform-api:latest
    command: celery -A app.jobs.celery_app worker -l info
    env_file: .env
    depends_on: [redis]

  celery-beat:
    image: ${ECR_REPO}/ri-platform-api:latest
    command: celery -A app.jobs.celery_app beat -l info
    env_file: .env
    depends_on: [redis]

  redis:
    image: redis:7-alpine
    volumes: ["redis_data:/data"]

volumes:
  redis_data:
```

---

## Environment Management

| Environment | Config Source |
|-------------|-------------|
| Local | `.env` file (git-ignored) |
| Production | AWS Systems Manager Parameter Store |
| CI | GitHub Actions secrets |

`.env.example` checked into git with placeholder values. Real secrets never in code.

---

## Infrastructure as Code

**Not at MVP.** With one EC2 + one RDS + one S3 bucket, manual setup via AWS Console is faster than writing Terraform for a 1-week build.

**When to add Terraform:** When adding staging environment, or if the team grows past 3 engineers. At that point, codify the existing infra.

---

## Deployment Strategy

**Rolling restart** via Docker Compose. With a single EC2 instance:

```bash
docker compose pull          # Pull new images
docker compose up -d         # Restart changed services (zero-downtime with uvicorn graceful reload)
```

Brief (~2-5 second) interruption during container restart. Acceptable for an internal tool with 20 users.

**When to upgrade:** Add blue-green deployment (ALB + two target groups) if zero-downtime deploys become a requirement.

---

## Rollback Procedure

1. **Backend:** `docker compose` with previous image tag: `docker compose up -d --no-deps api` (add `celery-worker celery-beat` if `SCHEDULER_BACKEND=celery`)
2. **Frontend:** Re-deploy previous S3 build: `aws s3 sync s3://ri-platform-frontend-backup/ s3://ri-platform-frontend/`
3. **Database:** Alembic downgrade: `alembic downgrade -1` (only if migration was the issue)
4. **Nuclear:** Restore EC2 from weekly AMI snapshot

---

## Local Development

### Quick Start (no Docker required)

The backend defaults to SQLite when no `DATABASE_URL` is set, so the simplest local setup is:

```bash
cd backend
pip install -e ".[dev]"
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

SQLite database auto-creates on first startup (`ri_platform.db`). No Docker, no PostgreSQL, no Redis needed for basic API development. Scheduled jobs run in-process via APScheduler (default `SCHEDULER_BACKEND`).

### Full Stack (Docker Compose)

For production-parity testing with PostgreSQL (Redis/Celery only needed if testing that backend):

```yaml
# docker-compose.dev.yml
services:
  api:
    build: ./backend
    command: uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
    volumes: ["./backend/app:/app/app"]  # Hot reload
    env_file: .env
    ports: ["8000:8000"]

  postgres:
    image: postgres:16-alpine
    environment:
      POSTGRES_DB: ri_platform
      POSTGRES_USER: dev
      POSTGRES_PASSWORD: dev
    ports: ["5432:5432"]
    volumes: ["pg_data:/var/lib/postgresql/data"]

  # Behind the "celery" Compose profile — only started when testing SCHEDULER_BACKEND=celery
  celery-worker:
    profiles: ["celery"]
    build: ./backend
    command: celery -A app.jobs.celery_app worker -l info
    volumes: ["./backend/app:/app/app"]
    env_file: .env

  redis:
    profiles: ["celery"]
    image: redis:7-alpine
    ports: ["6379:6379"]

volumes:
  pg_data:
```

To use PostgreSQL locally, set `DATABASE_URL=postgresql+asyncpg://dev:dev@localhost:5432/ri_platform` in `.env`. To test the Celery backend, also set `SCHEDULER_BACKEND=celery` and run `docker compose --profile celery -f docker-compose.dev.yml up`.

Frontend runs outside Docker via `npm run dev` (Vite dev server with API proxy to localhost:8000).
