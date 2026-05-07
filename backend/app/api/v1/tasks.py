"""任务进度查询（Celery）。"""
from __future__ import annotations

from celery.result import AsyncResult

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from backend.app.celery_app import celery_app
from backend.app.core.deps import get_current_user, get_db
from backend.app.models.orm import AnalyzeJob, ExportJob, User

router = APIRouter(prefix="/tasks", tags=["tasks"])


@router.get("/{task_id}")
def get_task_status(
    task_id: str,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> dict:
    ar = AsyncResult(task_id, app=celery_app)
    body: dict = {"task_id": task_id, "state": ar.state}
    if ar.successful():
        body["result"] = ar.result
    elif ar.failed():
        body["error"] = str(ar.result)

    aj = db.query(AnalyzeJob).filter(AnalyzeJob.celery_task_id == task_id).first()
    if aj and aj.content and aj.content.owner_id == user.id:
        body["content_id"] = aj.content.public_id
        body["job_status"] = aj.status
    ej = db.query(ExportJob).filter(ExportJob.celery_task_id == task_id).first()
    if ej and ej.owner_id == user.id:
        body["export_id"] = ej.id
        body["export_status"] = ej.status
        body["file_path"] = ej.file_path
    return body
