from celery import Celery

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
    beat_schedule={},
)


@celery_app.task(name="ping")
def ping() -> str:
    return "pong"
