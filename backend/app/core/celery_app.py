"""Celery task queue configuration."""

from celery import Celery

from app.core.config import get_settings

settings = get_settings()

celery_app = Celery(
    "merit",
    broker=settings.celery_broker_url,
    backend=settings.celery_result_backend,
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_acks_late=True,
    worker_prefetch_multiplier=1,
    task_default_queue="default",
    task_queues={
        "default": {"exchange": "default", "routing_key": "default"},
        "ocr": {"exchange": "ocr", "routing_key": "ocr"},
        "disbursement": {"exchange": "disbursement", "routing_key": "disbursement"},
        "notifications": {"exchange": "notifications", "routing_key": "notifications"},
    },
    task_routes={
        "app.tasks.ocr.*": {"queue": "ocr"},
        "app.tasks.disbursement.*": {"queue": "disbursement"},
        "app.tasks.notifications.*": {"queue": "notifications"},
    },
    # Retry configuration for transient failures
    task_default_retry_delay=60,
    task_max_retries=5,
)
