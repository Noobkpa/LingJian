"""多标签 logits 阈值：逐维搜索（验证集）与推理时应用。"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Union

import numpy as np
from sklearn.metrics import f1_score


def apply_logits_threshold(
    logits: np.ndarray, threshold: Union[float, int, np.ndarray]
) -> np.ndarray:
    """logits 与标量或 (num_labels,) 逐维阈值比较得到 0/1 预测。"""
    if isinstance(threshold, (float, int)):
        return (logits > float(threshold)).astype(np.int64)
    th = np.asarray(threshold, dtype=np.float64).reshape(1, -1)
    if th.shape[1] != logits.shape[1]:
        raise ValueError(f"阈值维数 {th.shape[1]} != logits 维数 {logits.shape[1]}")
    return (logits > th).astype(np.int64)


def tune_global_logits_threshold(
    y_true: np.ndarray,
    logits: np.ndarray,
    t_min: float = -3.0,
    t_max: float = 3.0,
    steps: int = 61,
) -> float:
    """单标量 logit 阈值，使验证集 macro-F1 最大。"""
    y_true = np.asarray(y_true, dtype=np.float64)
    logits = np.asarray(logits, dtype=np.float64)
    grid = np.linspace(t_min, t_max, steps)
    best_macro, best_t = -1.0, 0.0
    for t in grid:
        yp = apply_logits_threshold(logits, float(t))
        m = f1_score(y_true, yp, average="macro", zero_division=0)
        if m > best_macro:
            best_macro, best_t = m, float(t)
    return best_t


def pick_threshold_on_validation(
    y_true: np.ndarray,
    logits: np.ndarray,
    strategy: str = "global_only",
) -> tuple[str, float | np.ndarray]:
    """
    strategy:
      - global_only（默认）: 单标量 logit 阈值，验证集 macro-F1 最大；小验证集上更不易过拟合。
      - auto: 与逐维阈值比验证 macro-F1，再比完全一致率，取较优（仅作实验）。
    """
    th_global = tune_global_logits_threshold(y_true, logits)
    if strategy != "auto":
        return "global_logits", th_global
    th_per = tune_per_label_logits_thresholds(y_true, logits)
    y_g = apply_logits_threshold(logits, th_global)
    y_p = apply_logits_threshold(logits, th_per)
    macro_g = f1_score(y_true, y_g, average="macro", zero_division=0)
    macro_p = f1_score(y_true, y_p, average="macro", zero_division=0)
    exact_g = exact_match_rate(y_true, y_g)
    exact_p = exact_match_rate(y_true, y_p)
    if (macro_g, exact_g) >= (macro_p, exact_p):
        return "global_logits", th_global
    return "per_label_logits", th_per


def tune_per_label_logits_thresholds(
    y_true: np.ndarray,
    logits: np.ndarray,
    t_min: float = -4.0,
    t_max: float = 4.0,
    steps: int = 81,
) -> np.ndarray:
    """在验证集上对每一维 logit 独立网格搜索，使该维二分类 F1 最大。"""
    y_true = np.asarray(y_true, dtype=np.float64)
    logits = np.asarray(logits, dtype=np.float64)
    n_labels = y_true.shape[1]
    thresholds = np.zeros(n_labels, dtype=np.float64)
    grid = np.linspace(t_min, t_max, steps)
    for j in range(n_labels):
        yt = y_true[:, j].astype(int)
        s = logits[:, j]
        if yt.min() == yt.max():
            thresholds[j] = 0.0
            continue
        best_f1, best_t = -1.0, 0.0
        for t in grid:
            yp = (s > t).astype(int)
            f1 = f1_score(yt, yp, zero_division=0)
            if f1 > best_f1:
                best_f1, best_t = f1, t
        thresholds[j] = best_t
    return thresholds


def exact_match_rate(y_true: np.ndarray, y_pred: np.ndarray) -> float:
    y_true = np.asarray(y_true)
    y_pred = np.asarray(y_pred)
    return float(np.mean(np.all(y_true.astype(int) == y_pred.astype(int), axis=1)))


def save_threshold_config(path: Path, mode: str, value: Union[float, np.ndarray]) -> None:
    if mode == "global_logits":
        data = {"mode": mode, "value": float(value)}
    elif mode == "per_label_logits":
        arr = np.asarray(value, dtype=np.float64)
        data = {"mode": mode, "values": [float(x) for x in arr.tolist()]}
    else:
        raise ValueError(f"未知 mode: {mode}")
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def load_inference_threshold(checkpoint_dir: Path) -> Union[float, np.ndarray, None]:
    p = checkpoint_dir / "thresholds.json"
    if not p.is_file():
        return None
    data = json.loads(p.read_text(encoding="utf-8"))
    mode = data.get("mode")
    if mode == "global_logits":
        return float(data["value"])
    if mode == "per_label_logits":
        return np.array(data["values"], dtype=np.float64)
    return None


def load_thresholds_array(checkpoint_dir: Path) -> np.ndarray | None:
    """兼容旧调用：仅当为逐维时返回数组。"""
    th = load_inference_threshold(checkpoint_dir)
    if isinstance(th, np.ndarray):
        return th
    return None
