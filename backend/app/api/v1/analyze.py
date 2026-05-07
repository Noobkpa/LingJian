"""分析路由：文本 / 图片 / 混合（同步；鉴权 + 可选缓存）；同步结果落库与历史查询。"""
from __future__ import annotations

import hashlib
import json
import logging
from pathlib import Path
from typing import Annotated, Any

import redis
from fastapi import APIRouter, Depends, File, Form, HTTPException, Request, UploadFile
from pydantic import BaseModel, Field
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, joinedload

from backend.app.core.config import settings
from backend.app.core.deps import require_permission
from backend.app.db.session import get_db
from backend.app.models.orm import (
    AnalyzeJob,
    AnalyzeResult,
    Content,
    ContentFavorite,
    ReviewStatus,
    User,
)
from backend.app.schemas.analyze import AnalyzeResponse, HumanReviewOut, TextAnalyzeRequest
from backend.app.services.orchestrator import pipeline_orchestrator
from backend.app.services.review_list import format_datetime_shanghai
from backend.app.services.standard_judgment_builder import rehydrate_standard_judgment
from backend.app.services.sync_analyze_persist import persist_sync_analyze
from backend.app.services.upload_validate import save_upload_validated

router = APIRouter(prefix="/analyze", tags=["analyze"])
logger = logging.getLogger("backend.app.analyze")


def _human_review_from_content(c: Content) -> HumanReviewOut | None:
    """从 Content 生成用户可见的人工复核摘要；未进入复核流程则返回 None。"""
    st = (c.review_status or ReviewStatus.none.value).strip()
    if st in (ReviewStatus.none.value, ""):
        return None
    reviewed_iso = c.reviewed_at.isoformat() if c.reviewed_at else None
    if st == ReviewStatus.pending.value:
        return HumanReviewOut(
            status=st,
            summary_zh="等待人工复核。以下为系统自动研判，最终以人工复核结论为准。",
            note=None,
            reviewed_at=None,
        )
    if st == ReviewStatus.claimed.value:
        return HumanReviewOut(
            status=st,
            summary_zh="人工复核处理中。以下为系统自动研判，最终以人工复核结论为准。",
            note=None,
            reviewed_at=None,
        )
    if st == ReviewStatus.approved.value:
        return HumanReviewOut(
            status=st,
            summary_zh="人工复核结论：不构成伪科普（人工认定）。以下模型输出仅供参考。",
            note=(c.review_note or "").strip() or None,
            reviewed_at=reviewed_iso,
        )
    if st == ReviewStatus.rejected.value:
        return HumanReviewOut(
            status=st,
            summary_zh="人工复核结论：认定为伪科普。以下模型输出仅供参考。",
            note=(c.review_note or "").strip() or None,
            reviewed_at=reviewed_iso,
        )
    return HumanReviewOut(
        status=st,
        summary_zh="",
        note=(c.review_note or "").strip() or None,
        reviewed_at=reviewed_iso,
    )


def _with_persist_meta(resp: AnalyzeResponse, persist_ok: bool) -> AnalyzeResponse:
    """在响应 meta 中标注是否已成功落库（供排查审核队列缺失等问题）。"""
    meta = dict(resp.meta or {})
    meta["persist_ok"] = persist_ok
    return resp.model_copy(update={"meta": meta})


class HistoryItemOut(BaseModel):
    content_id: str
    content_type: str
    risk_level: str
    llm_score: float
    upload_time: str


class HistoryListOut(BaseModel):
    list: list[HistoryItemOut]
    total: int


class DeleteHistoryBody(BaseModel):
    content_ids: list[str] = Field(default_factory=list)


def _infer_cache_bundle_ver() -> str:
    """避免 Redis 长期缓存「LLM 失败/缺 tiktoken」的旧结果；随 LLM 开关与 tiktoken 可用性变化。"""
    if settings.infer_cache_version:
        return settings.infer_cache_version
    try:
        import tiktoken  # noqa: F401

        tik = "1"
    except ImportError:
        tik = "0"
    try:
        from backend.app.services.infer_admin_settings import get_infer_bundle, resolve_quantization

        qq = resolve_quantization(get_infer_bundle())
    except Exception:
        qq = "16bit"
    qn = qq.replace("bit", "")
    # v11：max_new_tokens / LLM 量化策略变化后废弃旧 Redis 缓存
    return f"v11-basis-llm{int(settings.enable_llm)}-tik{tik}-q{qn}"


def _infer_cache_key(prefix: str, payload: str) -> str:
    h = hashlib.sha256(payload.encode("utf-8")).hexdigest()
    ver = _infer_cache_bundle_ver()
    return f"infer:{prefix}:{ver}:{h}"


def _get_cached(redis_client: Any | None, key: str) -> AnalyzeResponse | None:
    if redis_client is None:
        return None
    try:
        raw = redis_client.get(key)
        if not raw:
            return None
        data = json.loads(raw)
        return AnalyzeResponse.model_validate(data)
    except Exception:
        return None


def _should_cache_infer_response(resp: AnalyzeResponse) -> bool:
    """无可用正文时不缓存，避免 OCR 解析失败或旧逻辑把空结果长期钉在 Redis。"""
    return bool((resp.input_text or "").strip())


def _set_cached(redis_client: Any | None, key: str, resp: AnalyzeResponse) -> None:
    if redis_client is None:
        return
    if not _should_cache_infer_response(resp):
        return
    try:
        redis_client.setex(
            key,
            settings.cache_infer_ttl_sec,
            json.dumps(resp.model_dump(), ensure_ascii=False),
        )
    except redis.RedisError:
        pass


def _map_risk_to_ui(risk_raw: str) -> str:
    s = str(risk_raw or "")
    if "高" in s:
        return "high"
    if "中" in s:
        return "middle"
    if "低" in s:
        return "low"
    sl = s.lower()
    if "high" in sl:
        return "high"
    if "mid" in sl:
        return "middle"
    if "low" in sl:
        return "low"
    return "low"


def _history_row_to_item(content: Content) -> HistoryItemOut | None:
    if not content.result or not content.result.payload:
        return None
    payload = content.result.payload
    sj = payload.get("standard_judgment") or {}
    fin = payload.get("final") or {}
    risk_zh = sj.get("risk_level") or fin.get("risk_level") or "低"
    risk = _map_risk_to_ui(str(risk_zh))
    ct = content.modality
    if ct == "mixed":
        ct = "mix"
    raw_score = sj.get("comprehensive_score")
    if raw_score is None:
        raw_score = fin.get("score")
    score = round(float(raw_score or 0), 1)
    upload_time = format_datetime_shanghai(content.created_at)
    return HistoryItemOut(
        content_id=content.public_id,
        content_type=ct,
        risk_level=risk,
        llm_score=score,
        upload_time=upload_time,
    )


@router.get("/history", response_model=HistoryListOut)
def list_analyze_history(
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[User, Depends(require_permission("analyze:run"))],
    page: int = 1,
    page_size: int = 20,
    risk_level: str | None = None,
    content_type: str | None = None,
    start_date: str | None = None,
    end_date: str | None = None,
) -> HistoryListOut:
    """当前用户同步/异步识别记录（有 analyze_results 的条目）。"""
    q = db.query(Content).options(joinedload(Content.result)).filter(Content.owner_id == user.id)
    modality_filter: str | None = None
    if content_type == "mix":
        modality_filter = "mixed"
    elif content_type in ("text", "image"):
        modality_filter = content_type
    if modality_filter:
        q = q.filter(Content.modality == modality_filter)
    rows = q.order_by(Content.created_at.desc()).all()
    items_raw: list[HistoryItemOut] = []
    for row in rows:
        if start_date or end_date:
            if row.created_at is None:
                continue
            try:
                cd = row.created_at.date().isoformat()
            except Exception:
                continue
            if start_date and cd < start_date:
                continue
            if end_date and cd > end_date:
                continue
        item = _history_row_to_item(row)
        if item is None:
            continue
        if risk_level and item.risk_level != risk_level:
            continue
        items_raw.append(item)
    total = len(items_raw)
    page = max(1, page)
    page_size = max(1, min(page_size, 100))
    start = (page - 1) * page_size
    return HistoryListOut(list=items_raw[start : start + page_size], total=total)


@router.get("/results/{public_id}", response_model=AnalyzeResponse)
def get_saved_analyze_result(
    public_id: str,
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[User, Depends(require_permission("analyze:run"))],
) -> AnalyzeResponse:
    """按 content_id（public_id）读取已保存的识别结果。"""
    row = (
        db.query(Content)
        .options(joinedload(Content.result))
        .filter(Content.public_id == public_id, Content.owner_id == user.id)
        .first()
    )
    if row is None or row.result is None:
        raise HTTPException(status_code=404, detail="记录不存在")
    base = rehydrate_standard_judgment(AnalyzeResponse.model_validate(row.result.payload))
    hr = _human_review_from_content(row)
    if hr is None:
        return base
    return base.model_copy(update={"human_review": hr})


def _purge_content_children(db: Session, content_pk: int) -> None:
    """删除与 content 主键关联的子表行，避免部分库未生效 ON DELETE CASCADE 时 commit 失败。"""
    db.query(AnalyzeJob).filter(AnalyzeJob.content_id == content_pk).delete(synchronize_session=False)
    db.query(AnalyzeResult).filter(AnalyzeResult.content_id == content_pk).delete(synchronize_session=False)
    db.query(ContentFavorite).filter(ContentFavorite.content_id == content_pk).delete(synchronize_session=False)


def _delete_content_row(db: Session, row: Content) -> None:
    _purge_content_children(db, row.id)
    db.delete(row)


def _delete_analyze_history_by_public_ids(
    db: Session, user: User, public_ids: list[str]
) -> dict[str, Any]:
    ids_in = [str(x).strip() for x in (public_ids or []) if str(x).strip()]
    requested = len(ids_in)
    deleted = 0
    for pid in ids_in:
        row = (
            db.query(Content)
            .filter(Content.public_id == pid, Content.owner_id == user.id)
            .first()
        )
        if row is not None:
            _delete_content_row(db, row)
            deleted += 1
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        logger.exception("delete analyze history integrity error")
        raise HTTPException(
            status_code=409,
            detail="删除失败：记录仍被其它数据引用，请稍后重试或联系管理员",
        ) from None
    except Exception:
        db.rollback()
        logger.exception("delete analyze history commit failed")
        raise HTTPException(status_code=500, detail="删除失败，请稍后重试") from None
    if requested > 0 and deleted == 0:
        raise HTTPException(status_code=404, detail="未找到可删除的识别记录")
    return {"ok": True, "deleted": deleted, "requested": requested}


@router.post("/history/delete")
def delete_analyze_history_items_post(
    body: DeleteHistoryBody,
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[User, Depends(require_permission("analyze:run"))],
) -> dict[str, Any]:
    """按 content_id（public_id）删除历史；使用 POST+JSON，避免部分环境对 DELETE+body 支持不佳。"""
    return _delete_analyze_history_by_public_ids(db, user, body.content_ids)


@router.delete("/history")
def delete_analyze_history_items(
    body: DeleteHistoryBody,
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[User, Depends(require_permission("analyze:run"))],
) -> dict[str, Any]:
    """按 content_id 删除（兼容旧客户端）；优先使用 POST /analyze/history/delete。"""
    return _delete_analyze_history_by_public_ids(db, user, body.content_ids)


@router.delete("/history/all")
def delete_all_analyze_history(
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[User, Depends(require_permission("analyze:run"))],
) -> dict:
    """清空当前用户全部识别内容记录。"""
    rows = db.query(Content).filter(Content.owner_id == user.id).all()
    for row in rows:
        _delete_content_row(db, row)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        logger.exception("delete all analyze history integrity error")
        raise HTTPException(
            status_code=409,
            detail="清空失败：部分记录仍被引用，请稍后重试或联系管理员",
        ) from None
    except Exception:
        db.rollback()
        logger.exception("delete all analyze history commit failed")
        raise HTTPException(status_code=500, detail="清空失败，请稍后重试") from None
    return {"ok": True}


@router.post("/text", response_model=AnalyzeResponse)
def analyze_text(
    request: Request,
    payload: TextAnalyzeRequest,
    user: Annotated[User, Depends(require_permission("analyze:run"))],
    db: Annotated[Session, Depends(get_db)],
) -> AnalyzeResponse:
    redis_client = getattr(request.app.state, "redis_client", None)
    cache_key = _infer_cache_key("text", payload.text)
    if not payload.skip_infer_cache:
        cached = _get_cached(redis_client, cache_key)
        if cached:
            # 命中时沿用缓存内完整 payload（含 standard_judgment 原文），不再按当前模板重算
            ok = persist_sync_analyze(db, user.id, cached)
            return _with_persist_meta(cached, ok)
    resp = pipeline_orchestrator.analyze_text(payload.text, payload.content_id)
    resp = rehydrate_standard_judgment(resp)
    ok = persist_sync_analyze(db, user.id, resp)
    if not payload.skip_infer_cache:
        _set_cached(redis_client, cache_key, resp)
    return _with_persist_meta(resp, ok)


@router.post("/image", response_model=AnalyzeResponse)
async def analyze_image(
    request: Request,
    user: Annotated[User, Depends(require_permission("analyze:run"))],
    db: Annotated[Session, Depends(get_db)],
    file: UploadFile = File(...),
    content_id: str | None = Form(default=None),
    skip_infer_cache: bool = Form(default=False),
) -> AnalyzeResponse:
    redis_client = getattr(request.app.state, "redis_client", None)
    image_path, digest = await save_upload_validated(file)
    cache_key = _infer_cache_key("img", digest)
    if not skip_infer_cache:
        cached = _get_cached(redis_client, cache_key)
        if cached:
            ok = persist_sync_analyze(db, user.id, cached)
            return _with_persist_meta(cached, ok)
    try:
        resp = pipeline_orchestrator.analyze_image(image_path, content_id)
    finally:
        try:
            image_path.unlink(missing_ok=True)
            if image_path.parent.is_dir() and not any(image_path.parent.iterdir()):
                image_path.parent.rmdir()
        except OSError:
            pass
    resp = rehydrate_standard_judgment(resp)
    ok = persist_sync_analyze(db, user.id, resp)
    if not skip_infer_cache:
        _set_cached(redis_client, cache_key, resp)
    return _with_persist_meta(resp, ok)


@router.post("/mixed", response_model=AnalyzeResponse)
async def analyze_mixed(
    request: Request,
    user: Annotated[User, Depends(require_permission("analyze:run"))],
    db: Annotated[Session, Depends(get_db)],
    text: str = Form(default=""),
    file: UploadFile = File(...),
    content_id: str | None = Form(default=None),
    skip_infer_cache: bool = Form(default=False),
) -> AnalyzeResponse:
    redis_client = getattr(request.app.state, "redis_client", None)
    image_path, digest = await save_upload_validated(file)
    payload_for_key = f"{text}\n{digest}"
    cache_key = _infer_cache_key("mix", payload_for_key)
    if not skip_infer_cache:
        cached = _get_cached(redis_client, cache_key)
        if cached:
            ok = persist_sync_analyze(db, user.id, cached)
            return _with_persist_meta(cached, ok)
    try:
        resp = pipeline_orchestrator.analyze_mixed(text, image_path, content_id)
    finally:
        try:
            image_path.unlink(missing_ok=True)
            if image_path.parent.is_dir() and not any(image_path.parent.iterdir()):
                image_path.parent.rmdir()
        except OSError:
            pass
    resp = rehydrate_standard_judgment(resp)
    ok = persist_sync_analyze(db, user.id, resp)
    if not skip_infer_cache:
        _set_cached(redis_client, cache_key, resp)
    return _with_persist_meta(resp, ok)
