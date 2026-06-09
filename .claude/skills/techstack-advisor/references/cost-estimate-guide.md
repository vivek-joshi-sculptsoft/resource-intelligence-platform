# Cost Estimate Guide

Reference pricing for building the monthly infra cost table in `techstack/cost-estimate.md`. All prices approximate as of mid-2026 — verify against provider pricing pages before finalizing.

---

## Three Tiers

| Tier | Definition | Typical signals |
|------|-----------|----------------|
| **MVP** | 0–1K monthly active users, early customers, low traffic | < 50 req/min, < 10GB data, 1 environment |
| **Growth** | 1K–50K MAU, product-market fit, scaling | 50–500 req/min, < 500GB data, staging + prod |
| **Scale** | 50K+ MAU, sustained load, reliability requirements | 500+ req/min, TBs of data, multi-region, SLA |

---

## Compute

### Railway

| Tier | Config | Est. Cost |
|------|--------|-----------|
| MVP | Starter plan, 1 service, 512MB RAM | $5–$20/mo |
| Growth | Pro plan, 2 services (API + worker), 1GB RAM each | $40–$100/mo |
| Scale | Multiple services, 2–4GB RAM, auto-sleep off | $150–$400/mo |

### Render

| Tier | Config | Est. Cost |
|------|--------|-----------|
| MVP | Free web service (sleeps after 15min), or $7/mo starter | $0–$25/mo |
| Growth | Standard ($25/mo per service), 2 services | $50–$100/mo |
| Scale | Pro services, multiple instances | $200–$500/mo |

### AWS ECS Fargate

| Tier | Config | Est. Cost |
|------|--------|-----------|
| MVP | 0.25 vCPU, 512MB, 1 task | $10–$30/mo |
| Growth | 0.5 vCPU, 1GB, 2 tasks + ALB | $80–$200/mo |
| Scale | 1+ vCPU, 2GB, 4+ tasks + ALB + NAT | $400–$1500/mo |

### Vercel (Frontend)

| Tier | Config | Est. Cost |
|------|--------|-----------|
| MVP | Hobby plan | $0/mo |
| Growth | Pro plan | $20/mo |
| Scale | Pro + usage | $20–$150/mo |

---

## Database

### Supabase

| Tier | Plan | Est. Cost |
|------|------|-----------|
| MVP | Free (500MB DB, 50K MAU auth) | $0/mo |
| Growth | Pro ($25/mo, 8GB DB, 100K MAU) | $25/mo |
| Scale | Pro + compute add-ons | $100–$300/mo |

### Neon (Serverless PostgreSQL)

| Tier | Plan | Est. Cost |
|------|------|-----------|
| MVP | Free tier (0.5GB, scale-to-zero) | $0/mo |
| Growth | Launch ($19/mo, 10GB) | $19/mo |
| Scale | Scale ($69/mo, 50GB) | $69–$200/mo |

### AWS RDS PostgreSQL

| Tier | Config | Est. Cost |
|------|--------|-----------|
| MVP | db.t3.micro, 20GB | $15–$25/mo |
| Growth | db.t3.small, 100GB, Multi-AZ | $80–$150/mo |
| Scale | db.r6g.large, 500GB, Multi-AZ | $400–$800/mo |

---

## Cache (Redis)

### Upstash Redis

| Tier | Plan | Est. Cost |
|------|------|-----------|
| MVP | Free (10K commands/day) | $0/mo |
| Growth | Pay-per-use (~1M commands/day) | $10–$30/mo |
| Scale | Fixed ($120/mo 1GB dedicated) | $120–$300/mo |

### Redis Cloud (Redis Ltd.)

| Tier | Plan | Est. Cost |
|------|------|-----------|
| MVP | Free (30MB) | $0/mo |
| Growth | Paid tier 100MB | $7–$25/mo |
| Scale | 1GB+ | $50–$200/mo |

---

## File Storage

### AWS S3

| Tier | Usage | Est. Cost |
|------|-------|-----------|
| MVP | < 10GB storage, < 10GB transfer | $1–$5/mo |
| Growth | 100GB storage, 100GB transfer | $10–$25/mo |
| Scale | 1TB+ storage, significant transfer | $50–$300/mo |

### Supabase Storage

| Tier | Included | Est. Cost |
|------|----------|-----------|
| MVP | 1GB (Free plan) | $0 |
| Growth | 100GB (Pro plan, included) | Included in Pro $25 |
| Scale | $0.021/GB beyond Pro | $0–$50/mo extra |

### Cloudinary

| Tier | Plan | Est. Cost |
|------|------|-----------|
| MVP | Free (25GB storage, 25GB bandwidth) | $0/mo |
| Growth | Plus ($89/mo, 75GB storage) | $89/mo |
| Scale | Custom | $200+/mo |

---

## Authentication

### Auth0

| Tier | MAU | Est. Cost |
|------|-----|-----------|
| MVP | < 7,500 MAU | $0/mo (Free) |
| Growth | 7.5K–50K MAU | $23–$240/mo |
| Scale | 50K+ MAU | $240+/mo (custom) |

### Clerk

| Tier | MAU | Est. Cost |
|------|-----|-----------|
| MVP | < 10K MAU | $0/mo (Free) |
| Growth | 10K+ MAU | $25/mo base + $0.02/MAU |
| Scale | 50K+ MAU | $1,000+/mo |

### Supabase Auth

Included with Supabase plan — no additional cost.

---

## Email

### Resend

| Tier | Volume | Est. Cost |
|------|--------|-----------|
| MVP | < 3,000 emails/mo | $0/mo |
| Growth | 100K emails/mo | $20/mo |
| Scale | 1M emails/mo | $90/mo |

### SendGrid

| Tier | Volume | Est. Cost |
|------|--------|-----------|
| MVP | < 100 emails/day | $0/mo |
| Growth | 100K emails/mo | $19.95/mo |
| Scale | 1M emails/mo | $89.95/mo |

### AWS SES

| Tier | Volume | Est. Cost |
|------|--------|-----------|
| MVP | 62K emails/mo (free from EC2) | $0/mo |
| Growth | 100K emails/mo | $10/mo |
| Scale | 1M emails/mo | $100/mo |

---

## Background Jobs

### BullMQ / Celery (self-hosted on Railway/Render)

Cost is included in compute cost — worker is just another service. Add $5–$20/mo for a dedicated worker process at MVP.

### Inngest

| Tier | Plan | Est. Cost |
|------|------|-----------|
| MVP | Free (50K function runs/mo) | $0/mo |
| Growth | Pro ($50/mo, 500K runs) | $50/mo |
| Scale | Enterprise | Custom |

---

## Monitoring

### Sentry

| Tier | Plan | Est. Cost |
|------|------|-----------|
| MVP | Free (5K errors/mo) | $0/mo |
| Growth | Team ($26/mo, 50K errors) | $26/mo |
| Scale | Business ($80/mo+) | $80–$300/mo |

### Datadog

| Tier | Config | Est. Cost |
|------|--------|-----------|
| MVP | Free trial / small team | $0–$15/mo |
| Growth | Pro (per host) | $15/host/mo |
| Scale | Multiple hosts + logs + APM | $200–$1000+/mo |

### Better Uptime (Uptime Monitoring)

| Tier | Plan | Est. Cost |
|------|------|-----------|
| MVP | Free (10 monitors) | $0/mo |
| Growth | Freelancer ($20/mo) | $20/mo |

---

## Sample Cost Summary Tables

### Node.js + Supabase + Railway + Vercel Stack

| Service | MVP | Growth | Scale |
|---------|-----|--------|-------|
| Frontend (Vercel) | $0 | $20 | $50 |
| Backend (Railway) | $10 | $60 | $200 |
| Database (Supabase) | $0 | $25 | $150 |
| Cache (Upstash) | $0 | $20 | $80 |
| Storage (Supabase) | $0 | included | $30 |
| Auth (Supabase) | $0 | included | included |
| Email (Resend) | $0 | $20 | $50 |
| Error tracking (Sentry) | $0 | $26 | $80 |
| Uptime (Better Uptime) | $0 | $20 | $20 |
| **Total** | **~$10/mo** | **~$191/mo** | **~$660/mo** |

### NestJS + AWS Stack

| Service | MVP | Growth | Scale |
|---------|-----|--------|-------|
| Frontend (Vercel) | $0 | $20 | $50 |
| Backend (ECS Fargate) | $20 | $150 | $600 |
| Database (RDS) | $20 | $100 | $500 |
| Cache (Upstash) | $0 | $25 | $120 |
| Storage (S3) | $2 | $20 | $100 |
| Auth (Auth0) | $0 | $50 | $240 |
| Email (SES) | $0 | $10 | $50 |
| Error tracking (Sentry) | $0 | $26 | $80 |
| Monitoring (CloudWatch) | $0 | $20 | $80 |
| **Total** | **~$42/mo** | **~$421/mo** | **~$1,820/mo** |

---

## Tier Upgrade Triggers

Use these as guidance for the "when to move up" notes in cost-estimate.md:

| Signal | Action |
|--------|--------|
| > 1K MAU or > 100K API calls/day | Move DB to paid plan |
| Response time degrading | Add Redis cache layer |
| > 3K emails/day | Move to paid email plan |
| DB storage > 1GB | Upgrade Supabase / Neon tier |
| > 7.5K MAU (Auth0) or > 10K (Clerk) | Upgrade auth plan |
| Error volume exceeding free Sentry | Upgrade or self-host Sentry |
| Deployment taking > 5 min | Add dedicated CI/CD runners |
