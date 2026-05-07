from __future__ import annotations

from enum import Enum
from typing import Any

from backend.app.core.config import settings
from pydantic import BaseModel, Field

from backend.app.schemas.standard_judgment import StandardJudgmentOutput


class Modality(str, Enum):
    text = "text"
    image = "image"
    mixed = "mixed"


class TextAnalyzeRequest(BaseModel):
    text: str = Field(..., min_length=1, max_length=settings.max_text_chars)
    content_id: str | None = Field(
        default=None,
        description="可选：指定本次内容的 public_id；不传则服务端生成 UUID",
    )
    skip_infer_cache: bool = Field(
        default=False,
        description="为 true 时不读不写 Redis 推理缓存（示例一键体验等，避免长期命中旧结果）",
    )


class OcrItem(BaseModel):
    text: str
    score: float | None = None


class OcrResult(BaseModel):
    text: str = ""
    items: list[OcrItem] = Field(default_factory=list)
    available: bool = True
    error: str | None = None


class BertLabelResult(BaseModel):
    name: str
    hit: bool
    prob: float


class BertResult(BaseModel):
    available: bool = True
    error: str | None = None
    risk_level: str = "未知"
    total_score_pct: float = 0.0
    score_mean_prob_pct: float = 0.0
    score_max_prob_pct: float = 0.0
    hit_rate_pct: float = 0.0
    hit_count: int = 0
    num_chunks: int = 0
    char_len: int = 0
    pred: list[int] = Field(default_factory=list)
    pred_dim_hint: str = ""
    label_names: list[str] = Field(default_factory=list)
    predicted_label_names: list[str] = Field(default_factory=list)
    per_label: list[BertLabelResult] = Field(default_factory=list)
    probs: list[float] = Field(default_factory=list)
    logits: list[float] = Field(default_factory=list)
    prediction_summary_zh: str = ""


class LlmResult(BaseModel):
    available: bool = True
    error: str | None = None
    risk_level: str = "未知"
    comprehensive_score: float = 0.0
    judgment_basis: str = ""
    why_sound: str = ""
    why_risky: str = ""
    reader_actions: str = ""
    features: list[str] = Field(default_factory=list)
    raw_output: str | None = None
    logical_fallacy: str = ""
    scientific_error: str = ""


class FinalResult(BaseModel):
    risk_level: str
    score: float
    basis: str
    features: list[str] = Field(default_factory=list)


class HumanReviewOut(BaseModel):
    """人工复核摘要（读取已保存结果时附加；不改变 analyze_results 内模型原 payload）。"""

    status: str = Field(..., description="Content.review_status：none/pending/claimed/approved/rejected")
    summary_zh: str = Field("", description="面向用户的一句话说明")
    note: str | None = Field(None, description="审核意见，对应 review_note")
    reviewed_at: str | None = Field(None, description="复核完成时间 ISO8601，未审结则为 null")


class AnalyzeResponse(BaseModel):
    content_id: str
    modality: Modality
    input_text: str = ""
    ocr: OcrResult = Field(default_factory=OcrResult)
    bert: BertResult = Field(default_factory=BertResult)
    llm: LlmResult = Field(default_factory=LlmResult)
    final: FinalResult
    standard_judgment: StandardJudgmentOutput
    meta: dict[str, Any] = Field(default_factory=dict)
    human_review: HumanReviewOut | None = Field(
        default=None,
        description="人工复核状态；仅 GET 已保存结果等场景由服务端写入",
    )
