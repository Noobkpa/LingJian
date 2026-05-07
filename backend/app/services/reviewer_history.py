"""当前审核员已处理记录列表（/review/history 与 /users/me/review-history 共用）。"""
from __future__ import annotations

from sqlalchemy import func, or_
from sqlalchemy.orm import Session, joinedload

from backend.app.models.orm import Content, ReviewStatus, User
from backend.app.services.review_list import content_row_to_list_item, format_datetime_shanghai


def reviewer_history_list(
    db: Session,
    user: User,
    *,
    page: int = 1,
    page_size: int = 20,
    audit_result: str | None = None,
) -> dict:
    q = (
        db.query(Content)
        .options(joinedload(Content.result), joinedload(Content.owner))
        .filter(Content.reviewer_id == user.id)
        .filter(
            or_(
                Content.review_status == ReviewStatus.approved.value,
                Content.review_status == ReviewStatus.rejected.value,
            )
        )
    )
    if audit_result == "pseudo_science":
        q = q.filter(Content.review_status == ReviewStatus.rejected.value)
    elif audit_result == "dismiss":
        q = q.filter(Content.review_status == ReviewStatus.approved.value)

    total = q.count()
    rows = (
        q.order_by(
            func.coalesce(Content.reviewed_at, Content.updated_at, Content.created_at).desc()
        )
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )
    out: list[dict] = []
    for r in rows:
        row_ui = content_row_to_list_item(r)
        ts = r.reviewed_at or r.updated_at
        audit_time = format_datetime_shanghai(ts)
        audit_result_ui = (
            "pseudo_science"
            if r.review_status == ReviewStatus.rejected.value
            else "dismiss"
        )
        out.append(
            {
                "audit_id": r.id,
                "content_id": r.public_id,
                "risk_level": row_ui.get("risk_level", "low"),
                "audit_result": audit_result_ui,
                "audit_opinion": (r.review_note or "").strip(),
                "audit_time": audit_time,
            }
        )
    return {"total": total, "page": page, "page_size": page_size, "list": out}
