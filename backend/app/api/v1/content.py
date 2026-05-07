"""内容入库与异步任务投递。"""
from __future__ import annotations

import logging
import tempfile
import uuid
import zipfile
from pathlib import Path

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from backend.app.core.config import settings
from backend.app.core.deps import require_permission
from backend.app.core.exceptions import AppException
from backend.app.db.session import get_db
from backend.app.models.orm import AnalyzeJob, Content, ContentStatus, JobStatus, ReviewStatus, User
from backend.app.services.upload_validate import save_upload_validated

logger = logging.getLogger("backend.app.content")

router = APIRouter(prefix="/contents", tags=["contents"])


class TextQueueBody(BaseModel):
    text: str = Field(..., min_length=1, max_length=settings.max_text_chars)


def _safe_extract_zip(zip_path: Path, dest: Path, *, max_files: int) -> list[Path]:
    dest.mkdir(parents=True, exist_ok=True)
    out: list[Path] = []
    with zipfile.ZipFile(zip_path, "r") as zf:
        members = [m for m in zf.infolist() if not m.is_dir()]
        if len(members) > max_files:
            raise AppException("ZIP_TOO_LARGE", "压缩包内文件过多", status_code=400)
        for m in members:
            name = Path(m.filename)
            if name.is_absolute() or ".." in name.parts:
                raise AppException("ZIP_INVALID", "非法路径", status_code=400)
            target = (dest / name).resolve()
            if not str(target).startswith(str(dest.resolve())):
                raise AppException("ZIP_INVALID", "路径穿越", status_code=400)
            target.parent.mkdir(parents=True, exist_ok=True)
            with zf.open(m) as src, target.open("wb") as out_f:
                written = 0
                while True:
                    chunk = src.read(1024 * 1024)
                    if not chunk:
                        break
                    written += len(chunk)
                    if written > settings.max_upload_bytes:
                        raise AppException("ZIP_ENTRY_TOO_BIG", "单文件过大", status_code=413)
                    out_f.write(chunk)
            out.append(target)
    return out


@router.post("/text")
def queue_text_analysis(
    body: TextQueueBody,
    db: Session = Depends(get_db),
    user: User = Depends(require_permission("content:upload")),
) -> dict:
    from backend.app.tasks.analyze_tasks import analyze_content_task

    public_id = uuid.uuid4().hex
    c = Content(
        public_id=public_id,
        owner_id=user.id,
        modality="text",
        text_snapshot=body.text,
        status=ContentStatus.pending.value,
        review_status=ReviewStatus.none.value,
    )
    db.add(c)
    db.flush()
    job = AnalyzeJob(content_id=c.id, status=JobStatus.pending.value)
    db.add(job)
    db.flush()
    res = analyze_content_task.delay(c.id)
    job.celery_task_id = res.id
    db.commit()
    return {"content_id": public_id, "job_id": job.id, "task_id": res.id}


@router.post("/image")
async def queue_image_analysis(
    db: Session = Depends(get_db),
    user: User = Depends(require_permission("content:upload")),
    file: UploadFile = File(...),
) -> dict:
    from backend.app.tasks.analyze_tasks import analyze_content_task

    path, digest = await save_upload_validated(file)
    public_id = uuid.uuid4().hex
    c = Content(
        public_id=public_id,
        owner_id=user.id,
        modality="image",
        file_path=str(path),
        file_hash=digest,
        status=ContentStatus.pending.value,
        review_status=ReviewStatus.none.value,
    )
    db.add(c)
    db.flush()
    job = AnalyzeJob(content_id=c.id, status=JobStatus.pending.value)
    db.add(job)
    db.flush()
    res = analyze_content_task.delay(c.id)
    job.celery_task_id = res.id
    db.commit()
    return {"content_id": public_id, "job_id": job.id, "task_id": res.id}


@router.post("/mixed")
async def queue_mixed_analysis(
    db: Session = Depends(get_db),
    user: User = Depends(require_permission("content:upload")),
    text: str = Form(default=""),
    file: UploadFile = File(...),
) -> dict:
    from backend.app.tasks.analyze_tasks import analyze_content_task

    if len(text) > settings.max_text_chars:
        raise HTTPException(status_code=400, detail="文本过长")
    path, digest = await save_upload_validated(file)
    public_id = uuid.uuid4().hex
    c = Content(
        public_id=public_id,
        owner_id=user.id,
        modality="mixed",
        text_snapshot=text or None,
        file_path=str(path),
        file_hash=digest,
        status=ContentStatus.pending.value,
        review_status=ReviewStatus.none.value,
    )
    db.add(c)
    db.flush()
    job = AnalyzeJob(content_id=c.id, status=JobStatus.pending.value)
    db.add(job)
    db.flush()
    res = analyze_content_task.delay(c.id)
    job.celery_task_id = res.id
    db.commit()
    return {"content_id": public_id, "job_id": job.id, "task_id": res.id}


@router.post("/batch_zip")
async def queue_zip_batch(
    db: Session = Depends(get_db),
    user: User = Depends(require_permission("content:batch")),
    file: UploadFile = File(...),
) -> dict:
    from backend.app.tasks.analyze_tasks import analyze_content_task

    if not file.filename or not file.filename.lower().endswith(".zip"):
        raise HTTPException(status_code=400, detail="请上传 zip 文件")
    tmp = Path(tempfile.mkdtemp(dir=str(settings.upload_dir))) / "batch.zip"
    size = 0
    with tmp.open("wb") as fout:
        while True:
            chunk = await file.read(1024 * 1024)
            if not chunk:
                break
            size += len(chunk)
            if size > settings.max_upload_bytes * 5:
                raise HTTPException(status_code=413, detail="压缩包过大")
            fout.write(chunk)
    head = tmp.read_bytes()[:4]
    if head != b"PK\x03\x04" and head[:2] != b"PK":
        tmp.unlink(missing_ok=True)
        raise HTTPException(status_code=400, detail="不是有效的 zip 文件")

    extract_root = tmp.parent / "extract"
    paths = _safe_extract_zip(tmp, extract_root, max_files=settings.max_zip_entries)
    allowed_sfx = {".png", ".jpg", ".jpeg", ".bmp", ".webp"}
    created: list[dict] = []
    for p in paths:
        if p.suffix.lower() not in allowed_sfx:
            continue
        public_id = uuid.uuid4().hex
        c = Content(
            public_id=public_id,
            owner_id=user.id,
            modality="image",
            file_path=str(p),
            status=ContentStatus.pending.value,
            review_status=ReviewStatus.none.value,
        )
        db.add(c)
        db.flush()
        job = AnalyzeJob(content_id=c.id, status=JobStatus.pending.value)
        db.add(job)
        db.flush()
        res = analyze_content_task.delay(c.id)
        job.celery_task_id = res.id
        created.append({"content_id": public_id, "job_id": job.id, "task_id": res.id})
    db.commit()
    return {"count": len(created), "items": created}
