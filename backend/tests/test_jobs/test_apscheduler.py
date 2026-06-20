from app.jobs.scheduler import configure_scheduler, scheduler, shutdown_scheduler


def test_scheduler_timezone():
    assert str(scheduler.timezone) == "Asia/Kolkata"


def test_configure_registers_jobs():
    configure_scheduler()
    job_ids = [job.id for job in scheduler.get_jobs()]
    assert "auto-release-assignments" in job_ids
    assert "process-recurring-costs" in job_ids


def test_configure_scheduler_is_idempotent():
    configure_scheduler()
    configure_scheduler()
    job_ids = [job.id for job in scheduler.get_jobs()]
    assert job_ids.count("auto-release-assignments") == 1
    assert job_ids.count("process-recurring-costs") == 1


def test_auto_release_schedule():
    configure_scheduler()
    job = scheduler.get_job("auto-release-assignments")
    assert job is not None
    trigger = job.trigger
    assert str(trigger) == "cron[hour='0', minute='0']"


def test_recurring_costs_schedule():
    configure_scheduler()
    job = scheduler.get_job("process-recurring-costs")
    assert job is not None
    trigger = job.trigger
    assert str(trigger) == "cron[day='1', hour='0', minute='0']"


def test_shutdown_when_not_running():
    shutdown_scheduler()
