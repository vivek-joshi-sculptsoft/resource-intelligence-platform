Run tests for backend, frontend, or both.

Argument: $ARGUMENTS

If argument is "backend" or "be": run `cd backend && python3 -m pytest tests/ -v`
If argument is "frontend" or "fe": run `cd frontend && npx vitest run`
If argument is "all" or empty: run both sequentially, backend first then frontend
If argument is "coverage": run `cd backend && python3 -m pytest tests/ -v --cov=app --cov-report=term-missing`

Report pass/fail counts for each.
