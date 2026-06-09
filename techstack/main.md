# Tech Stack — Resource Intelligence Platform

## Project Context

An internal web application for an IT services company (~30-40 employees) to replace Google Sheets for tracking resource allocations, project delivery, client billing, and financial margins. 14 entities, 13 modules, 3 build phases. 7 user roles with granular RBAC (105 permission rows). Multi-currency billing normalized to INR. Built by 1-2 engineers using Claude Code in ~1 week for Phase 1 MVP.

---

## Architecture Overview

```
┌──────────────────────────────────────────────────┐
│                   CloudFront CDN                  │
│            (React + Vite static build)            │
│                    S3 Bucket                      │
└─────────────────────┬────────────────────────────┘
                      │ HTTPS /api/*
┌─────────────────────▼────────────────────────────┐
│              EC2 (t3.small) — Docker Compose       │
│  ┌──────────┐  ┌───────────────┐  ┌───────────┐  │
│  │  Nginx   │→ │   FastAPI     │  │  Celery   │  │
│  │ reverse  │  │  (uvicorn)    │  │  worker   │  │
│  │ proxy    │  │               │  │  + beat   │  │
│  └──────────┘  └───────┬───────┘  └─────┬─────┘  │
│                        │                │         │
│                ┌───────▼────────────────▼──────┐  │
│                │        Redis 7               │  │
│                │  (Celery broker + cache)      │  │
│                └──────────────────────────────┘  │
└────────────────────────┬─────────────────────────┘
                         │ port 5432
               ┌─────────▼──────────┐
               │  RDS PostgreSQL 16  │
               │  (db.t4g.micro)     │
               └────────────────────┘
```

---

## Technology Summary

| Layer | Choice | Version |
|-------|--------|---------|
| Frontend Framework | React + Vite | React 19, Vite 6 |
| UI Library | shadcn/ui + Tailwind CSS | Tailwind 4 |
| Routing | React Router | v7 |
| State (Server) | TanStack Query | v5 |
| State (Client) | Zustand | v5 |
| Backend Framework | FastAPI | 0.115+ |
| Language | Python | 3.12 |
| ORM | SQLAlchemy + Alembic | SQLAlchemy 2.0 |
| Validation | Pydantic | v2 |
| Primary Database | PostgreSQL | 16 (AWS RDS) |
| Cache / Broker | Redis | 7 (Docker on EC2) |
| Background Jobs | Celery + celery-beat | 5.4 |
| Auth | Custom JWT (python-jose + argon2) | — |
| Hosting (Frontend) | AWS S3 + CloudFront | — |
| Hosting (Backend) | AWS EC2 (t3.small) + Docker Compose | — |
| CI/CD | GitHub Actions | — |
| Error Tracking | Sentry | Free tier |
| Infra Metrics | AWS CloudWatch | — |
| Email (future) | AWS SES | — |

---

## Key Architectural Decisions

1. **Modular monolith over microservices.** 1-2 devs, 1-week timeline, 20 concurrent users. Two processes (FastAPI + Celery worker) in Docker Compose, 13 modules as Python packages. See [ADR-008](decisions/008-monolith-vs-microservices.md).

2. **React SPA over Next.js.** No SSR, no SEO, no server-side features needed. React + Vite is lighter, faster to build, and eliminates server/client boundary confusion. See [ADR-003](decisions/003-frontend-framework.md).

3. **Custom JWT auth over managed providers.** Internal tool with email/password only. Auth0/Cognito add cost and complexity for no benefit here. RBAC lives in the database (RolePermission table) and is enforced via FastAPI middleware. See [ADR-005](decisions/005-auth-strategy.md).

4. **PostgreSQL on RDS over Supabase.** Already on AWS, need DECIMAL precision for financial data, JSONB for audit logs, UUID PKs. RDS gives full control over extensions, connection limits, and backups. See [ADR-002](decisions/002-database.md).

5. **Single EC2 with Docker Compose over ECS/Fargate.** At 20 concurrent users, container orchestration is pure overhead. One box, one `docker-compose up`, done. See [ADR-004](decisions/004-hosting-provider.md).

---

## Document Index

| File | Contents |
|------|----------|
| [frontend.md](frontend.md) | React + Vite setup, libraries, folder structure, testing |
| [backend.md](backend.md) | FastAPI architecture, project structure, API design |
| [database.md](database.md) | PostgreSQL schema, migrations, caching, backups |
| [auth.md](auth.md) | JWT strategy, RBAC implementation, password policy |
| [infra.md](infra.md) | AWS setup, EC2, RDS, S3, CloudFront, networking |
| [devops.md](devops.md) | CI/CD, Docker, deployment strategy, local dev |
| [integrations.md](integrations.md) | Third-party services (current and planned) |
| [monitoring.md](monitoring.md) | Sentry, CloudWatch, logging, alerting |
| [cost-estimate.md](cost-estimate.md) | Monthly cost at MVP, Growth, Scale tiers |
| [decisions/](decisions/) | Architecture Decision Records (8 ADRs) |

---

## Stack Fitness Check

- **Team size (1-2 devs):** Monolith + Docker Compose = one deployment, one codebase, zero coordination overhead.
- **Timeline (~1 week):** FastAPI + Pydantic auto-generates OpenAPI docs. React + shadcn/ui gives production-quality components instantly.
- **Scale (20 concurrent users):** A t3.small handles 10,000x this load. Room to grow without re-architecting.
- **Budget ($50-200/mo):** Estimated $20-35/mo at MVP. Entire stack fits in the lower end.
- **AI-assisted development:** Python + React are the two ecosystems Claude Code knows deepest. SQLAlchemy, FastAPI, and React have massive training data coverage.
