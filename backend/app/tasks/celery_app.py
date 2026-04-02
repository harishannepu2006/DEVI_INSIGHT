"""Celery application configuration."""
from celery import Celery
from celery.schedules import crontab
from app.config import settings

celery_app = Celery(
    "devinsight",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL,
    include=[
        "app.tasks.analysis_tasks",
        "app.tasks.monitoring_tasks",
    ]
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    result_expires=3600,
    worker_max_tasks_per_child=100,
)

# Periodic tasks (Celery Beat)
celery_app.conf.beat_schedule = {
    "monitor-repos-every-hour": {
        "task": "app.tasks.monitoring_tasks.check_monitored_repos",
        "schedule": crontab(minute=0),  # Every hour
    },
}
