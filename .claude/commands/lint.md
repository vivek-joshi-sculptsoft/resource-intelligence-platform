Run linters for backend, frontend, or both.

Argument: $ARGUMENTS

If argument is "backend" or "be": run `cd backend && python3 -m ruff check app/ && python3 -m ruff format --check app/`
If argument is "frontend" or "fe": run `cd frontend && npx tsc -b --noEmit`
If argument is "all" or empty: run both sequentially
If argument is "fix": run `cd backend && python3 -m ruff check app/ --fix && python3 -m ruff format app/` to auto-fix backend lint issues

Report results for each.
