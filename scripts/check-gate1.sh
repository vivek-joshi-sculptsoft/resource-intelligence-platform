#!/usr/bin/env bash
# Check Gate 1: spec approval marker exists.
# Called from /implement-ticket, /implement-sprint, /ship skills.
# Exit 0 = approved, Exit 1 = not approved (with message).

MARKER="docs/approvals/SPEC-APPROVED"

if [ -f "$MARKER" ]; then
  echo "Gate 1 PASSED — spec approved by: $(cat "$MARKER")"
  exit 0
else
  echo ""
  echo "╔══════════════════════════════════════════════════════════╗"
  echo "║  GATE 1 BLOCKED — Spec not approved                    ║"
  echo "║                                                         ║"
  echo "║  Before implementation can begin, a human must review   ║"
  echo "║  fsd/FSD.md, techstack/decisions/, and the relevant     ║"
  echo "║  modules/ specs, then create the approval marker:       ║"
  echo "║                                                         ║"
  echo "║  echo \"approved-by: <name> \$(date -u +%F)\" \\           ║"
  echo "║    > docs/approvals/SPEC-APPROVED                       ║"
  echo "║                                                         ║"
  echo "║  See docs/approvals/README.md for details.              ║"
  echo "╚══════════════════════════════════════════════════════════╝"
  echo ""
  exit 1
fi
