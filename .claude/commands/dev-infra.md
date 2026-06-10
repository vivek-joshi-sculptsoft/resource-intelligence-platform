Start infrastructure services (PostgreSQL + Redis) via Docker Compose.

Steps:
1. `cd /Users/sculptsoft/AgenticSDLC/project/resource-intelligence-platform && docker compose -f docker-compose.dev.yml up postgres redis -d`
2. Wait for healthchecks to pass: `docker compose -f docker-compose.dev.yml ps`
3. Report status of both containers

PostgreSQL: localhost:5432 (ri_platform / devuser / devpass)
Redis: localhost:6379
