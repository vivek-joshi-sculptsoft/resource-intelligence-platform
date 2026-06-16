from celery import Celery
from celery.schedules import crontab

from app.config import settings

celery_app = Celery(
    "ri_platform",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="Asia/Kolkata",
    enable_utc=True,
    task_track_started=True,
    task_default_retry_delay=10,
    task_max_retries=3,
    broker_connection_retry_on_startup=True,
    beat_schedule={
        "auto-release-assignments": {
            "task": "auto_release_assignments",
            "schedule": crontab(hour=0, minute=0),
        },
        "process-recurring-costs": {
            "task": "process_recurring_costs",
            "schedule": crontab(hour=0, minute=0, day_of_month=1),
        },
    },
)


@celery_app.task(name="ping")
def ping() -> str:
    return "pong"


@celery_app.task(name="auto_release_assignments", bind=True, max_retries=3)
def auto_release_assignments_task(self):
    """See FSD §8 — Daily auto-release job."""
    import asyncio

    from app.database import async_session_factory
    from app.modules.allocations.jobs import run_auto_release

    async def _run():
        async with async_session_factory() as session:
            try:
                result = await run_auto_release(session)
                await session.commit()
                return {"released_count": len(result), "assignments": result}
            except Exception:
                await session.rollback()
                raise

    return asyncio.run(_run())


@celery_app.task(name="process_recurring_costs", bind=True, max_retries=3)
def process_recurring_costs_task(self):
    """See JOBS.md — Monthly recurring cost snapshot generation."""
    import asyncio

    from app.database import async_session_factory
    from app.modules.nonhuman_costs.jobs import run_process_recurring_costs

    async def _run():
        async with async_session_factory() as session:
            try:
                result = await run_process_recurring_costs(session)
                await session.commit()
                return result
            except Exception:
                await session.rollback()
                raise

    return asyncio.run(_run())
