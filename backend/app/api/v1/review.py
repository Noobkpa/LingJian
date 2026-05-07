"""审核队列与流转。"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session, joinedload

from backend.app.core.deps import get_db, require_permission
from backend.app.models.orm import Content, ReviewStatus, User
from backend.app.schemas.analyze import AnalyzeResponse
from backend.app.services.review_list import (
    list_review_items_filtered,
    paginate_list,
)
from backend.app.services.reviewer_history import reviewer_history_list
from backend.app.services.standard_judgment_builder import rehydrate_standard_judgment

router = APIRouter(prefix="/review", tags=["review"])


@router.get("/history")
def review_history(
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[User, Depends(require_permission("review:read"))],
    page: int = 1,
    page_size: int = 20,
    audit_result: str | None = None,
) -> dict:
    """当前登录审核员已处理的记录（通过 / 驳回）；支持按前端筛选。"""
    return reviewer_history_list(
        db, user, page=page, page_size=page_size, audit_result=audit_result
    )


@router.get("/queue")
def review_queue(
    db: Annotated[Session, Depends(get_db)],
    _: Annotated[User, Depends(require_permission("review:read"))],
    page: int = 1,
    page_size: int = 20,
    risk_level: str | None = None,
    content_type: str | None = None,
    audit_status: str = Query(
        "pending",
        description="pending=仅待审核；audited=仅已审；all=全部（含已审等）",
    ),
) -> dict:
    """队列默认只拉待审核；与导出接口不同，避免已审内容占满列表。"""
    if audit_status == "all":
        audit_filter: str | None = None
    elif audit_status == "audited":
        audit_filter = "audited"
    else:
        audit_filter = "pending"
    enriched = list_review_items_filtered(
        db,
        risk_level=risk_level or None,
        content_type=content_type or None,
        audit_status=audit_filter,
    )
    page_slice, total = paginate_list(enriched, page, page_size)
    pids = [x["content_id"] for x in page_slice]
    if not pids:
        return {
            "total": total,
            "page": page,
            "page_size": page_size,
            "list": page_slice,
            "items": [],
        }
    rows_db = (
        db.query(Content)
        .filter(Content.public_id.in_(pids))
        .all()
    )
    by_id = {r.public_id: r for r in rows_db}
    compact = [
        {
            "public_id": pid,
            "modality": by_id[pid].modality,
            "review_status": by_id[pid].review_status,
        }
        for pid in pids
        if pid in by_id
    ]
    return {
        "total": total,
        "page": page,
        "page_size": page_size,
        "list": page_slice,
        "items": compact,
    }


@router.get("/item/{public_id}", response_model=AnalyzeResponse)
def review_item_detail(
    public_id: str,
    db: Annotated[Session, Depends(get_db)],
    _: Annotated[User, Depends(require_permission("review:read"))],
) -> AnalyzeResponse:
    """审核员读取待审内容的完整识别结果（不限 owner，需 review:read）。"""
    c = (
        db.query(Content)
        .options(joinedload(Content.result))
        .filter(Content.public_id == public_id)
        .first()
    )
    if c is None:
        raise HTTPException(status_code=404, detail="记录不存在")
    if c.result is None:
        raise HTTPException(status_code=404, detail="尚无识别结果")
    if c.review_status != ReviewStatus.pending.value:
        raise HTTPException(status_code=404, detail="非待审核状态")
    return rehydrate_standard_judgment(AnalyzeResponse.model_validate(c.result.payload))


class ReviewActionBody(BaseModel):
    public_id: str
    action: str  # approve | reject
    audit_opinion: str | None = None


@router.post("/action")
def review_action(
    body: ReviewActionBody,
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[User, Depends(require_permission("review:write"))],
) -> dict:
    c = db.query(Content).filter(Content.public_id == body.public_id).first()
    if c is None:
        return {"ok": False, "error": "not_found"}
    if body.action == "approve":
        c.review_status = ReviewStatus.approved.value
    elif body.action == "reject":
        c.review_status = ReviewStatus.rejected.value
    else:
        return {"ok": False, "error": "invalid_action"}
    c.reviewer_id = user.id
    c.reviewed_at = datetime.now(timezone.utc)
    c.review_note = (body.audit_opinion or "").strip() or None
    db.commit()
    return {"ok": True}
