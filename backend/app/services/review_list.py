"""审核队列列表：筛选、行序列化（管理端导出与 /review/queue 共用）。"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any
from zoneinfo import ZoneInfo

from sqlalchemy import or_
from sqlalchemy.orm import Session, joinedload

from backend.app.core.config import settings
from backend.app.models.orm import AnalyzeResult, Content, ReviewStatus


def format_datetime_shanghai(dt: datetime | None) -> str:
    """将存库时间统一格式化为北京时间（与 LINGJIAN_INFER_TZ 一致，默认同 Asia/Shanghai）。"""
    if dt is None:
        return ""
    try:
        tz = ZoneInfo((settings.infer_time_zone or "Asia/Shanghai").strip() or "Asia/Shanghai")
    except Exception:
        tz = ZoneInfo("Asia/Shanghai")
    if dt.tzinfo is None:
        # 常见：SQLite 等返回无时区，按 UTC 解释后转到上海墙钟
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(tz).strftime("%Y-%m-%d %H:%M:%S")


def _ui_modality(m: str) -> str:
    return {"text": "text", "image": "image", "mixed": "mix"}.get(m, m)


def _ui_risk_from_payload(payload: dict) -> str:
    """与前端 risk_level（high/middle/low）对齐；优先 standard_judgment，缺省时从 final/bert 解析。"""
    sj = (payload or {}).get("standard_judgment") or {}
    z = str(sj.get("risk_level") or "").strip()
    zl = z.lower()
    if z == "高" or zl == "high":
        return "high"
    if z == "中" or zl in ("middle", "medium"):
        return "middle"
    if z == "低" or zl == "low":
        return "low"
    fin = (payload or {}).get("final") or {}
    fr = str(fin.get("risk_level") or "").strip()
    fl = fr.lower()
    if fr.startswith("高") or "高风险" in fr or fl == "high":
        return "high"
    if fr.startswith("中") or "中风险" in fr or fl in ("middle", "medium"):
        return "middle"
    if fr.startswith("低") or "低风险" in fr or fl == "low":
        return "low"
    bert = (payload or {}).get("bert") or {}
    br = str(bert.get("risk_level") or "").strip()
    bl = br.lower()
    if br == "高" or bl == "high":
        return "high"
    if br == "中" or bl in ("middle", "medium"):
        return "middle"
    if br == "低" or bl == "low":
        return "low"
    return "low"


def model_flags_problem_from_payload(payload: dict) -> bool:
    """与列表展示档位一致：高/中视为模型「阳性」（与人工是否认定伪科普对齐统计用）。"""
    return _ui_risk_from_payload(payload or {}) in ("high", "middle")


def _audit_ui_status(review_status: str) -> str:
    if review_status == ReviewStatus.pending.value:
        return "pending"
    if review_status in (
        ReviewStatus.approved.value,
        ReviewStatus.rejected.value,
    ):
        return "audited"
    return "pending"


def _judgment_basis_list(payload: dict) -> list[str]:
    fin = payload.get("final") or {}
    basis = fin.get("basis")
    if isinstance(basis, list):
        return [str(x) for x in basis]
    if isinstance(basis, str) and basis.strip():
        return [basis]
    sj = payload.get("standard_judgment") or {}
    lines: list[str] = []
    if sj.get("logical_fallacy"):
        lines.append(f"逻辑谬误：{sj['logical_fallacy']}")
    if sj.get("scientific_error"):
        lines.append(f"科学事实：{sj['scientific_error']}")
    if sj.get("why_sound"):
        lines.append(f"为何仍可能成立：{sj['why_sound']}")
    if sj.get("why_risky"):
        lines.append(f"为何存疑：{sj['why_risky']}")
    if sj.get("reader_actions"):
        lines.append(f"建议：{sj['reader_actions']}")
    cfs = sj.get("core_features")
    if isinstance(cfs, list) and cfs:
        lines.append(f"核心特征：{'、'.join(str(x) for x in cfs)}")
    jb = sj.get("judgment_basis") or sj.get("judgment_summary") or ""
    if isinstance(jb, str) and jb.strip():
        lines.append(f"综合依据：{jb}")
    if lines:
        return lines
    if isinstance(jb, str) and jb.strip():
        return [jb]
    return []


def _image_list_from_payload(payload: dict) -> list[dict[str, str]]:
    imgs = payload.get("images") or payload.get("image_list") or []
    out: list[dict[str, str]] = []
    if isinstance(imgs, list):
        for it in imgs:
            if isinstance(it, dict) and it.get("url"):
                out.append({"url": str(it["url"])})
            elif isinstance(it, str):
                out.append({"url": it})
    fp = payload.get("input_image_path") or payload.get("image_path")
    if isinstance(fp, str) and fp.strip() and not out:
        out.append({"url": f"/uploads/{fp.split('/')[-1]}"})
    return out


def content_row_to_list_item(r: Content) -> dict[str, Any]:
    payload = (r.result.payload if r.result else None) or {}
    sj = payload.get("standard_judgment") or {}
    fin = payload.get("final") or {}
    text = str(payload.get("input_text") or r.text_snapshot or "")
    preview = text[:300]
    score = sj.get("comprehensive_score")
    if score is None:
        score = fin.get("score", 0)
    upload_time = format_datetime_shanghai(r.created_at)
    return {
        "content_id": r.public_id,
        "content_type": _ui_modality(r.modality),
        "risk_level": _ui_risk_from_payload(payload),
        "llm_score": score,
        "content_text": preview,
        "upload_time": upload_time,
        "audit_status": _audit_ui_status(r.review_status),
        "username": r.owner.username if r.owner else "-",
        "judgment_basis": _judgment_basis_list(payload),
        "image_list": _image_list_from_payload(payload),
    }


def query_review_contents(
    db: Session,
    *,
    content_type: str | None = None,
    audit_status: str | None = None,
) -> Any:
    """构建含 AnalyzeResult 的基础查询，并按 modality / 审核状态筛选。"""
    q = (
        db.query(Content)
        .options(joinedload(Content.result), joinedload(Content.owner))
        .join(AnalyzeResult, AnalyzeResult.content_id == Content.id)
    )
    if content_type:
        mod = {"text": "text", "image": "image", "mix": "mixed"}.get(
            content_type, content_type
        )
        q = q.filter(Content.modality == mod)
    if audit_status == "pending":
        # 待终审：须已有识别结果（下方 JOIN analyze_results）且人工复核状态为 pending
        q = q.filter(Content.review_status == ReviewStatus.pending.value)
    elif audit_status == "audited":
        q = q.filter(
            or_(
                Content.review_status == ReviewStatus.approved.value,
                Content.review_status == ReviewStatus.rejected.value,
            )
        )
    return q.order_by(Content.created_at.desc())


def list_review_items_filtered(
    db: Session,
    *,
    risk_level: str | None = None,
    content_type: str | None = None,
    audit_status: str | None = None,
) -> list[dict[str, Any]]:
    """内存筛选 risk_level（基于研判 JSON），数据量大时仅适用于中等规模库。"""
    q = query_review_contents(db, content_type=content_type, audit_status=audit_status)
    rows = q.all()
    enriched = [content_row_to_list_item(r) for r in rows]
    if risk_level:
        enriched = [e for e in enriched if e["risk_level"] == risk_level]
    return enriched


def paginate_list(items: list[dict[str, Any]], page: int, page_size: int) -> tuple[list[dict[str, Any]], int]:
    total = len(items)
    if page < 1:
        page = 1
    start = (page - 1) * page_size
    return items[start : start + page_size], total
