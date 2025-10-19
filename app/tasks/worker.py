from celery import Celery

from app.core.config import settings

# Celeryアプリケーションの作成
celery_app = Celery(
    "todo_api",
    broker=settings.redis_url,
    backend=settings.redis_url,
    include=["app.tasks.tasks", "app.tasks.backup_tasks"],
)

# Celery設定
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=30 * 60,  # 30分
    task_soft_time_limit=25 * 60,  # 25分
    worker_prefetch_multiplier=1,
    worker_max_tasks_per_child=1000,
)

# タスクの自動検出
celery_app.autodiscover_tasks(["app.tasks"])
