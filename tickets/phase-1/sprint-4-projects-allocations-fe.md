# Sprint 4 — Projects & Allocations Frontend

**Goal:** Full project UI with detail tabs. Assignment management from project detail. Resource profile shows assignments. App shell with sidebar navigation.
**Capacity:** 32 SP | **Duration:** 1 week
**Epics:** EP-4 (Project Management — frontend) + EP-5 (Allocation Tracking — frontend) + EP-0 (IaC)

---

## EP-4: Project Management — Frontend (13 SP)

### S4-01: App shell — sidebar navigation and layout
**Type:** Story | **Points:** 3 (M) | **Priority:** P0 — Blocker
**Labels:** `frontend`, `phase-1`, `must-have`, `agentic`
**Depends On:** S1-06

#### Context (read before starting)
- `techstack/frontend.md` → Layout, routing structure
- `shared/ACCESS-MATRIX.md` → what each role can see
- All SCREENS.md files → navigation items needed

#### Description
As a user, I want a persistent sidebar so that I can navigate between modules.

#### Acceptance Criteria
- [ ] Sidebar component with nav items: Dashboard (placeholder), Resources, Clients, Projects, Admin (Users, Roles)
- [ ] Role-based visibility: Engineer sees only Resources (own), Dashboard; no Clients/Projects/Admin
- [ ] HR sees Resources, Clients, Projects but no Admin
- [ ] CEO/CTO sees all including Admin section
- [ ] Active route highlighted in sidebar
- [ ] Collapsible sidebar (toggle button)
- [ ] Top bar: user name, role badge, logout button
- [ ] Responsive: sidebar collapses to icon-only on small screens
- [ ] Root layout wraps all authenticated routes with sidebar + top bar
- [ ] `/` redirects to `/dashboard` (placeholder page for now)

---

### S4-02: Project List screen UI
**Type:** Story | **Points:** 2 (S) | **Priority:** P1 — Critical
**Labels:** `frontend`, `phase-1`, `must-have`, `agentic`
**Depends On:** S3-02, S4-01

#### Context (read before starting)
- `modules/03-project-management/SCREENS.md` → Project List spec

#### Description
As a manager, I want a project list page so that I can see and filter all projects.

#### Acceptance Criteria
- [ ] `/projects` route — full-width data table
- [ ] Columns: Name (link), Client, Type badge (FP/T&M/Onboarding), Status badge (colored), DM, PM, Start Date, Contract End
- [ ] Contract End Date highlighted amber if expiring within 30 days
- [ ] Filter bar: status dropdown, type dropdown, client dropdown, DM dropdown
- [ ] Search input by project name
- [ ] Column sorting
- [ ] Pagination
- [ ] "Add Project" button — CEO, CTO, DM only
- [ ] Click row → `/projects/:id`
- [ ] Empty state: "No projects found. Try adjusting your filters or create a new project."
- [ ] DM/PM see only their portfolio (API enforces)

---

### S4-03: Project Detail screen with tabs
**Type:** Story | **Points:** 3 (M) | **Priority:** P1 — Critical
**Labels:** `frontend`, `phase-1`, `must-have`, `agentic`
**Depends On:** S3-02, S3-03, S4-02

#### Context (read before starting)
- `modules/03-project-management/SCREENS.md` → Project Detail spec
- `modules/05-allocation-tracking/SCREENS.md` → Assignment List (tab content)

#### Description
As a manager, I want a project detail page with tabs so that I see all project information in one place.

#### Acceptance Criteria
- [ ] `/projects/:id` route — header + tab navigation
- [ ] Header: name, client (link to `/clients/:id`), type badge, status badge, billing currency, DM name, PM name, start date, contract end date
- [ ] Status transition buttons: "Complete", "Put on Hold", "Cancel" — based on current status and valid transitions
- [ ] Transition buttons visible only to CEO/CTO/DM
- [ ] Confirmation dialog before status transition
- [ ] After transition: refetch project, show success toast
- [ ] Tab navigation: Assignments | Worklogs (if enabled, placeholder) | Financials (Phase 2, placeholder)
- [ ] Assignments tab is default active tab
- [ ] Edit button → `/projects/:id/edit` (CEO/CTO/DM/PM)
- [ ] `contract_value` hidden (Phase 2)

---

### S4-04: Project Create/Edit form UI
**Type:** Story | **Points:** 3 (M) | **Priority:** P1 — Critical
**Labels:** `frontend`, `phase-1`, `must-have`, `agentic`
**Depends On:** S3-02, S4-02

#### Context (read before starting)
- `modules/03-project-management/SCREENS.md` → Project Create/Edit Form spec

#### Description
As a CEO/CTO/DM, I want a project form so that I can create and edit projects.

#### Acceptance Criteria
- [ ] `/projects/new` and `/projects/:id/edit` routes
- [ ] Fields: Name (required), Client dropdown (required, active clients), Type radio (required: FP/T&M/Onboarding), Billing Currency dropdown (default INR), Start Date picker, Contract End Date picker, DM dropdown (required, active resources), PM dropdown (required, active resources), Worklog Enabled toggle, Notes textarea
- [ ] Conditional: Contract End Date required when type is T&M or CLIENT_ONBOARDING — show validation message
- [ ] DM creating: dm_id pre-filled with self, field disabled
- [ ] CEO/CTO creating: dm_id is open dropdown
- [ ] Edit form pre-populates all fields
- [ ] Client-side validations match server rules
- [ ] Save → redirect to project detail with success toast
- [ ] Cancel → back to project list
- [ ] Auth: CEO, CTO, DM for create; CEO, CTO, DM, PM (limited) for edit

---

### S4-05: Project frontend integration tests
**Type:** Story | **Points:** 2 (S) | **Priority:** P2 — Major
**Labels:** `testing`, `frontend`, `phase-1`, `nice-to-have`, `agentic`
**Depends On:** S4-02 through S4-04

#### Context (read before starting)
- `techstack/frontend.md` → Testing stack (Vitest)

#### Description
As a developer, I want frontend component tests for project screens so that UI logic is verified.

#### Acceptance Criteria
- [ ] Project list: renders columns, filters work, pagination works
- [ ] Project detail: renders header, tabs switch, status buttons show/hide per role
- [ ] Project form: required field validation, conditional contract_end_date, DM pre-fill for DM role
- [ ] Status transition: confirmation dialog appears, API called on confirm
- [ ] Empty states render correctly

---

## EP-5: Allocation Tracking — Frontend (14 SP)

### S4-06: Assignment List UI (within Project Detail)
**Type:** Story | **Points:** 3 (M) | **Priority:** P0 — Blocker
**Labels:** `frontend`, `phase-1`, `must-have`, `agentic`
**Depends On:** S3-07, S4-03

#### Context (read before starting)
- `modules/05-allocation-tracking/SCREENS.md` → Assignment List spec
- `shared/ACCESS-MATRIX.md` → field restrictions

#### Description
As a PM/DM, I want an assignments table within the project detail so that I can see who is allocated.

#### Acceptance Criteria
- [ ] Assignments tab content: data table
- [ ] Columns: Resource Name (link to `/resources/:id`), Effective Designation, Effective Expertise, Allocation %, Billability %, Shadow badge, Start Date, End Date ("Ongoing" if null), Status badge
- [ ] Status filter: Active / Released / All
- [ ] "Add Assignment" button — CEO, CTO, DM, PM
- [ ] Release button on each active row — confirmation dialog → POST /release
- [ ] Over-allocation banner: shown when any resource in the list has total allocation > 100%
- [ ] `billability_pct`, `is_shadow` hidden for HR/Engineer roles (show "—")
- [ ] `billing_rate` column hidden (Phase 2)
- [ ] Click row → opens edit form
- [ ] Empty state: "No assignments yet. Add a resource to this project."

---

### S4-07: Assignment Create/Edit form (modal)
**Type:** Story | **Points:** 3 (M) | **Priority:** P0 — Blocker
**Labels:** `frontend`, `phase-1`, `must-have`, `agentic`
**Depends On:** S3-07, S4-06

#### Context (read before starting)
- `modules/05-allocation-tracking/SCREENS.md` → Assignment Create/Edit Form spec

#### Description
As a PM/DM, I want an assignment form so that I can assign resources to projects with proper validation.

#### Acceptance Criteria
- [ ] Modal/slide-over form triggered from "Add Assignment" or row click
- [ ] Resource dropdown (required): active resources, shows current total allocation % next to each name
- [ ] Allocation % input (required, 1–100)
- [ ] Billability % input (required, 0–100)
- [ ] Shadow toggle: when ON, billability auto-sets to 0 and input becomes disabled
- [ ] Project Designation override (optional text input)
- [ ] Project Expertise override (optional text input)
- [ ] Start Date picker (required)
- [ ] End Date picker (optional, label shows "Leave blank for ongoing")
- [ ] **Client-side validation messages (match server):**
  - "Allocation must be between 1% and 100%"
  - "Billability cannot exceed allocation percentage"
  - "Shadow resources cannot have billability"
  - "End date must be after start date"
- [ ] Over-allocation warning: non-blocking amber banner "This will bring {resource}'s total allocation to {X}%"
- [ ] Duplicate active assignment: error from server displayed
- [ ] Save → refetch assignment list, close modal, success toast
- [ ] Cancel → close modal

---

### S4-08: Resource Profile — Assignments panel update
**Type:** Story | **Points:** 2 (S) | **Priority:** P1 — Critical
**Labels:** `frontend`, `phase-1`, `must-have`, `agentic`
**Depends On:** S3-07, S2-06

#### Context (read before starting)
- `modules/05-allocation-tracking/SCREENS.md` → Resource Assignments Panel spec
- `modules/04-resource-management/SCREENS.md` → Resource Profile (Assignments section)

#### Description
As a user, I want the resource profile to show actual assignment data (not just placeholder) now that the API exists.

#### Acceptance Criteria
- [ ] `/resources/:id` — Active Assignments tab: calls `GET /api/v1/resources/:resourceId/assignments?status=ACTIVE`
- [ ] Table: Project Name (link), Effective Designation, Allocation %, Billability %, Shadow badge, Start Date, End Date
- [ ] Total allocation % in stats row: live computed from active assignments
- [ ] Allocation > 100% highlighted red
- [ ] Assignment History tab: calls `GET /api/v1/resources/:resourceId/assignments?status=RELEASED,AUTO_RELEASED`
- [ ] History table adds: Released At, Status badge (Released / Auto-Released)
- [ ] `billability_pct`, `is_shadow` hidden for HR/Engineer
- [ ] Empty state: "No active assignments. This resource is currently on bench."
- [ ] Read-only from resource profile (edits done from project detail)

---

### S4-09: Shared UI components — status badges, role guards, data table
**Type:** Story | **Points:** 2 (S) | **Priority:** P1 — Critical
**Labels:** `frontend`, `phase-1`, `must-have`, `agentic`
**Depends On:** S1-06

#### Context (read before starting)
- `techstack/frontend.md` → Shared components approach

#### Description
As a developer, I want reusable shared components so that all modules have consistent UI patterns.

#### Acceptance Criteria
- [ ] `StatusBadge` component: accepts status string, returns colored badge (green=ACTIVE, gray=INACTIVE, blue=COMPLETED, red=CANCELLED, amber=ON_HOLD, etc.)
- [ ] `TypeBadge` component: project type badges (FP, T&M, Onboarding)
- [ ] `RoleGuard` component: wraps children, renders null if user lacks required role/access_level
- [ ] `DataTable` component: wraps shadcn Table with column sorting, pagination, loading state, empty state
- [ ] `ConfirmDialog` component: wraps shadcn AlertDialog with title, message, confirm/cancel
- [ ] `CurrencyDisplay` component: formats numbers as INR (or other currency) with appropriate precision
- [ ] All components use shadcn/ui primitives + Tailwind

---

### S4-10: Allocation frontend tests
**Type:** Story | **Points:** 2 (S) | **Priority:** P2 — Major
**Labels:** `testing`, `frontend`, `phase-1`, `nice-to-have`, `agentic`
**Depends On:** S4-06, S4-07

#### Context (read before starting)
- `techstack/frontend.md` → Testing stack

#### Description
As a developer, I want allocation UI tests so that form validation and field restrictions are verified.

#### Acceptance Criteria
- [ ] Assignment form: shadow toggle disables billability, client-side validations fire
- [ ] Over-allocation warning appears at > 100%
- [ ] Release confirmation dialog renders and triggers API call
- [ ] Field masking: billability/shadow hidden for HR role
- [ ] Resource profile: assignment table renders, history tab works
- [ ] Empty states render correctly

---

### S4-11: Navigation breadcrumbs and page titles
**Type:** Story | **Points:** 2 (S) | **Priority:** P2 — Major
**Labels:** `frontend`, `phase-1`, `nice-to-have`, `agentic`
**Depends On:** S4-01

#### Context (read before starting)
- All SCREENS.md files → breadcrumb patterns

#### Description
As a user, I want breadcrumbs and document titles so that I always know where I am.

#### Acceptance Criteria
- [ ] Breadcrumb component at top of each page: Home > Module > Entity Name
- [ ] Examples: Home > Projects > Project Phoenix; Home > Resources > Vivek Sharma > Edit
- [ ] Document title updates: "Project Phoenix — Resource Intelligence Platform"
- [ ] Back navigation via breadcrumb links
- [ ] Breadcrumb data loaded from route params + API responses

---

### S4-12: Infrastructure as Code (Terraform) — AWS provisioning
**Type:** Story | **Points:** 5 (L) | **Priority:** P2 — Major
**Labels:** `infra`, `iac`, `phase-1`, `nice-to-have`, `agentic`
**Depends On:** None (can be worked in parallel)
**JIRA:** VRIP-79

#### Context (read before starting)
- `techstack/infra.md` → Target AWS architecture
- `techstack/cost-estimate.md` → ~$36/mo budget target
- `docker-compose.dev.yml` → Services to replicate in production

#### Description
As a developer, I want Terraform configs so that production AWS infrastructure is provisioned repeatably.

#### Acceptance Criteria
- [ ] `infra/` directory with Terraform modules: VPC, EC2, RDS, S3, CloudFront, security groups, IAM
- [ ] VPC: public + private subnets in ap-south-1
- [ ] EC2: t3.small for Docker Compose (API + Celery + Redis)
- [ ] RDS: db.t4g.micro PostgreSQL 16, private subnet, automated backups
- [ ] S3 + CloudFront: static frontend hosting with CDN
- [ ] Security groups: API (80/443), DB (5432 from EC2 only), Redis (6379 internal only)
- [ ] IAM roles for EC2 → RDS, EC2 → S3 access
- [ ] Separate tfvars for dev/staging/prod environments
- [ ] Remote state: S3 backend + DynamoDB locking table
- [ ] `terraform init && terraform plan` runs without errors
- [ ] `terraform destroy` cleans up all resources
- [ ] README with first-time deploy instructions
- [ ] Estimated cost validates against ~$36/mo target

---

## Sprint 4 Summary

| Story | Title | SP | Epic | Labels | Priority |
|-------|-------|---|------|--------|----------|
| S4-01 | App shell + sidebar nav | 3 | EP-4 | frontend | P0 |
| S4-02 | Project List UI | 2 | EP-4 | frontend | P1 |
| S4-03 | Project Detail + tabs | 3 | EP-4 | frontend | P1 |
| S4-04 | Project Create/Edit form | 3 | EP-4 | frontend | P1 |
| S4-05 | Project frontend tests | 2 | EP-4 | testing | P2 |
| S4-06 | Assignment List UI | 3 | EP-5 | frontend | P0 |
| S4-07 | Assignment Create/Edit form | 3 | EP-5 | frontend | P0 |
| S4-08 | Resource Profile assignments | 2 | EP-5 | frontend | P1 |
| S4-09 | Shared UI components | 2 | EP-5 | frontend | P1 |
| S4-10 | Allocation frontend tests | 2 | EP-5 | testing | P2 |
| S4-11 | Breadcrumbs + page titles | 2 | — | frontend | P2 |
| S4-12 | Terraform IaC — AWS provisioning | 5 | EP-0 | infra | P2 |
| **Total** | | **32** | | | |
