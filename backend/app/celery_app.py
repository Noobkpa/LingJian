"""Celery 应用实例。"""
from __future__ import annotations

from celery import Celery

from backend.app.core.config import settings

celery_app = Celery(
    "lingjian",
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
)

# 注册具体任务（避免 autodiscover 未找到子模块）
import backend.app.tasks.analyze_tasks  # noqa: E402,F401
import backend.app.tasks.export_tasks  # noqa: E402,F401
