"""In-process job scheduler using APScheduler — drop-in alternative to Celery for environments without Redis."""

import logging

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

logger = logging.getLogger(__name__)

scheduler = AsyncIOScheduler(timezone="Asia/Kolkata")


async def _run_auto_release() -> None:
    from app.database import async_session_factory
    from app.modules.allocations.jobs import run_auto_release

    async with async_session_factory() as session:
        try:
            result = await run_auto_release(session)
            await session.commit()
            logger.info("APScheduler auto-release completed: %d assignments released", len(result))
        except Exception:
            await session.rollback()
            logger.exception("APScheduler auto-release failed")


async def _run_process_recurring_costs() -> None:
    from app.database import async_session_factory
    from app.modules.nonhuman_costs.jobs import run_process_recurring_costs

    async with async_session_factory() as session:
        try:
            result = await run_process_recurring_costs(session)
            await session.commit()
            logger.info("APScheduler recurring costs completed: %s", result)
        except Exception:
            await session.rollback()
            logger.exception("APScheduler recurring costs failed")


def configure_scheduler() -> None:
    scheduler.remove_all_jobs()
    scheduler.add_job(
        _run_auto_release,
        CronTrigger(hour=0, minute=0),
        id="auto-release-assignments",
        replace_existing=True,
    )
    scheduler.add_job(
        _run_process_recurring_costs,
        CronTrigger(day=1, hour=0, minute=0),
        id="process-recurring-costs",
        replace_existing=True,
    )


def start_scheduler() -> None:
    configure_scheduler()
    scheduler.start()
    logger.info("APScheduler started with %d jobs", len(scheduler.get_jobs()))


def shutdown_scheduler() -> None:
    if scheduler.running:
        scheduler.shutdown(wait=False)
        logger.info("APScheduler shut down")
