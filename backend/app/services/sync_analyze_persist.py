"""同步 /analyze/* 的结果落库，供历史记录与个人详情查询。"""
from __future__ import annotations

import logging
from typing import Any

from sqlalchemy.orm import Session

from backend.app.models.orm import AnalyzeResult, Content, ContentStatus, ReviewStatus
from backend.app.schemas.analyze import AnalyzeResponse

logger = logging.getLogger("backend.app.sync_analyze_persist")


def review_status_after_analyze(risk_level_str: str) -> str:
    """识别完成后进入待审核队列：高/中/低均待人工复核（与批量审核列表一致）。"""
    _ = risk_level_str  # 保留参数便于调用方与后续策略扩展（如按配置自动放行）
    return ReviewStatus.pending.value


def persist_sync_analyze(db: Session, owner_id: int, resp: AnalyzeResponse) -> bool:
    """写入或更新当前用户的 Content + AnalyzeResult（幂等：按 public_id + owner）。成功返回 True。"""
    try:
        payload: dict[str, Any] = resp.model_dump(mode="json", exclude={"human_review"})
        row = (
            db.query(Content)
            .filter(Content.public_id == resp.content_id, Content.owner_id == owner_id)
            .first()
        )
        risk_label = str(resp.final.risk_level or "")
        rev = review_status_after_analyze(risk_label)
        if row is None:
            row = Content(
                public_id=resp.content_id,
                owner_id=owner_id,
                modality=resp.modality.value,
                text_snapshot=resp.input_text or None,
                status=ContentStatus.completed.value,
                review_status=rev,
            )
            db.add(row)
            db.flush()
            db.add(AnalyzeResult(content_id=row.id, payload=payload))
        else:
            row.modality = resp.modality.value
            row.text_snapshot = resp.input_text or None
            row.status = ContentStatus.completed.value
            row.review_status = rev
            existing = db.query(AnalyzeResult).filter(AnalyzeResult.content_id == row.id).first()
            if existing:
                existing.payload = payload
            else:
                db.add(AnalyzeResult(content_id=row.id, payload=payload))
        db.commit()
        return True
    except Exception:
        logger.exception(
            "persist_sync_analyze failed owner_id=%s content_id=%s", owner_id, resp.content_id
        )
        db.rollback()
        return False
