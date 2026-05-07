"""面向前端的固定研判 JSON 结构（与系统设计文档一致）。"""
from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

StandardRiskLevel = Literal["高", "中", "低"]


class StandardJudgmentOutput(BaseModel):
    """多模态伪科普识别 — 标准输出块（嵌于 AnalyzeResponse.standard_judgment）。"""

    content_id: str = Field(..., description="内容唯一标识，与本次请求/内容一致")
    risk_level: StandardRiskLevel = Field(..., description="风险等级：高 / 中 / 低")
    comprehensive_score: float = Field(
        ...,
        ge=0,
        le=100,
        description="综合风险得分（可与 BERT 总分对齐），越高风险越大",
    )
    logical_fallacy: str = Field(
        ...,
        description="逻辑谬误或不当推论类型说明，如因果谬误、数据篡改等",
    )
    scientific_error: str = Field(
        ...,
        description="科学事实错误点及正确方向说明；无充分依据时给出保守说明",
    )
    core_features: list[str] = Field(
        default_factory=list,
        description="伪科普/高风险特征标签集合",
    )
    judgment_basis: str = Field(..., description="综合判定依据，解释风险等级与得分")
    why_sound: str = Field(
        default="",
        description="相对可信或为何不直接否定的说明，面向普通读者",
    )
    why_risky: str = Field(
        default="",
        description="具体问题与风险来源的叙事化说明，面向普通读者",
    )
    reader_actions: str = Field(
        default="",
        description="读者可执行的核实与防护建议",
    )
    infer_time: str = Field(
        ...,
        description="服务端完成推理的本地时间戳，格式 YYYY-MM-DD HH:MM:SS",
    )
