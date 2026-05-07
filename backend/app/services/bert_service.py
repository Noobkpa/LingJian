from __future__ import annotations

import sys
import json
from pathlib import Path
from threading import Lock

import numpy as np

from backend.app.core.config import PROJECT_ROOT, settings
from backend.app.schemas.analyze import BertLabelResult, BertResult

BERT_DIR = PROJECT_ROOT / "Bert"
if str(BERT_DIR) not in sys.path:
    sys.path.insert(0, str(BERT_DIR))

LABEL_NAMES = [
    "绝对化用语",
    "术语堆砌",
    "虚假疗效",
    "标点异常",
    "数据篡改",
    "权威伪造",
]
_DIM_HINT = "绝术虚标数权"


def _pred_dim_hint(pred: list[int]) -> str:
    return "".join(_DIM_HINT[j] if pred[j] else "-" for j in range(len(LABEL_NAMES)))


def _load_threshold(checkpoint: Path) -> float | np.ndarray:
    path = checkpoint / "thresholds.json"
    if not path.is_file():
        return 0.0
    data = json.loads(path.read_text(encoding="utf-8"))
    if data.get("mode") == "per_label_logits":
        return np.asarray(data.get("values", []), dtype=np.float64)
    if data.get("mode") == "global_logits":
        return float(data.get("value", 0.0))
    return 0.0


def _apply_threshold(logits: np.ndarray, threshold: float | np.ndarray) -> np.ndarray:
    if isinstance(threshold, np.ndarray):
        th = threshold.reshape(1, -1)
        return (logits > th).astype(np.int64)
    return (logits > float(threshold)).astype(np.int64)


def _sigmoid(values: np.ndarray) -> np.ndarray:
    clipped = np.clip(values.astype(np.float64), -500.0, 500.0)
    return 1.0 / (1.0 + np.exp(-clipped))


def _score_from_logits(logits: np.ndarray) -> dict:
    probs = _sigmoid(logits)
    mean_prob = float(np.mean(probs))
    max_prob = float(np.max(probs))
    total = min(100.0, (0.3 * mean_prob + 0.7 * max_prob) * 100.0)
    return {
        "probs": probs.astype(float).tolist(),
        "total_score_pct": round(total, 1),
        "score_mean_prob_pct": round(mean_prob * 100.0, 1),
        "score_max_prob_pct": round(max_prob * 100.0, 1),
    }


class BertService:
    def __init__(self) -> None:
        self._model = None
        self._tokenizer = None
        self._device = None
        self._threshold = None
        self._lock = Lock()

    def _load(self) -> None:
        if self._model is not None:
            return
        with self._lock:
            if self._model is not None:
                return
            import torch
            from transformers import AutoModelForSequenceClassification, AutoTokenizer

            checkpoint = settings.bert_checkpoint
            if not (checkpoint / "config.json").is_file():
                raise FileNotFoundError(f"未找到 BERT checkpoint: {checkpoint}")
            threshold = _load_threshold(checkpoint)
            device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
            tokenizer = AutoTokenizer.from_pretrained(str(checkpoint))
            model = AutoModelForSequenceClassification.from_pretrained(str(checkpoint))
            model.to(device)
            model.eval()

            self._threshold = threshold
            self._device = device
            self._tokenizer = tokenizer
            self._model = model

    @staticmethod
    def _risk_level(score: float, hit_count: int) -> str:
        if score >= 75 or hit_count >= 4:
            return "高"
        if score >= 40 or hit_count >= 2:
            return "中"
        return "低"

    def predict(self, text: str) -> BertResult:
        try:
            self._load()
            import torch
            from long_text import aggregate_logits_max, chunk_by_chars

            assert self._model is not None
            assert self._tokenizer is not None
            assert self._device is not None
            threshold = self._threshold
            if threshold is None:
                threshold = 0.0
            chunks = chunk_by_chars(
                text,
                max_chars=settings.bert_chunk_chars,
                overlap=settings.bert_chunk_overlap,
            ) or [""]
            logits_list = []
            with torch.no_grad():
                for chunk in chunks:
                    encoded = self._tokenizer(
                        chunk,
                        max_length=settings.bert_max_length,
                        padding="max_length",
                        truncation=True,
                        return_tensors="pt",
                    )
                    encoded = {key: value.to(self._device) for key, value in encoded.items()}
                    logits_list.append(self._model(**encoded).logits.squeeze(0).float())
            agg = aggregate_logits_max(logits_list).cpu().numpy().astype(np.float64)
            pred = _apply_threshold(agg.reshape(1, -1), threshold)[0].astype(int).tolist()
            score_data = _score_from_logits(agg)
            hit_count = int(sum(pred))
            hit_rate_pct = round(100.0 * hit_count / len(LABEL_NAMES), 1)
            probs = [float(v) for v in score_data["probs"]]
            predicted_names = [LABEL_NAMES[i] for i, value in enumerate(pred) if value]
            per_label = [
                BertLabelResult(name=LABEL_NAMES[i], hit=bool(pred[i]), prob=round(probs[i], 4))
                for i in range(len(LABEL_NAMES))
            ]
            score = float(score_data["total_score_pct"])
            risk = self._risk_level(score, hit_count)
            summary_tags = "、".join(predicted_names) if predicted_names else "无"
            return BertResult(
                risk_level=risk,
                total_score_pct=score,
                score_mean_prob_pct=float(score_data["score_mean_prob_pct"]),
                score_max_prob_pct=float(score_data["score_max_prob_pct"]),
                hit_rate_pct=hit_rate_pct,
                hit_count=hit_count,
                num_chunks=len(chunks),
                char_len=len(text.strip()),
                pred=pred,
                pred_dim_hint=_pred_dim_hint(pred),
                label_names=list(LABEL_NAMES),
                predicted_label_names=predicted_names,
                per_label=per_label,
                probs=probs,
                logits=[float(v) for v in agg.tolist()],
                prediction_summary_zh=(
                    f"风险{risk}；命中标签：{summary_tags}；总得分：{round(score, 1)}/100"
                ),
            )
        except Exception as exc:
            return BertResult(available=False, error=str(exc), risk_level="未知")


bert_service = BertService()
