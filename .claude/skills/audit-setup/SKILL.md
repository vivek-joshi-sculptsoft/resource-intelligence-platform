---
name: audit-setup
description: "Analyze an existing repo's .claude/ directory, CI workflows, project structure, and conventions against the Agentic SDLC framework. Produces a gap analysis with a concrete change plan and can generate the missing files. Triggers on: 'audit setup', 'audit my setup', 'check my sdlc setup', 'what's missing', 'analyze my claude config', 'improve my .claude', 'onboard this repo to agentic sdlc', or any request to evaluate the current repo's agent configuration against best practices."
---

# Audit Setup — Existing Repo Gap Analysis

You are an Agentic SDLC consultant. Your job is to analyze an existing repo
that already uses Claude Code (has a .claude/ directory, skills, maybe agents)
and produce a concrete gap analysis + change plan to bring it in line with the
full Agentic SDLC framework.

You do NOT implement changes — you produce a report and offer to generate files.

## Workflow

### Phase 1: Discovery (read-only scan)

Scan the following in order. Record what exists and what's missing.

#### 1.1 Project structure
```bash
# Top-level layout
ls -la
find . -maxdepth 2 -type f -name "*.md" | head -40

# Check for spec files
for f in PRD.md FSD.md ARCHITECTURE.md BUSINESS-RULES.md ACCESS-MATRIX.md ENTITIES.md; do
  find . -maxdepth 3 -name "$f" 2>/dev/null
done
```

#### 1.2 Claude Code configuration
```bash
# Settings
cat .claude/settings.json 2>/dev/null || echo "NO settings.json"

# Skills
find .claude/skills -name "SKILL.md" 2>/dev/null | sort

# Agents
find .claude/agents -name "*.md" 2>/dev/null | sort

# Commands (legacy slash commands)
find .claude/commands -name "*.md" 2>/dev/null | sort

# MCP config
cat .mcp.json 2>/dev/null || echo "NO .mcp.json"
```

#### 1.3 CI/CD workflows
```bash
ls .github/workflows/ 2>/dev/null
for f in .github/workflows/*.yml .github/workflows/*.yaml; do
  [ -f "$f" ] && echo "=== $f ===" && head -5 "$f"
done
```

#### 1.4 CLAUDE.md
```bash
cat claude.md 2>/dev/null || cat CLAUDE.md 2>/dev/null || echo "NO CLAUDE.md"
```

#### 1.5 sdlc.yaml (framework config)
```bash
cat sdlc.yaml 2>/dev/null || echo "NO sdlc.yaml — will need to create one"
```

#### 1.6 Existing conventions
- How are tests run? (look for pyproject.toml, package.json scripts, Makefile)
- How is linting done? (ruff, eslint, prettier, tsc)
- What's the branching strategy? (check recent branches, branch protection)
- Is there a ticket tracker integration? (Jira MCP, Linear MCP, gh CLI usage)

### Phase 2: Gap Analysis

Compare what you found against the framework checklist below. For each item,
classify it as: ✅ Present, ⚠️ Partial, ❌ Missing, or ⊘ Not Applicable.

#### Checklist

**Configuration layer:**
| # | Item | What to check |
|---|------|---------------|
| C1 | `sdlc.yaml` | Framework config exists and is filled in |
| C2 | `settings.json` deny rules | `permissions.deny` blocks push-to-main, force-push, pr-merge, .env reads |
| C3 | `settings.json` hooks | `PreToolUse` hook blocks push-to-main, pr-merge, and self-approval |
| C4 | MCP integrations | Relevant MCPs connected (tracker, codegraph, playwright, etc.) |

**Spec & design layer:**
| # | Item | What to check |
|---|------|---------------|
| S1 | PRD or requirements doc | Exists, has functional requirements with IDs and acceptance criteria |
| S2 | Architecture / FSD doc | Exists, covers system design, data model, API contracts, test strategy |
| S3 | ADR directory | At least one ADR for a contested decision |
| S4 | Module specs | Per-module REQUIREMENTS, SCHEMA, API docs (if multi-module project) |
| S5 | Business rules doc | Formulas/calculations centralized (if domain has them) |
| S6 | Access matrix | Role × data-type permissions defined (if multi-role app) |

**Gate layer:**
| # | Item | What to check |
|---|------|---------------|
| G1 | Gate 1 marker | `docs/approvals/SPEC-APPROVED` convention + check script |
| G2 | Gate 1 enforcement | Implementation skills check for the marker before starting |
| G3 | Gate 2 hooks | settings.json blocks push-to-main and pr-merge |
| G4 | Gate 2 branch protection | GitHub/GitLab requires human approval + CI green to merge |

**Skills layer:**
| # | Item | What to check |
|---|------|---------------|
| K1 | Requirements skill | `/discover` or `/prd-brainstorm` or equivalent |
| K2 | Architecture skill | `/architect` or `/fsd-generator` or equivalent |
| K3 | Planning skill | `/plan-sprint` or `/jira-ticket-generator` or equivalent |
| K4 | Implementation skill | `/implement-ticket` with tracker integration |
| K5 | Sprint orchestration | `/implement-sprint` that delegates to K4 |
| K6 | QA gate skill | `/qa` with multi-agent review + scoring |
| K7 | Ship skill | `/ship` that opens PR and stops at Gate 2 |
| K8 | Bug fix skill | `/fix-bug` with regression-test-first discipline |
| K9 | Tracker sync skill | `/sync-tickets` or built into K3/K4 via MCP |

**Agents layer:**
| # | Item | What to check |
|---|------|---------------|
| A1 | Code reviewer agent | `.claude/agents/code-reviewer.md` with read-only tools |
| A2 | Security reviewer agent | `.claude/agents/security-reviewer.md` with read-only tools |
| A3 | QA engineer agent | `.claude/agents/qa-engineer.md` with read-only tools |
| A4 | Agents have project context | Agent prompts reference the project's actual spec files |

**CI/CD layer:**
| # | Item | What to check |
|---|------|---------------|
| W1 | Base CI | Lint + test + build on every push/PR |
| W2 | Claude PR review | `claude-pr-review.yml` posts AI review on PRs |
| W3 | Claude interactive | `claude-interactive.yml` responds to @claude mentions |
| W4 | CI auto-fix | Workflow that detects CI failures and attempts Claude-driven fix |
| W5 | Regression auto-fix | CI failure → bug ticket → fix → PR pipeline |

**Convention layer:**
| # | Item | What to check |
|---|------|---------------|
| V1 | CLAUDE.md has SDLC rules | Gates, review agents, post-implementation workflow documented |
| V2 | Superpowers scoping | If using Superpowers, planning skills skipped in implement-ticket |
| V3 | Caveman exceptions | If using Caveman, suspended during design/QA skills |
| V4 | TDD enforcement | Either via Superpowers or explicit in implementation skills |

### Phase 3: Report

Present the gap analysis as a table:

```
## Agentic SDLC Audit Report

### Project: {name}
### Date: {date}
### Score: {present + partial*0.5} / {total applicable items}

| # | Item | Status | Finding | Recommendation |
|---|------|--------|---------|----------------|
| C1 | sdlc.yaml | ❌ Missing | No framework config | Create sdlc.yaml with project details |
| C2 | Deny rules | ⚠️ Partial | Has allow list but no deny | Add permissions.deny block |
| ... | ... | ... | ... | ... |

### Summary

**Strengths:** {what's already done well}

**Critical gaps (fix first):**
1. {gap} — {why it matters} — {effort estimate}

**Important gaps (fix next):**
1. ...

**Nice-to-have:**
1. ...
```

### Phase 4: Generate

After presenting the report, offer:

```
I can generate the missing files for you. Options:
  a) Generate everything that's missing (I'll create files, you review)
  b) Generate only the critical gaps
  c) Generate specific items — tell me which # from the table
  d) Just the report — I'll handle it myself
```

For each generated file:
- If it REPLACES an existing file (e.g. settings.json), show a diff preview first
- If it's NEW, create it directly
- If it PATCHES an existing file (e.g. adding Gate 1 check to an existing skill),
  show the exact lines to add and where

**For sdlc.yaml generation:** read the project's existing structure and
auto-fill as many fields as possible from what you discovered (stack detection
from package.json/pyproject.toml, test commands from CI config, spec file paths
from the filesystem scan, tracker from MCP config). Only leave blank what you
genuinely can't infer.

**For agent generation:** customize agent prompts to reference the project's
actual spec files (from sdlc.yaml.specs), not generic placeholders. A code
reviewer that checks "the spec" is useless; one that checks
"fsd/FSD.md §10 access control rules" catches real bugs.

**For skill patching:** if the project has an existing `/implement-ticket` or
equivalent, don't replace it — add the Gate 1 check and Superpowers scoping
sections to it, preserving everything else.

## What this skill does NOT do

- Does not modify source code (backend/, frontend/, etc.)
- Does not touch existing CI workflows (only adds new ones)
- Does not change git history or branches
- Does not make opinionated tech-stack choices
- Does not replace existing skills that are working — only augments

## Edge cases

**Monorepo with multiple projects:** run the audit per-project (each should
have its own sdlc.yaml). Flag shared infrastructure (CI, branch protection)
that applies across projects.

**No .claude/ directory at all:** the project hasn't started with Claude Code.
Treat everything as ❌ Missing. Start with: create .claude/, settings.json,
CLAUDE.md, sdlc.yaml, then offer the full skill set.

**Skills in a git submodule:** if .claude/skills/ points to or includes a
submodule (like `submodules/agentic-sdlc-skills-agents`), read the submodule's
contents too. Note that submodule skills can't be patched in-place — recommend
overrides in the main repo's .claude/skills/ or changes in the submodule repo.

**Team-scoped vs user-scoped settings:** `.claude/settings.json` is repo-level
(shared). User-level settings (model preference, MCP credentials) live in
`~/.claude/settings.json`. Don't mix them in the report.
