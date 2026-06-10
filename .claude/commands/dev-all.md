Start the full dev stack: infrastructure + backend + frontend.

Steps:
1. Start PostgreSQL and Redis: `cd /Users/sculptsoft/AgenticSDLC/project/resource-intelligence-platform && docker compose -f docker-compose.dev.yml up postgres redis -d`
2. Wait for healthchecks: `docker compose -f docker-compose.dev.yml ps` — confirm postgres and redis are healthy
3. Start backend in background: `cd backend && python3 -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000 &`
4. Start frontend in background: `cd frontend && npm run dev &`
5. Confirm both servers are running — backend at http://localhost:8000/api/v1/health, frontend at http://localhost:5173

If any step fails, report the error and stop.
