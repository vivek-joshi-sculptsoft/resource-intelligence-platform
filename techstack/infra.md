# Infrastructure — AWS

## Cloud Provider

**Amazon Web Services (AWS)** — existing account, team familiarity, broadest service catalog.

**Region:** `ap-south-1` (Mumbai) — lowest latency for India-based internal users.

---

## Compute

### Backend: EC2 (t3.small)

Single EC2 instance running Docker Compose with 4 containers:
1. **Nginx** — reverse proxy, SSL termination, static file serving
2. **FastAPI** — uvicorn with 2 workers
3. **Celery worker** — background job processor
4. **Redis 7** — Celery broker + application cache

| Spec | Value |
|------|-------|
| Instance type | t3.small (2 vCPU, 2 GB RAM) |
| Storage | 30 GB gp3 EBS |
| OS | Amazon Linux 2023 |
| IP | Elastic IP (static) |

**Scaling strategy:** Vertical first. Move to t3.medium (4 GB RAM) if memory pressure occurs. Horizontal scaling (ALB + multiple EC2) only if >200 concurrent users — not expected.

---

## Networking

| Component | Configuration |
|-----------|--------------|
| VPC | Default VPC (single AZ sufficient for internal tool) |
| Security Group (EC2) | Inbound: 443 (HTTPS from CloudFront), 22 (SSH from admin IP) |
| Security Group (RDS) | Inbound: 5432 from EC2 security group only |
| Elastic IP | Assigned to EC2 for stable DNS |

No NAT Gateway, no private subnets, no ALB at MVP — these add $30+/mo with no benefit for 20 users. Add when/if the tool goes multi-AZ.

---

## Database: RDS PostgreSQL

| Setting | Value |
|---------|-------|
| Engine | PostgreSQL 16 |
| Instance | db.t4g.micro (2 vCPU, 1 GB RAM) |
| Storage | 20 GB gp3, auto-scaling to 100 GB |
| Multi-AZ | No (internal tool, RTO < 1 hour acceptable) |
| Backups | Automated, 7-day retention |
| Encryption | At rest (AWS-managed key) |

---

## Frontend Deploy: S3 + CloudFront

React + Vite builds to static files (`dist/`), uploaded to S3, served via CloudFront.

| Component | Configuration |
|-----------|--------------|
| S3 bucket | `ri-platform-frontend`, private, website hosting disabled |
| CloudFront | Origin = S3 via OAC, HTTPS only, custom domain (optional) |
| Cache behavior | `/api/*` → EC2 origin (no cache), `/*` → S3 origin (cache 1 day) |
| Invalidation | `/*` invalidation on each deploy |

**Why not serve frontend from EC2?** Separation of concerns. S3+CloudFront is cheaper, faster (edge-cached), and doesn't compete for EC2 resources.

---

## CDN

CloudFront serves double duty:
1. **Frontend static assets** — React JS/CSS/HTML from S3
2. **API proxy** — `/api/*` routes to EC2 origin (HTTPS, no caching)

Single CloudFront distribution, two origin behaviors. Users hit one domain for everything.

---

## DNS & SSL

| Component | Setup |
|-----------|-------|
| Domain | Custom domain via Route 53 (optional — can use CloudFront default domain initially) |
| SSL | AWS Certificate Manager (ACM) — free, auto-renewing |
| SSL on EC2 | Let's Encrypt via Nginx (for direct EC2 access during dev) or ACM via CloudFront |

---

## Environments

| Environment | Infrastructure | Purpose |
|-------------|---------------|---------|
| Local | Docker Compose (full stack) | Development |
| Production | EC2 + RDS + S3/CloudFront | Live system |

**No staging environment at MVP.** With 1-2 devs and a week timeline, a staging env doubles infra cost for minimal benefit. Add staging when the team grows or before Phase 2 financial features go live.

---

## Disaster Recovery

| Scenario | Recovery |
|----------|----------|
| EC2 failure | Launch new instance from AMI, attach EBS snapshot, docker-compose up |
| RDS failure | Automatic failover (if Multi-AZ) or restore from automated backup (< 1 hour) |
| Data corruption | RDS point-in-time recovery (5-minute granularity) |
| Region outage | Accept downtime (internal tool, not customer-facing SLA) |

**AMI snapshots:** Weekly AMI of the EC2 instance for fast recovery.
