from __future__ import annotations

import uuid
from pathlib import Path
from typing import Any

from backend.app.schemas.analyze import (
    AnalyzeResponse,
    BertResult,
    FinalResult,
    LlmResult,
    Modality,
    OcrResult,
)
from backend.app.services.bert_service import bert_service
from backend.app.services.infer_admin_settings import (
    get_infer_bundle,
    resolve_effective_prompt_scene,
)
from backend.app.services.llm_service import LlmService, llm_service
from backend.app.services.ocr_service import ocr_service
from backend.app.services.standard_judgment_builder import (
    build_standard_judgment,
    format_infer_time,
    infer_completed_at,
)
from backend.app.services.text_utils import join_nonempty


class PipelineService:
    def analyze_text(self, text: str, content_id: str | None = None) -> AnalyzeResponse:
        return self._run(Modality.text, content_id=content_id, input_text=text, image_path=None)

    def analyze_image(self, image_path: Path, content_id: str | None = None) -> AnalyzeResponse:
        return self._run(Modality.image, content_id=content_id, input_text="", image_path=image_path)

    def analyze_mixed(
        self, text: str, image_path: Path, content_id: str | None = None
    ) -> AnalyzeResponse:
        return self._run(Modality.mixed, content_id=content_id, input_text=text, image_path=image_path)

    @staticmethod
    def _final_from(bert: BertResult, llm: LlmResult) -> FinalResult:
        if llm.risk_level != "未知" or llm.judgment_basis:
            return FinalResult(
                risk_level=llm.risk_level,
                score=float(llm.comprehensive_score),
                basis=llm.judgment_basis,
                features=llm.features,
            )
        return FinalResult(
            risk_level=f"{bert.risk_level}风险" if bert.risk_level != "未知" else "未知",
            score=round(float(bert.total_score_pct), 1),
            basis=bert.prediction_summary_zh or bert.error or "",
            features=bert.predicted_label_names,
        )

    def _run(
        self,
        modality: Modality,
        *,
        content_id: str | None,
        input_text: str,
        image_path: Path | None,
    ) -> AnalyzeResponse:
        resolved_content_id = content_id or uuid.uuid4().hex
        ocr = OcrResult()
        if image_path is not None:
            # Windows 下 Paddle 与 Torch 同进程使用时需要先装载 Torch DLL，
            # 否则先 import paddle 后再 import torch 可能触发 shm.dll 依赖错误。
            try:
                import torch  # noqa: F401
            except Exception:
                pass
            ocr = ocr_service.extract(image_path)
        merged_text = join_nonempty([input_text, ocr.text])
        if not merged_text:
            bert = BertResult(available=False, error="没有可用于识别的文本", risk_level="未知")
            completed_at = infer_completed_at()
            infer_ts = format_infer_time(completed_at)
            basis = "未提供可用于识别的文本，未执行 BERT/LLM 研判。"
            z = "未提供可分析的正文，系统无法评价其科学性与论证质量。"
            llm = LlmResult(
                available=False,
                error="没有可用于识别的文本",
                risk_level="未知",
                comprehensive_score=0.0,
                judgment_basis=basis,
                why_sound=z,
                why_risky=z,
                reader_actions="请重新提交含正文的识别请求；若仅含图片请使用图片或图文混合识别。",
                raw_output=LlmService._canonical_llm_json(
                    content_id=resolved_content_id,
                    infer_time_str=infer_ts,
                    risk_normalized="未知",
                    comprehensive_score=0.0,
                    logical_fallacy="无",
                    scientific_error="无",
                    core_features=[],
                    judgment_basis=basis,
                    why_sound=z,
                    why_risky=z,
                    reader_actions="请重新提交含正文的识别请求；若仅含图片请使用图片或图文混合识别。",
                ),
                logical_fallacy="无",
                scientific_error="无",
            )
            final = self._final_from(bert, llm)
            completed_at = infer_completed_at()
            standard_judgment = build_standard_judgment(
                content_id=resolved_content_id,
                bert=bert,
                llm=llm,
                final=final,
                completed_at=completed_at,
                source_text="",
            )
            return AnalyzeResponse(
                content_id=resolved_content_id,
                modality=modality,
                input_text=merged_text,
                ocr=ocr,
                bert=bert,
                llm=llm,
                final=final,
                standard_judgment=standard_judgment,
                meta={"image_path": str(image_path) if image_path else None},
            )
        bert = bert_service.predict(merged_text)
        completed_at = infer_completed_at()
        infer_ts = format_infer_time(completed_at)
        bundle = get_infer_bundle()
        scene_eff, scene_src, scene_scores = resolve_effective_prompt_scene(
            bundle, merged_text, bert
        )
        llm = llm_service.analyze(
            merged_text,
            bert,
            content_id=resolved_content_id,
            infer_time_str=infer_ts,
            preferred_prompt_scene=scene_eff,
            infer_bundle=bundle,
        )
        final = self._final_from(bert, llm)
        standard_judgment = build_standard_judgment(
            content_id=resolved_content_id,
            bert=bert,
            llm=llm,
            final=final,
            completed_at=completed_at,
            source_text=merged_text,
        )
        meta: dict[str, Any] = {"image_path": str(image_path) if image_path else None}
        meta["prompt_scene"] = scene_eff
        meta["prompt_scene_source"] = scene_src
        if scene_scores is not None:
            meta["prompt_scene_scores"] = scene_scores
        return AnalyzeResponse(
            content_id=resolved_content_id,
            modality=modality,
            input_text=merged_text,
            ocr=ocr,
            bert=bert,
            llm=llm,
            final=final,
            standard_judgment=standard_judgment,
            meta=meta,
        )


pipeline_service = PipelineService()
