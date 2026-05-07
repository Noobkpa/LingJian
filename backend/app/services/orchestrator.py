"""Pipeline 编排：步骤级重试与降级说明写入 meta。"""
from __future__ import annotations

import logging
import time
import uuid
from pathlib import Path

from backend.app.core.exceptions import AppException
from backend.app.schemas.analyze import AnalyzeResponse, Modality
from backend.app.services.pipeline_service import pipeline_service

logger = logging.getLogger("backend.app.orchestrator")


class PipelineOrchestrator:
    """在现有 pipeline_service 外包一层：整链重试与元信息。"""

    def __init__(
        self,
        *,
        llm_retries: int = 2,
        overall_retries: int = 1,
    ) -> None:
        self._llm_retries = llm_retries
        self._overall_retries = overall_retries

    def analyze_text(self, text: str, content_id: str | None = None) -> AnalyzeResponse:
        return self._run_with_retry(Modality.text, content_id, text, None)

    def analyze_image(self, image_path: Path, content_id: str | None = None) -> AnalyzeResponse:
        return self._run_with_retry(Modality.image, content_id, "", image_path)

    def analyze_mixed(self, text: str, image_path: Path, content_id: str | None = None) -> AnalyzeResponse:
        return self._run_with_retry(Modality.mixed, content_id, text, image_path)

    def _run_with_retry(
        self,
        modality: Modality,
        content_id: str | None,
        input_text: str,
        image_path: Path | None,
    ) -> AnalyzeResponse:
        last_exc: Exception | None = None
        attempts = max(1, self._overall_retries + 1)
        for attempt in range(attempts):
            t0 = time.perf_counter()
            try:
                if modality == Modality.text:
                    resp = pipeline_service.analyze_text(input_text, content_id)
                elif modality == Modality.image:
                    resp = pipeline_service.analyze_image(image_path, content_id)  # type: ignore[arg-type]
                else:
                    resp = pipeline_service.analyze_mixed(input_text, image_path, content_id)  # type: ignore[arg-type]
                elapsed_ms = int((time.perf_counter() - t0) * 1000)
                meta = dict(resp.meta or {})
                meta.update(
                    {
                        "orchestrator_attempt": attempt + 1,
                        "elapsed_ms": elapsed_ms,
                        "request_trace": uuid.uuid4().hex[:12],
                    }
                )
                resp.meta = meta
                return resp
            except Exception as e:
                last_exc = e
                logger.warning(
                    "pipeline attempt %s/%s failed: %s",
                    attempt + 1,
                    attempts,
                    e,
                    exc_info=False,
                )
        raise AppException(
            "PIPELINE_FAILED",
            "分析流水线失败",
            status_code=502,
            detail=str(last_exc) if last_exc else None,
        )


pipeline_orchestrator = PipelineOrchestrator()
