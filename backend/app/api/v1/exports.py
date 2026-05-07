"""异步导出任务。"""
from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from backend.app.core.deps import get_db, require_permission
from backend.app.models.orm import ExportJob, User

router = APIRouter(prefix="/exports", tags=["exports"])


@router.post("")
def start_export(
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[User, Depends(require_permission("admin:export"))],
) -> dict:
    from backend.app.tasks.export_tasks import export_results_task

    job = ExportJob(owner_id=user.id, status="pending", export_format="csv")
    db.add(job)
    db.flush()
    res = export_results_task.delay(job.id)
    job.celery_task_id = res.id
    db.commit()
    return {"export_id": job.id, "task_id": res.id}
