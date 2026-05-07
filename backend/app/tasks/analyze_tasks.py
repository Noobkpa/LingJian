"""异步分析内容：写库 + ES 索引。"""
from __future__ import annotations

import logging
from pathlib import Path

from backend.app.celery_app import celery_app
from backend.app.models.orm import AnalyzeJob, AnalyzeResult, Content, ContentStatus, JobStatus
from backend.app.services.es_service import es_service
from backend.app.services.orchestrator import pipeline_orchestrator
from backend.app.services.sync_analyze_persist import review_status_after_analyze

logger = logging.getLogger("backend.app.tasks.analyze")


@celery_app.task(bind=True, name="lingjian.analyze_content")
def analyze_content_task(self, content_pk: int) -> dict:
    from backend.app.db.session import SessionLocal

    db = SessionLocal()
    try:
        content = db.query(Content).filter(Content.id == content_pk).first()
        if content is None:
            return {"ok": False, "error": "content_not_found"}
        job = (
            db.query(AnalyzeJob)
            .filter(AnalyzeJob.content_id == content_pk)
            .order_by(AnalyzeJob.id.desc())
            .first()
        )
        if job:
            job.status = JobStatus.processing.value
            job.celery_task_id = self.request.id
            db.commit()

        content.status = ContentStatus.processing.value
        db.commit()

        modality = content.modality
        path = Path(content.file_path) if content.file_path else None
        text = content.text_snapshot or ""

        try:
            if modality == "text":
                resp = pipeline_orchestrator.analyze_text(text, content.public_id)
            elif modality == "image":
                if path is None or not path.is_file():
                    raise ValueError("缺少有效的图片路径")
                resp = pipeline_orchestrator.analyze_image(path, content.public_id)
            else:
                if path is None or not path.is_file():
                    raise ValueError("缺少有效的图片路径")
                resp = pipeline_orchestrator.analyze_mixed(text, path, content.public_id)

            payload = resp.model_dump(mode="json", exclude={"human_review"})
            existing = db.query(AnalyzeResult).filter(AnalyzeResult.content_id == content.id).first()
            if existing:
                existing.payload = payload
            else:
                db.add(AnalyzeResult(content_id=content.id, payload=payload))
            content.status = ContentStatus.completed.value
            risk_label = str(resp.final.risk_level or "")
            content.review_status = review_status_after_analyze(risk_label)
            if job:
                job.status = JobStatus.completed.value
                job.error_message = None
            db.commit()

            es_service.index_content(
                content.public_id,
                {
                    "content_id": content.public_id,
                    "owner_id": content.owner_id,
                    "text": resp.input_text,
                    "risk_level": resp.final.risk_level,
                    "features": resp.final.features,
                },
            )
            return {"ok": True, "content_id": content.public_id}
        except Exception as e:
            logger.exception("analyze_content_task failed content_pk=%s", content_pk)
            content.status = ContentStatus.failed.value
            if job:
                job.status = JobStatus.failed.value
                job.error_message = str(e)
            db.commit()
            return {"ok": False, "error": str(e)}
    finally:
        db.close()


@celery_app.task(bind=True, name="lingjian.batch_import")
def batch_import_task(self, content_ids: list[int]) -> dict:
    """顺序投递多个分析任务。"""
    ids: list[str] = []
    for cid in content_ids:
        r = analyze_content_task.delay(cid)
        ids.append(r.id)
    return {"task_ids": ids}
