#!/bin/sh
set -e

run_migrations() {
  case "$DATABASE_URL" in
    sqlite*|"") ;;
    # `python -m alembic` (not the bare `alembic` console script) so cwd (/app) lands on
    # sys.path — env.py does `from app.config import settings`, which otherwise 404s.
    *) python -m alembic upgrade head ;;
  esac
}

case "$1" in
  api)
    run_migrations
    exec uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers "${UVICORN_WORKERS:-2}"
    ;;
  api-dev)
    exec uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
    ;;
  worker)
    exec celery -A app.jobs.celery_app worker -l info
    ;;
  beat)
    exec celery -A app.jobs.celery_app beat -l info
    ;;
  migrate)
    exec python -m alembic upgrade head
    ;;
  *)
    echo "Usage: startup.sh {api|api-dev|worker|beat|migrate}" >&2
    exit 1
    ;;
esac
