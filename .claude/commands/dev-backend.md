Start the backend FastAPI dev server with hot-reload.

Steps:
1. `cd backend && python3 -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000`

This runs uvicorn with auto-reload on code changes. API available at http://localhost:8000. Health check at http://localhost:8000/api/v1/health.

Note: Requires PostgreSQL and Redis running (use `/dev-infra` command or `docker compose -f docker-compose.dev.yml up postgres redis -d` first).
