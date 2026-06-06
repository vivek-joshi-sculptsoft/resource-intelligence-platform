# Resource Intelligence & Project Economics Platform

An internal tool for an IT services company (~30-40 employees) to track resource allocations, project delivery, client billing, and financial margins. Replaces Google Sheets with a structured, role-based platform.

## What This Repo Contains

This repository holds the **complete project specification** — not application code (yet). Everything a developer or AI coding assistant needs to build the platform module by module.

```
project/
├── prd/PRD.md                        # Product requirements (business perspective)
├── fsd/FSD.md                        # Functional specifications (technical detail)
├── shared/                           # Cross-cutting reference documents
│   ├── ENTITIES.md                   # Master entity definitions (14 entities)
│   ├── BUSINESS-RULES.md             # Formulas, calculations, constraints
│   ├── ACCESS-MATRIX.md              # Role-based access (7 roles × 15 data types)
│   └── GLOSSARY.md                   # Term definitions
├── modules/                          # Module-wise specifications (13 modules)
│   └── {NN}-{module-name}/
│       ├── REQUIREMENTS.md           # What this module does + acceptance criteria
│       ├── SCHEMA.md                 # Entity fields owned by this module
│       ├── API.md                    # REST endpoint definitions
│       ├── SCREENS.md               # UI view specifications
│       ├── DEPENDENCIES.md          # Upstream and downstream module dependencies
│       └── JOBS.md                  # Background jobs (only if module has any)
├── tickets/                          # JIRA-ready story breakdowns per module
│   └── {module-name}.md
├── CLAUDE.md                         # Master build instructions for Claude Code
├── ROADMAP.md                        # Phase-wise build plan with estimates
└── README.md                         # This file
```

## Modules

| # | Module | Phase | Key Entities | Description |
|---|---|---|---|---|
| 01 | auth-and-roles | 1 | Role, RolePermission, User | Authentication, authorization, role management |
| 02 | client-management | 1 | Client | Client CRUD and portfolio tracking |
| 03 | project-management | 1 | Project | Project lifecycle with 3 types (FP/T&M/Onboarding) |
| 04 | resource-management | 1 | Resource, ResourceTag | Employee profiles, skills, designations |
| 05 | allocation-tracking | 1 | Assignment | Resource-to-project assignments with auto-release |
| 06 | non-human-costs | 2 | NonHumanCost | Software, infrastructure, and travel costs |
| 07 | utilization-dashboards | 1+2 | (none) | Company/DM/client/project/resource dashboards |
| 08 | financial-engine | 2 | (none) | Cost, revenue, and margin calculations |
| 09 | invoicing | 2 | Milestone, Invoice | Milestone tracking and invoice lifecycle |
| 10 | bench-forecasting | 2 | (none) | Bench tracking and availability projections |
| 11 | worklog | 1 | Worklog | Daily hour logging per project |
| 12 | alerts | 3 | Alert, SystemConfig | Proactive alerts and system configuration |
| 13 | audit-history | 1+3 | AuditLog | Append-only audit trail with point-in-time reconstruction |

## User Roles

| Role | Level | Primary Responsibility |
|---|---|---|
| CEO | 100 | Full visibility, strategic decisions |
| CTO | 90 | Technical oversight, resource costs, utilization |
| Delivery Manager (DM) | 70 | Portfolio management, resource allocation |
| Project Manager (PM) | 60 | Project execution, assignments, worklogs |
| Finance | 70 | Billing, invoicing, cost tracking |
| HR | 50 | Resource onboarding, bench tracking |
| Engineer | 10 | Own profile, assignments, worklogs |

## How to Build

1. **Decide the tech stack** — Update the Tech Stack section in `CLAUDE.md`
2. **Read `CLAUDE.md`** — Master instructions for the entire build process
3. **Build modules in order** — Follow the phase and build order in `ROADMAP.md`
4. **For each module:** Read its REQUIREMENTS.md, SCHEMA.md, API.md, SCREENS.md, and DEPENDENCIES.md before writing any code

### Using Claude Code

```bash
cd project/
claude "Build module 01-auth-and-roles"
```

Claude Code reads `CLAUDE.md` automatically and follows the module build process defined there.

## Key Documents

| Document | Purpose | When to Read |
|---|---|---|
| `prd/PRD.md` | Business requirements | Understanding the "why" |
| `fsd/FSD.md` | Technical specifications | Understanding the "how" |
| `shared/ENTITIES.md` | All 14 entity definitions | Before building any entity |
| `shared/BUSINESS-RULES.md` | Formulas and calculations | Before any financial logic |
| `shared/ACCESS-MATRIX.md` | Who sees what | Before any API endpoint |
| `CLAUDE.md` | Build instructions | Before starting any module |
| `ROADMAP.md` | Build plan and estimates | Planning and sequencing |

## Tech Stack

> **Not yet decided.** See `CLAUDE.md` for recommendations. Update both files once the team finalizes the stack.
