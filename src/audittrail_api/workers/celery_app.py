"""Celery application used by background workers."""

from celery import Celery

from audittrail_api.config import get_settings
from audittrail_api.dead_letters import signals as dead_letter_signals  # noqa: F401

settings = get_settings()
celery_app = Celery(
    "audittrail",
    broker=settings.redis_url,
    backend=settings.redis_url,
    include=["audittrail_api.workers.tasks"],
)
celery_app.conf.update(
    task_acks_late=True,
    task_reject_on_worker_lost=True,
    worker_prefetch_multiplier=1,
    task_track_started=True,
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
)
