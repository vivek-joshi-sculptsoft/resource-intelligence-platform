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
Before I create tickets in Jira, I need 5 quick preferences:

1. EPIC GROUPING — How should I group work into Epics?
   a) One epic per module [RECOMMENDED — best traceability, e.g. "Client Management", "Allocation Tracking"]
   b) One epic per phase [Good for smaller projects, e.g. "Phase 1 — Core", "Phase 2 — Features"]
   c) One epic per feature area [Good for cross-cutting work, e.g. "Auth & Security", "Financial Engine"]
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
```

After getting answers, confirm the setup before proceeding:
```
Got it. Creating tickets with:
- Epics: {grouping choice}
- Story size: {granularity choice}
- Team: {team structure}
- Technical tasks: {split pattern}
- Sprints: {sprint setup}

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
PROJ-4  [Epic] Resource Management
PROJ-5  [Epic] Allocation Tracking
PROJ-6  [Epic] Financial Engine
...
```

- Epic description = module description from REQUIREMENTS.md
- Epic label = `phase-N` for which phase the module belongs to
- Stories link to their module's epic

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

Use the format: `[Action] [Subject] — [scope qualifier]`

```
Implement Assignment CRUD — REST API with validations and access control
Build Allocation List View — sortable, filterable table with pagination
Set up Auth Middleware — JWT validation and role-based route protection
```

Avoid vague titles like "Work on assignments" or "Assignment stuff."

### Story Body Template (Jira Description)

```
h2. As a {role}, I want to {capability} so that {benefit}.

h3. Acceptance Criteria
* {criterion 1}
* {criterion 2}
* {criterion 3}

h3. Out of Scope
* {what this story does NOT include — prevents scope creep}

h3. Technical Notes
* FSD Reference: §{section}
* Related entities: {list}
* Dependencies: {story titles this depends on}
```

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

```
h3. Scope
{what this task covers — be specific}

h3. Definition of Done
* {criterion 1}
* {criterion 2}

h3. Notes
* Linked story: {parent story title}
* FSD section: §{section}
```

---

## Jira MCP Creation Sequence

### Phase 1: Create Epics + Stories

```
For each module (or grouping):
  1. Create Epic
     - summary: {module name}
     - description: {module description}
     - labels: [phase-N, module-name]
     - priority: based on module priority

  2. For each story in the module:
     a. Create Story
        - summary: {story title}
        - description: {story body with AC}
        - epic_link: {epic key from step 1}
        - priority: P0-P4 mapped to Blocker/Critical/Major/Minor/Trivial
        - story_points: 1/2/3/5/8
        - labels: [backend/frontend/database, phase-N, must-have/nice-to-have]
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
