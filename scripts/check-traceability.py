#!/usr/bin/env python3
"""
Traceability checker — compares changed files in a PR against the dependency
map in shared/TRACEABILITY.yaml and reports potentially stale documents.

Usage:
  python scripts/check-traceability.py [--base main] [--format github|text]

Reads changed files from `git diff --name-only <base>...HEAD`.
Outputs a report of dependents that may need updating.

Exit codes:
  0 — no warnings (or only non-doc files changed)
  1 — stale-doc warnings found (non-blocking by default)
"""

import argparse
import fnmatch
import subprocess
import sys
from collections import defaultdict
from pathlib import Path

try:
    import yaml
except ImportError:
    print("PyYAML not installed. Install with: pip install pyyaml", file=sys.stderr)
    sys.exit(2)

REPO_ROOT = Path(__file__).resolve().parent.parent
TRACEABILITY_PATH = REPO_ROOT / "shared" / "TRACEABILITY.yaml"


def load_traceability():
    with open(TRACEABILITY_PATH) as f:
        data = yaml.safe_load(f)
    return data.get("dependencies", [])


def get_changed_files(base_branch):
    result = subprocess.run(
        ["git", "diff", "--name-only", f"{base_branch}...HEAD"],
        capture_output=True, text=True, cwd=REPO_ROOT,
    )
    if result.returncode != 0:
        result = subprocess.run(
            ["git", "diff", "--name-only", base_branch],
            capture_output=True, text=True, cwd=REPO_ROOT,
        )
    return [f.strip() for f in result.stdout.strip().split("\n") if f.strip()]


def expand_glob(pattern):
    """Expand glob patterns relative to repo root. Returns matching file paths."""
    if "*" in pattern:
        return [str(p.relative_to(REPO_ROOT)) for p in REPO_ROOT.glob(pattern)]
    return [pattern] if (REPO_ROOT / pattern).exists() else []


def match_file_to_pattern(filepath, pattern):
    """Check if a filepath matches a pattern (supports globs)."""
    if "*" in pattern:
        return fnmatch.fnmatch(filepath, pattern)
    return filepath == pattern


def find_module_from_path(filepath):
    """Extract module directory from a file path like modules/05-allocation-tracking/SCHEMA.md."""
    parts = Path(filepath).parts
    if len(parts) >= 2 and parts[0] == "modules":
        return parts[1]
    return None


def resolve_glob_for_changed_file(pattern, changed_file):
    """When source is a glob like modules/*/SCHEMA.md and the changed file matches,
    resolve dependent globs to the same module where possible."""
    if "*" not in pattern:
        return None

    module = find_module_from_path(changed_file)
    if not module:
        return None
    return module


def build_warnings(changed_files, dependencies):
    """Walk the dependency graph and collect warnings."""
    warnings = []
    changed_set = set(changed_files)

    for dep in dependencies:
        source_pattern = dep["source"]
        matching_changed = [f for f in changed_files if match_file_to_pattern(f, source_pattern)]

        if not matching_changed:
            continue

        for changed_file in matching_changed:
            source_module = find_module_from_path(changed_file)

            for dependent in dep.get("dependents", []):
                dep_pattern = dependent["path"]
                why = dependent.get("why", "")

                dep_files = expand_glob(dep_pattern)

                if source_module and "*" in dep_pattern:
                    same_module_files = [
                        f for f in dep_files
                        if find_module_from_path(f) == source_module
                    ]
                    if same_module_files:
                        dep_files = same_module_files

                for dep_file in dep_files:
                    if dep_file in changed_set:
                        continue

                    ticket_match = dep_pattern == "tickets/*.md" and source_module
                    if ticket_match:
                        expected_ticket = f"tickets/{source_module}.md"
                        if dep_file != expected_ticket:
                            continue

                    warnings.append({
                        "source": changed_file,
                        "dependent": dep_file,
                        "why": why,
                    })

    seen = set()
    unique_warnings = []
    for w in warnings:
        key = (w["source"], w["dependent"])
        if key not in seen:
            seen.add(key)
            unique_warnings.append(w)

    return unique_warnings


def format_github(warnings):
    """Format as a GitHub PR comment body."""
    lines = []
    lines.append("## :mag: Traceability Check — Potentially Stale Documents")
    lines.append("")
    lines.append("The following documents may need updating based on what changed in this PR.")
    lines.append("This is a **warning, not a blocker** — review each and update if needed, or add a comment explaining why no change is required.")
    lines.append("")

    by_source = defaultdict(list)
    for w in warnings:
        by_source[w["source"]].append(w)

    for source, deps in sorted(by_source.items()):
        lines.append(f"### Changed: `{source}`")
        lines.append("")
        lines.append("| Potentially Stale Document | Why |")
        lines.append("|---|---|")
        for d in sorted(deps, key=lambda x: x["dependent"]):
            lines.append(f"| `{d['dependent']}` | {d['why']} |")
        lines.append("")

    lines.append("---")
    lines.append("*Generated by traceability check from `shared/TRACEABILITY.yaml`*")
    return "\n".join(lines)


def format_text(warnings):
    """Format as plain text for local use."""
    if not warnings:
        return "No stale document warnings."

    lines = []
    lines.append("TRACEABILITY CHECK — Potentially Stale Documents")
    lines.append("=" * 50)
    lines.append("")

    by_source = defaultdict(list)
    for w in warnings:
        by_source[w["source"]].append(w)

    for source, deps in sorted(by_source.items()):
        lines.append(f"Changed: {source}")
        for d in sorted(deps, key=lambda x: x["dependent"]):
            lines.append(f"  -> {d['dependent']}")
            lines.append(f"     Why: {d['why']}")
        lines.append("")

    lines.append(f"Total: {len(warnings)} document(s) may need review.")
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description="Check document traceability")
    parser.add_argument("--base", default="main", help="Base branch to diff against")
    parser.add_argument("--format", choices=["github", "text"], default="text",
                        help="Output format")
    parser.add_argument("--files", nargs="*", help="Override: check these files instead of git diff")
    args = parser.parse_args()

    if not TRACEABILITY_PATH.exists():
        print(f"Traceability file not found: {TRACEABILITY_PATH}", file=sys.stderr)
        sys.exit(2)

    dependencies = load_traceability()

    if args.files:
        changed_files = args.files
    else:
        changed_files = get_changed_files(args.base)

    doc_extensions = {".md", ".yaml", ".yml"}
    doc_files = [f for f in changed_files if Path(f).suffix in doc_extensions]

    if not doc_files:
        if args.format == "text":
            print("No documentation files changed — skipping traceability check.")
        sys.exit(0)

    warnings = build_warnings(doc_files, dependencies)

    if not warnings:
        if args.format == "text":
            print("All dependents are either unchanged or updated in this PR. No warnings.")
        sys.exit(0)

    if args.format == "github":
        print(format_github(warnings))
    else:
        print(format_text(warnings))

    sys.exit(1)


if __name__ == "__main__":
    main()
