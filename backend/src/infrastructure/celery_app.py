import os

from celery import Celery

REDIS_URL = f"redis://{os.environ.get('REDIS_HOST', 'localhost')}:{os.environ.get('REDIS_PORT', '6379')}/0"

celery_app = Celery(
    "clinic_ai",
    broker=REDIS_URL,
    backend=REDIS_URL,
    include=[
        "src.infrastructure.celery_tasks.vectorize_document",
        "src.infrastructure.celery_tasks.process_publishing_batch",
    ],
)

celery_app.conf.update(
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_acks_late=True,
    worker_prefetch_multiplier=1,
)
