#!/bin/sh
set -e

case "$1" in
  api)
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
    exec alembic upgrade head
    ;;
  *)
    echo "Usage: startup.sh {api|api-dev|worker|beat|migrate}" >&2
    exit 1
    ;;
esac
