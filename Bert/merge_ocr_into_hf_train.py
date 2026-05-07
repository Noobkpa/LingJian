"""
将 PaddleOCR 风格标签文件（每行：相对图路径\\t识别文本）中的文本并入 hf/train.jsonl。

OCR 语料无六维人工标注：默认使用弱标签 [0,1,1,0,0,0]（术语堆砌、虚假疗效），
weight=1.2；若需精标请改 DEFAULT_LABELS / DEFAULT_WEIGHT 或改脚本逻辑后重跑。

用法：
  python merge_ocr_into_hf_train.py
  python merge_ocr_into_hf_train.py --ocr_dir data/ocr_paddleocr_import --dry_run
"""
from __future__ import annotations

import argparse
import json
import shutil
from pathlib import Path


# 与 hf/dataset_info.json 中 positive_double 档一致；标签可按业务修改
DEFAULT_LABELS = [0, 1, 1, 0, 0, 0]
DEFAULT_WEIGHT = 1.2


def load_jsonl(path: Path) -> list[dict]:
    rows = []
    with path.open(encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            rows.append(json.loads(line))
    return rows


def parse_paddleocr_label_line(line: str) -> str | None:
    line = line.strip()
    if not line:
        return None
    parts = line.split("\t", 1)
    if len(parts) < 2:
        return None
    text = parts[1].strip()
    return text if text else None


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


def main() -> None:
    base = Path(__file__).resolve().parent
    p = argparse.ArgumentParser(description="合并 OCR 文本到 hf/train.jsonl")
    p.add_argument(
        "--ocr_dir",
        type=str,
        default=str(base / "data" / "ocr_paddleocr_import"),
        help="内含 train/train_label.txt、val/、test/ 的 PaddleOCR 格式目录",
    )
    p.add_argument(
        "--train_jsonl",
        type=str,
        default=str(base / "hf" / "train.jsonl"),
    )
    p.add_argument("--dry_run", action="store_true", help="只统计不写文件")
    args = p.parse_args()

    ocr_root = Path(args.ocr_dir)
    train_path = Path(args.train_jsonl)
    if not ocr_root.is_dir():
        raise SystemExit(f"未找到 OCR 目录: {ocr_root.resolve()}")

    existing = load_jsonl(train_path)
    seen = {r["text"].strip() for r in existing if isinstance(r.get("text"), str)}
    ocr_texts = iter_ocr_texts(ocr_root)
    new_texts = []
    for t in ocr_texts:
        if t in seen:
            continue
        seen.add(t)
        new_texts.append(t)

    print(f"已有 train 条数: {len(existing)}")
    print(f"OCR 解析到文本条数: {len(ocr_texts)}（含 train/val/test 三份）")
    print(f"去重后待追加: {len(new_texts)}（与现有 train 文本完全相同的已跳过）")

    if args.dry_run:
        return

    if not new_texts:
        print("无新样本，退出。")
        return

    bak = train_path.with_suffix(train_path.suffix + ".bak")
    shutil.copy2(train_path, bak)
    print(f"已备份: {bak.resolve()}")

    start = len(existing) + 1
    added = []
    for i, text in enumerate(new_texts):
        added.append(
            {
                "id": f"ocr-import-{start + i}",
                "text": text,
                "labels": list(DEFAULT_LABELS),
                "weight": DEFAULT_WEIGHT,
            }
        )

    out_rows = existing + added
    train_path.write_text(
        "\n".join(json.dumps(r, ensure_ascii=False) for r in out_rows) + "\n",
        encoding="utf-8",
    )
    print(f"已写入 {train_path.resolve()} ，新总行数: {len(out_rows)}")


if __name__ == "__main__":
    main()
