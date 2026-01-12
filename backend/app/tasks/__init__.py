"""Celery tasks for background job processing.

Phase 6 & 10: Async job queue for:
- Weekly rakeback settlement
- Statistics aggregation
- Notifications
"""

from app.tasks.celery_app import celery_app
from app.tasks.rakeback import calculate_weekly_rakeback_task

__all__ = [
    "celery_app",
    "calculate_weekly_rakeback_task",
]
