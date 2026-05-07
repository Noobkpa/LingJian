"""管理端统计。"""
from __future__ import annotations

from datetime import date, timedelta
from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from backend.app.core.deps import get_db, require_permission
from backend.app.models.orm import AnalyzeResult, Content, ReviewStatus, User
from backend.app.services.review_list import _ui_risk_from_payload, model_flags_problem_from_payload

router = APIRouter(prefix="/admin/stats", tags=["admin"])


def _audit_accuracy_over_reviewed(db: Session) -> tuple[float | None, int]:
    """已终审样本上：与列表/审核端一致的风险档位 vs 人工结论是否一致。

    - 人工 rejected = 认定为伪科普；approved = 不认定伪科普。
    - 模型侧取 standard_judgment → final → bert 归一后的 high/middle/low，
      其中 high/middle 视为「模型倾向有问题」，与 rejected 对齐为一致。
    """
    rows = (
        db.query(Content, AnalyzeResult)
        .join(AnalyzeResult, AnalyzeResult.content_id == Content.id)
        .filter(
            Content.review_status.in_(
                [ReviewStatus.approved.value, ReviewStatus.rejected.value]
            )
        )
        .all()
    )
    if not rows:
        return None, 0
    agree = 0
    for _c, ar in rows:
        payload = ar.payload or {}
        model_pos = model_flags_problem_from_payload(payload)
        human_expect_fake = _c.review_status == ReviewStatus.rejected.value
        if model_pos == human_expect_fake:
            agree += 1
    n = len(rows)
    return round(100.0 * agree / n, 1), n


@router.get("/overview")
def overview(
    db: Annotated[Session, Depends(get_db)],
    _: Annotated[User, Depends(require_permission("admin:stats"))],
) -> dict:
    user_count = db.query(User).count()
    content_count = db.query(Content).count()
    result_count = db.query(AnalyzeResult).count()
    acc_pct, acc_n = _audit_accuracy_over_reviewed(db)
    return {
        "users": user_count,
        "contents": content_count,
        "analyze_results": result_count,
        "accuracy_percent": acc_pct,
        "accuracy_review_count": acc_n,
    }


@router.get("/risk_buckets")
def risk_buckets(
    db: Annotated[Session, Depends(get_db)],
    _: Annotated[User, Depends(require_permission("admin:stats"))],
) -> dict:
    rows = db.query(AnalyzeResult).all()
    buckets = {"高": 0, "中": 0, "低": 0}
    for r in rows:
        ui = _ui_risk_from_payload(r.payload or {})
        label = {"high": "高", "middle": "中", "low": "低"}.get(ui, "低")
        buckets[label] = buckets.get(label, 0) + 1
    return {"buckets": buckets, "total": len(rows)}


@router.get("/daily")
def daily_counts(
    db: Annotated[Session, Depends(get_db)],
    _: Annotated[User, Depends(require_permission("admin:stats"))],
    days: int = 7,
) -> dict:
    """按分析结果创建日期粗略聚合（SQLite/MySQL 通用：内存分组）。"""
    today = date.today()
    start = today - timedelta(days=max(1, min(days, 90)) - 1)
    rows = db.query(AnalyzeResult).all()
    series: dict[str, int] = {}
    for r in rows:
        created = getattr(r, "created_at", None)
        if created is None:
            continue
        d = created.date()
        if d < start:
            continue
        key = d.isoformat()
        series[key] = series.get(key, 0) + 1
    return {"series": series}


@router.get("/model-runtime")
def model_runtime_today(
    db: Annotated[Session, Depends(get_db)],
    _: Annotated[User, Depends(require_permission("admin:stats"))],
) -> dict:
    """今日识别次数（按 analyze_results 创建日）与今日样本平均整链耗时（payload.meta.elapsed_ms）。"""
    today = date.today()
    rows = db.query(AnalyzeResult).all()
    today_calls = 0
    elapsed_ms_list: list[float] = []
    for r in rows:
        created = getattr(r, "created_at", None)
        if created is None:
            continue
        if created.date() != today:
            continue
        today_calls += 1
        payload = r.payload or {}
        meta = payload.get("meta") or {}
        ms = meta.get("elapsed_ms")
        if isinstance(ms, (int, float)) and ms > 0:
            elapsed_ms_list.append(float(ms))

    avg_elapsed_sec: float | None = None
    if elapsed_ms_list:
        avg_elapsed_sec = round(sum(elapsed_ms_list) / len(elapsed_ms_list) / 1000.0, 1)

    return {
        "today_calls": today_calls,
        "avg_elapsed_sec": avg_elapsed_sec,
        "elapsed_samples": len(elapsed_ms_list),
    }
