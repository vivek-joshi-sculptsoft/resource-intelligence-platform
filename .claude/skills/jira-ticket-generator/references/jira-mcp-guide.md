# Jira MCP Integration Guide

## Overview

When Jira MCP tools are available, the skill creates tickets directly in Jira instead of (or in addition to) generating files. The workflow is always two-phase:

1. **Phase 1 (always)** — Create Epics + User Stories
2. **Phase 2 (on demand)** — Create Technical Sub-tasks under those stories

Do not skip the preference questionnaire. It takes 2 minutes and prevents a week of wrong structure.

---

## Detecting Jira MCP

The skill uses the official Atlassian Remote MCP (see SETUP.md for connection steps). At the start of execution, check if Atlassian MCP tools are available by looking for tools with `atlassian` or `jira` in their name.

If found → offer MCP creation. If not found → fall back to file output only.

---

## Preference Questionnaire

Ask ALL of these before creating anything. Present as a numbered list the user can answer at once.

```
Before I create tickets in Jira, I need a few quick preferences:

1. EPIC GROUPING — How should I group work into Epics?
   a) One epic per module [RECOMMENDED — best traceability]
   b) One epic per phase [Good for smaller projects]
   c) One epic per feature area [Good for cross-cutting work]
   d) Custom — tell me your grouping preference

2. STORY GRANULARITY — What size should most stories be?
   a) Small (1-2 days, tight scope) [Best for experienced teams with clear specs]
   b) Medium (2-3 days, full feature slice) [RECOMMENDED — balances detail with agility]
   c) Large (3-5 days, cross-cutting) [Good when team members own full features end-to-end]

3. TEAM STRUCTURE — How is your dev team organized?
   a) Full-stack — one dev per feature [RECOMMENDED for most startups]
   b) FE/BE split — separate frontend and backend devs
   c) 3-track — separate backend, frontend, and QA

4. TECHNICAL TASKS — When you ask me to break stories into tasks, how should I split them?
   a) Full-stack task per story [Best for full-stack teams]
   b) Backend + Frontend task per story [RECOMMENDED for FE/BE split teams]
   c) Backend + Frontend + QA task per story [Best for teams with dedicated QA]
   d) Only for L and XL stories — keep S and M as-is

5. SPRINT SETUP — What is your sprint length and team velocity?
   a) 1-week sprints, ~15 pts per dev
   b) 2-week sprints, ~20 pts per dev [RECOMMENDED]
   c) 2-week sprints, ~25 pts per dev
   d) Custom — tell me sprint length and velocity

6. DESCRIPTION FORMAT — What format does your Jira project use?
   a) Markdown [RECOMMENDED — used by team-managed / next-gen projects]
   b) Jira wiki markup [Used by company-managed / classic projects]

7. NAMING CONVENTION — How should I name epics and stories?
   a) Plain titles [RECOMMENDED — e.g. "Auth & Roles", "Implement login flow"]
   b) Numbered — sprint-prefixed stories, numbered epics [e.g. "EP-1: Auth & Roles", "S1-01: Implement login flow"]
   c) Custom — tell me your naming pattern

8. CUSTOM LABELS — Any project-specific labels to add to all tickets?
   a) None — use only standard labels (backend, frontend, phase-N, etc.)
   b) Yes — tell me the labels [e.g. "agentic", "team-alpha", "mvp"]
```

After getting answers, confirm the setup before proceeding:
```
Got it. Creating tickets with:
- Epics: {grouping choice}
- Story size: {granularity choice}
- Team: {team structure}
- Technical tasks: {split pattern}
- Sprints: {sprint setup}
- Description format: {markdown or wiki}
- Naming: {naming choice}
- Custom labels: {labels or none}

Shall I proceed?
```

---

## Epic Distribution Standards

### Option A: One Epic per Module (Recommended)

Best for: medium-to-large projects (5+ modules), teams that work module-by-module, projects where multiple devs own separate modules.

```
PROJ-1  [Epic] Auth & Roles
PROJ-2  [Epic] Client Management
PROJ-3  [Epic] Project Management
...
```

- Epic description = module summary from REQUIREMENTS.md + metadata block (see below)
- Epic label = `phase-N` for which phase the module belongs to
- Stories link to their module's epic

### Epic Description Template

Every epic description should include a summary paragraph followed by a metadata block. This gives PMs and developers a quick snapshot without opening individual stories.

```
{1-2 sentence module summary from REQUIREMENTS.md}

**Sprint:** {sprint number or range} | **Stories:** {count} | **SP:** {total story points}
**Spec refs:** {paths to module spec files}
```

Example:
```
Resource CRUD with tags, availability computation, access control, and UI (list / profile / form).

**Sprint:** 2 | **Stories:** 8 | **SP:** 19
**Spec refs:** modules/04-resource-management/, shared/ENTITIES.md
```

**Rules:**
- Summary comes from the module's REQUIREMENTS.md overview section
- Story count and SP are computed after all stories for the epic are generated
- Spec refs point to the module folder and any shared files the module heavily uses
- If using numbered naming convention (question 7b), prefix epic title: `EP-{N}: {Module Name}`

### Option B: One Epic per Phase

Best for: small projects (< 5 modules), rapid MVP builds, stakeholder reporting by phase.

```
PROJ-1  [Epic] Phase 1 — Foundation
PROJ-2  [Epic] Phase 2 — Core Features
PROJ-3  [Epic] Phase 3 — Advanced & Reporting
```

- All Phase 1 module stories → Phase 1 Epic
- Epic description = "All foundation work: {module list}"
- Risk: large epics become hard to track; consider splitting if >30 stories per epic

### Option C: One Epic per Feature Area

Best for: cross-cutting feature work, platform teams, projects where single modules span multiple phases.

```
PROJ-1  [Epic] Authentication & Security
PROJ-2  [Epic] Data Management (Clients, Projects, Resources)
PROJ-3  [Epic] Workflow Engine (Allocations, Invoicing)
PROJ-4  [Epic] Financials & Reporting
PROJ-5  [Epic] Platform & Infrastructure
```

- Group modules by functional affinity, not by module number
- Use when modules within the same phase are very different in nature

---

## Story Distribution Standards

### What Makes a Good User Story in Jira

Follow the INVEST criteria:
- **I**ndependent — can be built without waiting on another story in the same sprint
- **N**egotiable — scope can be adjusted
- **V**aluable — delivers visible value (feature, fix, or foundation for another feature)
- **E**stimable — team can size it
- **S**mall — completable in one sprint
- **T**estable — has clear acceptance criteria

### Story Title Format

Base format: `[Action] [Subject] — [scope qualifier]`

Apply the naming convention from the user's preference (question 7):

**Plain (7a — default):**
```
Implement Assignment CRUD — REST API with validations and access control
Build Allocation List View — sortable, filterable table with pagination
Set up Auth Middleware — JWT validation and role-based route protection
```

**Numbered (7b):**
```
S{sprint}-{seq}: Implement Assignment CRUD — REST API with validations and access control
S{sprint}-{seq}: Build Allocation List View — sortable, filterable table with pagination
```

Where `{sprint}` = sprint number (0-padded if >9), `{seq}` = sequence within the sprint (01, 02, ...).

Avoid vague titles like "Work on assignments" or "Assignment stuff."

### Story Body Template (Jira Description)

Use the format matching the user's description format preference (question 6).

**Markdown format (team-managed projects):**

```
## Context (read before starting)

* `{path/to/spec-file}` — {what to look for}
* `{path/to/another-file}` — {relevant section}

**As a {role}**, I want to {capability} so that {benefit}.

## Acceptance Criteria

- [ ] {criterion 1}
- [ ] {criterion 2}
- [ ] {criterion 3}

## Out of Scope

* {what this story does NOT include — prevents scope creep}

**Depends On:** {story titles this depends on}
```

**Wiki markup format (company-managed projects):**

```
h3. Context (read before starting)
* {{path/to/spec-file}} — {what to look for}
* {{path/to/another-file}} — {relevant section}

h2. As a {role}, I want to {capability} so that {benefit}.

h3. Acceptance Criteria
* {criterion 1}
* {criterion 2}
* {criterion 3}

h3. Out of Scope
* {what this story does NOT include — prevents scope creep}

*Depends On:* {story titles this depends on}
```

### Context Derivation Rules

The Context section tells a developer or AI agent exactly which files to read before starting. Derive file references based on the story's labels and content:

| Story labels / type | Files to reference |
|---|---|
| `database` (schema/migration) | `modules/{mod}/SCHEMA.md`, `shared/ENTITIES.md` |
| `backend` (API/logic) | `modules/{mod}/API.md`, `modules/{mod}/REQUIREMENTS.md` |
| `backend` (business rules/calculations) | `shared/BUSINESS-RULES.md` |
| `frontend` (UI) | `modules/{mod}/SCREENS.md`, `modules/{mod}/REQUIREMENTS.md` |
| access control story | `shared/ACCESS-MATRIX.md` |
| audit/logging story | `CLAUDE.md` → Audit Logging section |
| testing story | All relevant module files + `CLAUDE.md` → Testing section |
| scheduled job story | `modules/{mod}/JOBS.md` (if exists) |
| any story | `CLAUDE.md` → relevant conventions section |

**Rules:**
- Always include the most specific file first (module file before shared file)
- Add the relevant section or heading after `→` when pointing to a large file
- Include `CLAUDE.md` only when pointing to a specific section, not generically
- If a story touches multiple concerns (e.g., backend + frontend), include files for both
- Keep to 2-5 file references — enough for context, not a reading list

### Stories per Epic (Guidance)

| Epic type | Typical story count | Warning signal |
|---|---|---|
| CRUD entity module | 7-10 stories | > 14 = split epic |
| Workflow/lifecycle module | 8-12 stories | > 16 = split epic |
| Financial module | 6-9 stories | > 12 = split epic |
| Dashboard module | 4-7 stories | > 10 = split epic |
| Infrastructure module | 4-8 stories | > 12 = split epic |

If an epic exceeds the warning signal, split it into "{Module} — Core" and "{Module} — Advanced" epics.

---

## Technical Task Breakdown Standards

Triggered when user says: "break stories into tasks", "create technical tasks", "add sub-tasks", "distribute technical work."

### When to Add Tasks vs Not

| Story size | Action |
|---|---|
| XS | No sub-tasks. Story IS the task. |
| S | No sub-tasks for full-stack teams. One task per discipline for FE/BE teams. |
| M | Split only if FE/BE split team. Full-stack → no sub-tasks. |
| L | Always split. Minimum: Backend task + Frontend task. |
| XL | Always split. Backend + Frontend + QA/Test task. Consider further splitting the story. |

### Task Patterns by Team Structure

**Full-stack team (Option a):**
```
[Story] Assignment CRUD — L
  └── [Task] Implement Assignment CRUD end-to-end — 5 pts
      # No split needed. One dev owns it all.
```

**FE/BE split team (Option b):**
```
[Story] Assignment CRUD — L
  ├── [Task] Backend: Assignment API + validations + access control — M (3 pts)
  └── [Task] Frontend: Assignment list + detail + form views — M (3 pts)
```

**3-track team with QA (Option c):**
```
[Story] Assignment CRUD — L
  ├── [Task] Backend: Assignment API + validations + access control — M (3 pts)
  ├── [Task] Frontend: Assignment list + detail + form views — M (3 pts)
  └── [Task] QA: Test plan + automation for Assignment CRUD — S (2 pts)
```

### Task Title Format

`[Track]: [Action] [Subject] — [key scope]`

```
Backend: Implement Allocation CRUD API — 7 endpoints, state machine, audit log
Frontend: Build Allocation UI — list view, detail view, create/edit form
QA: Test Allocation module — happy path + edge cases + access control
```

### Task Description Template

Use the format matching the user's description format preference (question 6).

**Markdown format:**
```
## Context (read before starting)

* `{path/to/relevant-file}` — {what to look for}

## Scope

{what this task covers — be specific}

## Definition of Done

- [ ] {criterion 1}
- [ ] {criterion 2}

**Parent story:** {parent story title}
```

**Wiki markup format:**
```
h3. Context (read before starting)
* {{path/to/relevant-file}} — {what to look for}

h3. Scope
{what this task covers — be specific}

h3. Definition of Done
* {criterion 1}
* {criterion 2}

*Parent story:* {parent story title}
```

---

## Jira MCP Creation Sequence

### Phase 1: Create Epics + Stories

```
For each module (or grouping):
  1. Create Epic
     - summary: {epic title per naming convention preference}
     - description: {module summary + metadata block — see Epic Description Template}
     - labels: [phase-N, module-name] + {custom labels from question 8}
     - priority: based on module priority

  2. For each story in the module:
     a. Create Story
        - summary: {story title per naming convention preference}
        - description: {story body with Context + AC + Out of Scope — per format preference}
        - epic_link: {epic key from step 1}
        - priority: P0-P4 mapped to Blocker/Critical/Major/Minor/Trivial
        - story_points: 1/2/3/5/8
        - labels: [backend/frontend/database, phase-N, sprint-N, must-have/nice-to-have] + {custom labels}
        - sprint: {sprint suggestion}

  3. After all stories created, set issue links (blocks/is-blocked-by)
     - Do this AFTER all stories exist so keys are known
```

### Phase 2: Create Technical Tasks (on demand)

```
For each story where tasks are warranted (based on team structure preference):
  1. Create Sub-task(s) under the story
     - issue_type: Sub-task (or Task if project uses Tasks)
     - parent: {story key}
     - summary: {task title}
     - description: {task description}
     - assignee: (optional — ask user if they want auto-assignment)
     - story_points: subset of parent story's points
```

### Error Handling

If a create call fails:
1. Log the failure with the story title
2. Continue creating remaining tickets
3. At the end, report a summary: "X tickets created, Y failed: {list}"
4. Offer to retry failed tickets or export them as CSV for manual import

---

## Post-Creation Report

After all tickets are created, output a summary:

```
## Jira Tickets Created

### Epics ({N} total)
| Epic Key | Title | Stories |
|---|---|---|
| {KEY} | {title} | {count} |

### Stories ({N} total)
| Key | Title | Epic | Points | Sprint |
|---|---|---|---|---|
| {KEY} | {title} | {epic} | {pts} | {sprint} |

### Technical Tasks ({N} total, if Phase 2 run)
| Key | Title | Parent Story |
|---|---|---|
| {KEY} | {title} | {key} |

### Sprint Summary
| Sprint | Stories | Total Points |
|---|---|---|
| Sprint 1 | {N} | {pts} |

### Failed Tickets
{list if any, or "None"}
```
