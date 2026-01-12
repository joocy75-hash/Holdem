"""Celery application configuration.

Phase 6 & 10: Async job queue setup.

Features:
- Redis as broker and result backend
- Task routing by queue
- Scheduled tasks via Celery Beat
"""

import os

from celery import Celery
from celery.schedules import crontab

# Get Redis URL from environment
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")

# Create Celery app
celery_app = Celery(
    "poker_tasks",
    broker=f"{REDIS_URL.rsplit('/', 1)[0]}/1",  # Use DB 1 for broker
    backend=f"{REDIS_URL.rsplit('/', 1)[0]}/2",  # Use DB 2 for results
    include=[
        "app.tasks.rakeback",
    ],
)

# Celery configuration
celery_app.conf.update(
    # Serialization
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    
    # Timezone
    timezone="Asia/Seoul",
    enable_utc=True,
    
    # Task routing
    task_routes={
        "app.tasks.rakeback.*": {"queue": "settlement"},
        "app.tasks.analytics.*": {"queue": "analytics"},
        "app.tasks.notification.*": {"queue": "notification"},
    },
    
    # Task execution settings
    task_acks_late=True,
    task_reject_on_worker_lost=True,
    worker_prefetch_multiplier=1,
    
    # Result settings
    result_expires=86400,  # 24 hours
    
    # Beat schedule (periodic tasks)
    beat_schedule={
        # Weekly rakeback settlement - Monday 4 AM KST
        "weekly-rakeback-settlement": {
            "task": "app.tasks.rakeback.calculate_weekly_rakeback_task",
            "schedule": crontab(hour=4, minute=0, day_of_week=1),
            "options": {"queue": "settlement"},
        },
    },
)


# Optional: Configure for development
if os.getenv("APP_ENV") == "development":
    celery_app.conf.update(
        task_always_eager=False,  # Set to True to run tasks synchronously
        task_eager_propagates=True,
    )
