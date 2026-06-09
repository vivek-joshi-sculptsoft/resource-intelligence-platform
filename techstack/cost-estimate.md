# Monthly Infrastructure Cost Estimate

## Three Tiers

| Tier | Definition | Trigger to Upgrade |
|------|-----------|-------------------|
| **MVP** | Current state: 20-40 users, internal only | — |
| **Growth** | Team expands, 100+ users, staging env needed | > 50 concurrent users or adding staging |
| **Scale** | Multiple offices, high availability required | > 500 users or SLA requirements |

---

## Cost Breakdown

| Service | MVP (20-40 users) | Growth (100+ users) | Scale (500+ users) |
|---------|-------------------|--------------------|--------------------|
| EC2 (t3.small, ap-south-1) | $15/mo | $30/mo (t3.medium) | $120/mo (2x t3.medium + ALB) |
| RDS PostgreSQL (db.t4g.micro) | $13/mo (free tier yr 1: $0) | $50/mo (db.t4g.small, Multi-AZ) | $200/mo (db.t4g.medium, Multi-AZ) |
| S3 (frontend + uploads) | $1/mo | $3/mo | $10/mo |
| CloudFront | $1/mo | $5/mo | $20/mo |
| Elastic IP | $3.65/mo | $3.65/mo | $7.30/mo (2 IPs) |
| EBS (30GB gp3) | $2.40/mo | $4.80/mo (60GB) | $12/mo (150GB) |
| Redis (Docker on EC2) | $0 (included in EC2) | $0 | $13/mo (ElastiCache t4g.micro) |
| Sentry | $0 (free tier) | $26/mo (Team plan) | $26/mo |
| CloudWatch | $0 (basic) | $5/mo (detailed + logs) | $15/mo |
| UptimeRobot | $0 (free tier) | $0 | $7/mo (Pro) |
| Email — SES (future) | $0 | $1/mo | $5/mo |
| **Total** | **~$36/mo** | **~$128/mo** | **~$435/mo** |

*Note: RDS is free-tier eligible for the first 12 months (750 hrs/mo db.t4g.micro). MVP cost drops to ~$23/mo during that period.*

---

## Year 1 Projection

| Period | Monthly Cost | Annual |
|--------|-------------|--------|
| Months 1-12 (RDS free tier) | ~$23/mo | ~$276 |
| Months 13+ (post free tier) | ~$36/mo | ~$432 |

---

## Cost Optimization Notes

| Optimization | Savings | When |
|-------------|---------|------|
| EC2 Reserved Instance (1-year) | ~40% on compute | After 3 months if committed |
| RDS Reserved Instance (1-year) | ~35% on database | After free tier expires |
| S3 Intelligent-Tiering | Minimal at this scale | When storage > 50GB |
| Spot instances for dev/staging | ~70% on compute | When staging env is added |

---

## What's NOT in This Estimate

| Item | Why Excluded |
|------|-------------|
| Domain registration | ~$12/year, one-time |
| Developer machines | Existing hardware |
| GitHub (repo hosting) | Free for private repos |
| Claude Code (development tool) | Separate subscription |
| Slack/Teams | Not integrated |

---

## Tier Upgrade Triggers

| Signal | Action | Cost Impact |
|--------|--------|------------|
| CPU > 80% sustained | EC2 → t3.medium | +$15/mo |
| DB connections > 80 | RDS → t4g.small | +$37/mo |
| Team > 3 devs | Add staging environment | +$50/mo (duplicate minimal infra) |
| Uptime SLA required | RDS Multi-AZ + second EC2 + ALB | +$150/mo |
| > 5K Sentry errors/mo | Sentry Team plan | +$26/mo |
