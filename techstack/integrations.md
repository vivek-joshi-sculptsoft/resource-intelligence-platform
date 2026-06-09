# Integrations — Third-Party Services

## Current State

Per the PRD, **external integrations are explicitly out of scope** for the initial build. The platform is self-contained — no HRMS, no accounting software, no Slack, no payment gateway.

---

## Active Integrations (MVP)

| Service | Provider | Purpose | Integration Type | Cost |
|---------|----------|---------|-----------------|------|
| Error Tracking | Sentry | Frontend + backend error capture | SDK (Python + JS) | Free tier |
| Infra Metrics | AWS CloudWatch | EC2/RDS monitoring | AWS-native | Included with AWS |

---

## Planned Integrations (Future Phases)

### Email Notifications — AWS SES

| Attribute | Value |
|-----------|-------|
| **Provider** | AWS Simple Email Service (SES) |
| **Why** | Already on AWS, cheapest option ($0.10/1000 emails), no new vendor |
| **Integration** | boto3 SDK, called from Celery jobs |
| **Use cases** | Alert digests, password reset (if added), weekly utilization summaries |
| **Volume** | < 100 emails/day (7 roles × ~10 alerts/day) |
| **Cost** | Free from EC2 (first 62K/month), then $0.10/1000 |
| **Fallback** | Alerts remain in-app. Email is a delivery channel, not the source of truth. |
| **Credentials** | SES verified domain + IAM role with `ses:SendEmail` |

**When to add:** After Phase 1 MVP is stable and users request email notifications.

### PDF Export — WeasyPrint or ReportLab

| Attribute | Value |
|-----------|-------|
| **Purpose** | Generate invoice PDFs, utilization reports, project summaries |
| **Integration** | Python library, runs in Celery worker |
| **Cost** | Free (open source) |

### CSV/Excel Export — openpyxl

| Attribute | Value |
|-----------|-------|
| **Purpose** | Bulk data export for Finance team |
| **Integration** | Python library, runs in API or Celery worker |
| **Cost** | Free (open source) |

---

## Explicitly Not Planned

| Integration | Why Not |
|-------------|---------|
| Slack/Teams | PRD: in-app alerts only |
| HRMS (Zoho/BambooHR) | PRD: out of scope |
| Accounting (Tally/QuickBooks) | PRD: out of scope |
| Payment gateway | No external payments — invoicing is tracking, not collection |
| Calendar (Google/Outlook) | No calendar integration needed |
| Auto exchange rates (forex API) | PRD: manual exchange rate entry only |
