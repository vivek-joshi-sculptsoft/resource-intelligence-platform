from app.jobs.celery_app import celery_app, ping


def test_celery_app_name():
    assert celery_app.main == "ri_platform"


def test_celery_timezone():
    assert celery_app.conf.timezone == "Asia/Kolkata"


def test_celery_serializer_is_json():
    assert celery_app.conf.task_serializer == "json"
    assert "json" in celery_app.conf.accept_content


def test_celery_utc_enabled():
    assert celery_app.conf.enable_utc is True


def test_celery_track_started():
    assert celery_app.conf.task_track_started is True


def test_celery_default_retry_delay():
    assert celery_app.conf.task_default_retry_delay == 10


def test_celery_max_retries():
    assert celery_app.conf.task_max_retries == 3


def test_celery_beat_schedule_empty():
    assert celery_app.conf.beat_schedule == {}


def test_ping_task_registered():
    assert "ping" in celery_app.tasks


def test_ping_returns_pong():
    result = ping()
    assert result == "pong"


def test_celery_broker_retry_on_startup():
    assert celery_app.conf.broker_connection_retry_on_startup is True
