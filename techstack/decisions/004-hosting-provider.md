# ADR-004: Hosting Provider & Architecture

**Status:** Accepted
**Date:** 2026-06-09
**Deciders:** Engineering Team

---

## Context

We need to host a Python/FastAPI backend, PostgreSQL database, Redis, and static React frontend. The team has an existing AWS account. Budget is $50-200/mo. There is no DevOps engineer — the 1-2 full-stack developers manage infrastructure. The application serves ~20 concurrent internal users.

## Decision

> We will deploy on **AWS** using a **single EC2 instance (t3.small) with Docker Compose** for the backend, **RDS** for PostgreSQL, and **S3 + CloudFront** for the frontend.

## Rationale

- Existing AWS account eliminates onboarding friction
- Docker Compose on EC2 is the simplest production deployment: `docker-compose up -d` deploys 4 containers (Nginx, FastAPI, Celery, Redis)
- Total cost ~$36/mo, well within budget
- ap-south-1 (Mumbai) region for lowest latency to India-based users
- RDS handles database backups, patching, and recovery automatically

## Alternatives Considered

| Alternative | Why Rejected |
|-------------|-------------|
| Vercel + Railway | Vercel is Next.js-optimized (we're using React+Vite). Railway is great but adds a second vendor when we're already on AWS. |
| AWS ECS / Fargate | Container orchestration overhead for a single-instance deployment. Task definitions, service discovery, ALB — all unnecessary for 20 users. |
| AWS Lambda + API Gateway | Cold starts hurt UX for an always-active internal tool. Stateless model complicates Celery and persistent connections. |
| DigitalOcean | Cheaper compute, but team is already on AWS. Switching providers for $5/mo savings isn't worth the setup time. |
| Render / Fly.io | Good PaaS options but add vendor dependency when AWS already covers all needs. |

## Consequences

**Positive:**
- One cloud provider for everything — no multi-vendor complexity
- Docker Compose is the same in dev and production — minimal deployment surprise
- Full control over Nginx config, Redis tuning, container resource limits

**Negative / Trade-offs:**
- Single EC2 = single point of failure. Acceptable for internal tool. Recovery: launch new instance from AMI (~15 min).
- More ops responsibility than a PaaS (Railway/Render). Mitigated by Docker Compose simplicity.
- No auto-scaling. Not needed at this user count.

**Neutral:**
- Can migrate to ECS/Fargate later without changing Docker images — just add task definitions.

## Review Trigger

Revisit if uptime SLA is required (add ALB + multi-AZ) or if team wants zero-ops deployment (switch to Fargate).
