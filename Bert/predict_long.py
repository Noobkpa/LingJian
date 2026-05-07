"""
长文本多标签预测：按字分块（默认每块≤512 字），每块经 BERT 后对 logits 逐维取 max 聚合，
再应用 thresholds.json（或 --threshold）得到六维 0/1 预测；
并输出百分制 total_score_pct（六维 sigmoid 的均值与最大值加权融合×100，0–100）与 hit_rate_pct。
支持 --lines_file：纯文本每行一条，终端直接打印得分表。
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except (OSError, ValueError):
        pass

import numpy as np
import torch
from tqdm import tqdm
from transformers import AutoModelForSequenceClassification, AutoTokenizer

from long_text import aggregate_logits_max, chunk_by_chars
from thresholding import apply_logits_threshold, load_inference_threshold


def load_jsonl(path: Path) -> list[dict]:
    rows = []
    with path.open(encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            rows.append(json.loads(line))
    return rows


LABEL_NAMES = [
    "绝对化用语",
    "术语堆砌",
    "虚假疗效",
    "标点异常",
    "数据篡改",
    "权威伪造",
]

_NUM_LABELS = len(LABEL_NAMES)
# 终端表头：六维缩写（与 LABEL_NAMES 顺序一致）
_DIM_HINT = "绝术虚标数权"


def _pred_dim_hint(pred: list[int]) -> str:
    return "".join(_DIM_HINT[j] if pred[j] else "-" for j in range(_NUM_LABELS))


def _sigmoid_np(x: np.ndarray) -> np.ndarray:
    x = np.clip(x.astype(np.float64), -500.0, 500.0)
    return 1.0 / (1.0 + np.exp(-x))


# 总得分：纯六维概率均值往往只有十几～三十多，百分制观感偏低；用「均值+峰值」融合更贴近「任一类很强则分高」。
_TOTAL_SCORE_MEAN_WEIGHT = 0.3
_TOTAL_SCORE_MAX_WEIGHT = 0.7


def aggregate_scores_from_logits(logits: list[float] | np.ndarray) -> dict:
    """
    由聚合后的 logits 得到百分制指标（与阈值无关，便于对比不同阈值下的「强度」）。
    - total_score_pct: 0.3×mean(sigmoid) + 0.7×max(sigmoid)，再 ×100 并封顶 100；
      比单纯六维均值更能反映「至少有一类风险维很确定」的情况。
    """
    lg = np.asarray(logits, dtype=np.float64).reshape(-1)
    probs = _sigmoid_np(lg)
    mean_p = float(np.mean(probs))
    max_p = float(np.max(probs))
    blend = _TOTAL_SCORE_MEAN_WEIGHT * mean_p + _TOTAL_SCORE_MAX_WEIGHT * max_p
    total = min(100.0, blend * 100.0)
    return {
        "probs": probs.astype(float).tolist(),
        "total_score_pct": round(total, 1),
        "score_mean_prob_pct": round(mean_p * 100.0, 1),
        "score_max_prob_pct": round(max_p * 100.0, 1),
    }


@torch.no_grad()
def forward_one_chunk(
    model,
    tokenizer,
    text: str,
    max_length: int,
    device: torch.device,
) -> torch.Tensor:
    enc = tokenizer(
        text,
        max_length=max_length,
        padding="max_length",
        truncation=True,
        return_tensors="pt",
    )
    enc = {k: v.to(device) for k, v in enc.items()}
    return model(**enc).logits.squeeze(0).float()


def predict_long(
    model,
    tokenizer,
    text: str,
    device: torch.device,
    *,
    max_length: int,
    chunk_chars: int,
    chunk_overlap: int,
    threshold: float | np.ndarray,
) -> dict:
    chunks = chunk_by_chars(text, max_chars=chunk_chars, overlap=chunk_overlap)
    if not chunks:
        chunks = [""]
    logits_list = [forward_one_chunk(model, tokenizer, ch, max_length, device) for ch in chunks]
    agg = aggregate_logits_max(logits_list)
    lg = agg.cpu().numpy().tolist()
    y = apply_logits_threshold(
        np.asarray(lg, dtype=np.float64).reshape(1, -1),
        threshold if isinstance(threshold, np.ndarray) else float(threshold),
    )[0].astype(int).tolist()
    agg_scores = aggregate_scores_from_logits(lg)
    hit = int(sum(y))
    hit_rate_pct = round(100.0 * hit / _NUM_LABELS, 1)
    return {
        "num_chunks": len(chunks),
        "char_len": len(text.strip()),
        "logits": lg,
        "pred": y,
        "probs": agg_scores["probs"],
        "total_score_pct": agg_scores["total_score_pct"],
        "score_mean_prob_pct": agg_scores["score_mean_prob_pct"],
        "score_max_prob_pct": agg_scores["score_max_prob_pct"],
        "hit_rate_pct": hit_rate_pct,
        "hit_count": hit,
    }


def main():
    base = Path(__file__).resolve().parent
    p = argparse.ArgumentParser(description="长文本分块 + logits max 多标签预测")
    p.add_argument(
        "--checkpoint",
        type=str,
        default=str(base / "bert_chinese_multilabel_out" / "best"),
    )
    p.add_argument("--text", type=str, default="")
    p.add_argument("--text_file", type=str, default="", help="UTF-8 全文路径")
    p.add_argument(
        "--lines_file",
        type=str,
        default="",
        help="UTF-8 文本：非空行逐条推理，终端打印得分表（与 --jsonl_in / --text / --text_file 互斥）",
    )
    p.add_argument(
        "--lines_preview",
        type=int,
        default=56,
        help="与 --lines_file 合用：原文预览最大字符数",
    )
    p.add_argument("--jsonl_in", type=str, default="", help="每行含 text 的 JSONL，写出预测")
    p.add_argument("--jsonl_out", type=str, default="", help="与 --jsonl_in 同用")
    p.add_argument("--max_length", type=int, default=512, help="每块 tokenizer 上限（≤512）")
    p.add_argument("--chunk_chars", type=int, default=512, help="按字分块最大长度")
    p.add_argument("--chunk_overlap", type=int, default=0)
    p.add_argument(
        "--threshold",
        type=float,
        default=None,
        help="覆盖 thresholds.json 的全局 logit 阈值",
    )
    args = p.parse_args()

    has_jsonl = bool(args.jsonl_in)
    has_lines = bool(args.lines_file.strip())
    has_single = bool((args.text or "").strip()) or bool(args.text_file.strip())
    n_modes = sum([has_jsonl, has_lines, has_single])
    if n_modes > 1:
        raise SystemExit(
            "输入方式请只选一种：--jsonl_in、--lines_file、或 --text / --text_file"
        )
    if n_modes == 0:
        raise SystemExit("请提供 --jsonl_in、--lines_file、--text 或 --text_file")

    if args.max_length > 512:
        raise SystemExit("bert-base-chinese 的 max_position_embeddings 为 512，请勿把 --max_length 调大。")

    ckpt = Path(args.checkpoint)
    if not (ckpt / "config.json").is_file():
        raise FileNotFoundError(f"未找到 checkpoint: {ckpt}")

    th = args.threshold if args.threshold is not None else load_inference_threshold(ckpt)
    if th is None:
        th = 0.0

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    tokenizer = AutoTokenizer.from_pretrained(str(ckpt))
    model = AutoModelForSequenceClassification.from_pretrained(str(ckpt))
    model.to(device)
    model.eval()

    def one(text: str) -> dict:
        return predict_long(
            model,
            tokenizer,
            text,
            device,
            max_length=args.max_length,
            chunk_chars=args.chunk_chars,
            chunk_overlap=args.chunk_overlap,
            threshold=th,
        )

    if args.jsonl_in:
        if not args.jsonl_out:
            raise SystemExit("使用 --jsonl_in 时必须指定 --jsonl_out")
        rows = load_jsonl(Path(args.jsonl_in))
        out_path = Path(args.jsonl_out)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        with out_path.open("w", encoding="utf-8") as fout:
            for row in tqdm(rows, desc="predict_long", unit="line"):
                t = row.get("text")
                if not isinstance(t, str) or not t.strip():
                    continue
                pr = one(t)
                o = dict(row)
                o["pred_long"] = pr["pred"]
                o["model_logits_long"] = pr["logits"]
                o["model_probs_long"] = pr["probs"]
                o["total_score_pct"] = pr["total_score_pct"]
                o["score_mean_prob_pct"] = pr["score_mean_prob_pct"]
                o["score_max_prob_pct"] = pr["score_max_prob_pct"]
                o["hit_rate_pct"] = pr["hit_rate_pct"]
                o["hit_count"] = pr["hit_count"]
                o["num_chunks"] = pr["num_chunks"]
                fout.write(json.dumps(o, ensure_ascii=False) + "\n")
        print(f"已写入 {out_path.resolve()}")
        return

    if has_lines:
        lp = Path(args.lines_file.strip())
        if not lp.is_file():
            raise FileNotFoundError(f"未找到 --lines_file: {lp}")
        pairs: list[tuple[int, str]] = []
        for lineno, raw in enumerate(lp.read_text(encoding="utf-8").splitlines(), 1):
            t = raw.strip()
            if t:
                pairs.append((lineno, t))
        if not pairs:
            raise SystemExit(f"{lp} 无非空行")
        prev = max(8, args.lines_preview)
        print(
            f"checkpoint: {ckpt.resolve()}  阈值: {th}  设备: {device}  共 {len(pairs)} 条"
        )
        legend = " | ".join(f"{_DIM_HINT[i]}={LABEL_NAMES[i]}" for i in range(_NUM_LABELS))
        print(f"六维缩写 {_DIM_HINT} → {legend}")
        print("-" * 120)
        print(
            f"{'行号':>4}  {'总得分':>6}  {'命中%':>6}  {'六维':^6}  {'命中标签':<24}  原文（前{prev}字）"
        )
        print("-" * 120)
        for lineno, text in tqdm(pairs, desc="lines_file", unit="line"):
            pr = one(text)
            hint = _pred_dim_hint(pr["pred"])
            tags = "、".join(LABEL_NAMES[j] for j, v in enumerate(pr["pred"]) if v) or "-"
            tail = "…" if len(text) > prev else ""
            pv = text[:prev] + tail
            print(
                f"{lineno:4d}  {pr['total_score_pct']:6.1f}  {pr['hit_rate_pct']:5.1f}%  "
                f"[{hint}]  {tags[:24]:<24}  {pv}"
            )
        print("-" * 120)
        return

    body = args.text
    if args.text_file:
        body = Path(args.text_file).read_text(encoding="utf-8")
    if not body.strip():
        raise SystemExit("请提供 --text、--text_file 或 --jsonl_in")

    out = one(body)
    on = "、".join(LABEL_NAMES[i] for i, v in enumerate(out["pred"]) if v) or "(无)"
    print(f"字符数: {out['char_len']}  分块数: {out['num_chunks']}")
    print(
        f"总得分: {out['total_score_pct']}/100（0.3×六维概率均值 + 0.7×峰值维概率，再×100；与阈值无关）"
    )
    print(
        f"  分解: 均值项 {out['score_mean_prob_pct']}/100  峰值项 {out['score_max_prob_pct']}/100"
    )
    print(
        f"命中占比: {out['hit_rate_pct']}%（{out['hit_count']}/{_NUM_LABELS} 维预测为 1）"
    )
    print(f"预测: {on}")
    print(f"probs: {json.dumps(out['probs'], ensure_ascii=False)}")
    print(f"logits: {json.dumps(out['logits'], ensure_ascii=False)}")


if __name__ == "__main__":
    main()
