"""异步导出分析结果为 CSV。"""
from __future__ import annotations

import csv
import logging
import uuid
from pathlib import Path

from backend.app.celery_app import celery_app
from backend.app.core.config import settings
from backend.app.models.orm import AnalyzeResult, Content, ExportJob

logger = logging.getLogger("backend.app.tasks.export")


@celery_app.task(bind=True, name="lingjian.export_results")
def export_results_task(self, export_pk: int) -> dict:
    from backend.app.db.session import SessionLocal

    db = SessionLocal()
    try:
        job = db.query(ExportJob).filter(ExportJob.id == export_pk).first()
        if job is None:
            return {"ok": False, "error": "export_not_found"}
        job.status = "processing"
        job.celery_task_id = self.request.id
        db.commit()

        owner_id = job.owner_id
        rows = (
            db.query(AnalyzeResult)
            .join(Content, AnalyzeResult.content_id == Content.id)
            .filter(Content.owner_id == owner_id)
            .all()
        )

        out_dir = settings.upload_dir / "exports"
        out_dir.mkdir(parents=True, exist_ok=True)
        path = out_dir / f"export-{export_pk}-{uuid.uuid4().hex}.csv"
        with path.open("w", newline="", encoding="utf-8-sig") as fout:
            w = csv.writer(fout)
            w.writerow(["content_id", "risk_level", "score", "basis"])
            for r in rows:
                payload = r.payload or {}
                fin = payload.get("final") or {}
                cid = payload.get("content_id") or ""
                if r.content is not None:
                    cid = cid or r.content.public_id
                w.writerow(
                    [
                        cid,
                        fin.get("risk_level", ""),
                        fin.get("score", ""),
                        fin.get("basis", ""),
                    ]
                )
        job.status = "completed"
        job.file_path = str(path)
        db.commit()
        return {"ok": True, "path": str(path)}
    except Exception as e:
        logger.exception("export failed")
        job = db.query(ExportJob).filter(ExportJob.id == export_pk).first()
        if job:
            job.status = "failed"
            job.error_message = str(e)
            db.commit()
        return {"ok": False, "error": str(e)}
    finally:
        db.close()
