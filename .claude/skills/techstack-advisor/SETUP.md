# TechStack Advisor — Setup Guide

Conducts a structured tech stack interview, recommends the right technologies for your project, confirms with you, then generates a complete `/techstack/` document set including Architecture Decision Records.

---

## Setup

### Claude Code
```bash
cp -r techstack-advisor/ ~/.claude/skills/
```

### Claude.ai Project
1. Paste `claude-ai-project-prompt.md` as custom instructions
2. Upload knowledge files:
   - `references/stack-options.md`
   - `references/adr-template.md`
   - `references/cost-estimate-guide.md`
3. Enable File Creation

---

## Usage

```bash
# Start the interview (reads PRD.md/FSD.md automatically if present)
claude "Brainstorm our tech stack"

# With explicit context
claude "Help me decide the tech stack for our resource management SaaS"

# Skip to recommendations (if you already know your preferences)
claude "Recommend a tech stack: Next.js frontend, Node.js backend, PostgreSQL DB, AWS hosting"

# Regenerate just the cost estimate
claude "Regenerate techstack/cost-estimate.md based on the confirmed stack"

# Add an ADR for a new decision
claude "Add an ADR for our decision to use Razorpay over Stripe"
```

---

## Output

```
techstack/
├── main.md              ← Start here — executive summary + architecture diagram
├── frontend.md          ← Framework, libraries, state management, testing
├── backend.md           ← Framework, API design, ORM, error handling
├── database.md          ← Primary DB, cache, search, file storage, backups
├── auth.md              ← Auth provider, flows, token strategy, RBAC
├── infra.md             ← Hosting, compute, networking, CDN, environments
├── devops.md            ← CI/CD, Docker, secrets, deployment strategy
├── integrations.md      ← All third-party services
├── monitoring.md        ← Error tracking, APM, logging, alerts
├── cost-estimate.md     ← Monthly infra cost at MVP/Growth/Scale
└── decisions/
    ├── 001-backend-framework.md
    ├── 002-database.md
    ├── 003-frontend-framework.md
    ├── 004-hosting-provider.md
    ├── 005-auth-strategy.md
    ├── 006-api-design.md
    ├── 007-background-jobs.md
    └── 008-monolith-vs-microservices.md
```

**Open `techstack/main.md` first** — it has the full tech table, architecture diagram, and links to all other files.

---

## Interview Flow

The skill interviews in 3 short rounds before making recommendations:

| Round | Topics | When |
|-------|--------|------|
| Round 1 | Frontend, backend, database preference | First message |
| Round 2 | Hosting, auth, background jobs, integrations | After Round 1 |
| Round 3 | Team size, timeline, budget, existing infra | After Round 2 |

If PRD.md / FSD.md exist in the project, the skill reads them first and may skip obvious questions that are already answered.

---

## Pipeline Position

```
PRD Brainstorm → TechStack Advisor → FSD Generator → Repo Architect → JIRA Tickets
                                                            ↓
                                                    Mockup Generator
```

Run TechStack Advisor after the PRD is finalized and before the FSD or Repo Architect — tech choices influence both the FSD's technical decisions and the repo structure.

---

## Files

| File | Purpose |
|------|---------|
| `SKILL.md` | Core instructions |
| `claude-ai-project-prompt.md` | System prompt for Claude.ai |
| `references/stack-options.md` | Curated options per layer with tradeoffs and selection rules |
| `references/adr-template.md` | ADR format template with filled example |
| `references/cost-estimate-guide.md` | Pricing data for infra cost estimate table |
