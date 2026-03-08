from celery import Celery

from app.config.settings import settings

celery_app = Celery(
    "hptraffic",
    broker=settings.broker_url,
    backend=settings.broker_url,
    include=["app.workers.tasks"],
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
)
