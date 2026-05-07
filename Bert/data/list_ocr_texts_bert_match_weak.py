"""
对 OCR paddleocr_format 中的文本逐条跑 predict_long，与合并时弱标签 GOLD=[0,1,1,0,0,0] 比对。
列出「六维预测与弱标签完全一致」的句子（相对该弱监督的「准确」），并写出未命中列表便于核对。

默认 OCR 目录（优先临时路径，否则用仓库内副本）：
  c:\\Users\\28079\\AppData\\Local\\Temp\\BNZ.69f2b2034ca759d1\\OCR\\paddleocr_format
  或 Bert/data/ocr_paddleocr_import

用法（在 Bert 目录）:
  python data/list_ocr_texts_bert_match_weak.py
  python data/list_ocr_texts_bert_match_weak.py --ocr_dir "D:\\path\\to\\paddleocr_format"
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

_BERT_ROOT = Path(__file__).resolve().parent.parent
if str(_BERT_ROOT) not in sys.path:
    sys.path.insert(0, str(_BERT_ROOT))

if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except (OSError, ValueError):
        pass

import torch
from transformers import AutoModelForSequenceClassification, AutoTokenizer

from merge_ocr_into_hf_train import DEFAULT_LABELS, parse_paddleocr_label_line
from predict_long import predict_long
from thresholding import load_inference_threshold

GOLD = list(DEFAULT_LABELS)
TEMP_OCR = Path(r"c:\Users\28079\AppData\Local\Temp\BNZ.69f2b2034ca759d1\OCR\paddleocr_format")
REPO_OCR = _BERT_ROOT / "data" / "ocr_paddleocr_import"


def iter_ocr_texts(ocr_root: Path) -> list[str]:
    texts: list[str] = []
    for sub in ("train", "val", "test"):
        p = ocr_root / sub / f"{sub}_label.txt"
        if not p.is_file():
            continue
        for raw in p.read_text(encoding="utf-8").splitlines():
            t = parse_paddleocr_label_line(raw)
            if t:
                texts.append(t)
    return texts


def pick_ocr_root(cli_dir: str | None) -> Path:
    if cli_dir:
        return Path(cli_dir)
    if TEMP_OCR.is_dir():
        return TEMP_OCR
    return REPO_OCR


def main() -> None:
    base = _BERT_ROOT
    p = argparse.ArgumentParser()
    p.add_argument("--ocr_dir", type=str, default="", help="paddleocr_format 根目录，默认同脚本说明")
    p.add_argument(
        "--checkpoint",
        type=str,
        default=str(base / "bert_chinese_multilabel_out" / "best"),
    )
    args = p.parse_args()

    ocr_root = pick_ocr_root(args.ocr_dir.strip() or None)
    if not ocr_root.is_dir():
        raise SystemExit(f"未找到 OCR 目录: {ocr_root}")

    ckpt = Path(args.checkpoint)
    th = load_inference_threshold(ckpt)
    if th is None:
        th = 0.0

    texts_ordered = iter_ocr_texts(ocr_root)
    seen: set[str] = set()
    texts: list[str] = []
    for t in texts_ordered:
        if t in seen:
            continue
        seen.add(t)
        texts.append(t)

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    tok = AutoTokenizer.from_pretrained(str(ckpt))
    model = AutoModelForSequenceClassification.from_pretrained(str(ckpt))
    model.to(device)
    model.eval()

    match_rows: list[dict] = []
    miss_rows: list[dict] = []

    for i, text in enumerate(texts, 1):
        pr = predict_long(
            model,
            tok,
            text,
            device,
            max_length=512,
            chunk_chars=512,
            chunk_overlap=0,
            threshold=th,
        )
        pred = pr["pred"]
        row = {
            "idx": i,
            "text": text,
            "pred": pred,
            "gold": GOLD,
            "total_score_pct": pr["total_score_pct"],
        }
        if pred == GOLD:
            match_rows.append(row)
        else:
            miss_rows.append(row)

    out_dir = base / "data"
    out_dir.mkdir(parents=True, exist_ok=True)
    hit_path = out_dir / "ocr_bert_match_weak_label.txt"
    miss_path = out_dir / "ocr_bert_mismatch_weak_label.txt"

    lines_hit = [
        f"OCR 根目录: {ocr_root.resolve()}",
        f"权重: {ckpt.resolve()}  阈值: {th}  设备: {device}",
        f"弱标签 GOLD（与 merge_ocr 一致）: {GOLD}",
        f"去重后条数: {len(texts)}  与 GOLD 六维全一致: {len(match_rows)}  不一致: {len(miss_rows)}",
        "",
        "=== 与弱标签预测一致（相对该 GOLD 可视为「准」）===",
    ]
    for r in match_rows:
        lines_hit.append(f"{r['idx']}\tscore={r['total_score_pct']}\t{r['text']}")

    lines_hit.append("")
    lines_hit.append(f"（共 {len(match_rows)} 条）")
    hit_path.write_text("\n".join(lines_hit), encoding="utf-8")

    lines_miss = [
        f"=== 与弱标签预测不一致 ===",
        f"共 {len(miss_rows)} 条",
        "",
    ]
    for r in miss_rows:
        lines_miss.append(
            f"{r['idx']}\tscore={r['total_score_pct']}\tpred={r['pred']}\tgold={GOLD}\t{r['text']}"
        )
    miss_path.write_text("\n".join(lines_miss), encoding="utf-8")

    meta = {
        "ocr_root": str(ocr_root.resolve()),
        "checkpoint": str(ckpt.resolve()),
        "threshold": float(th) if isinstance(th, (int, float)) else str(th),
        "gold": GOLD,
        "unique_texts": len(texts),
        "match_count": len(match_rows),
        "mismatch_count": len(miss_rows),
        "match_rate": round(len(match_rows) / max(len(texts), 1), 4),
    }
    (out_dir / "ocr_bert_weak_eval_meta.json").write_text(
        json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    print(json.dumps(meta, ensure_ascii=False, indent=2))
    print(f"已写: {hit_path.resolve()}")
    print(f"已写: {miss_path.resolve()}")


if __name__ == "__main__":
    main()
