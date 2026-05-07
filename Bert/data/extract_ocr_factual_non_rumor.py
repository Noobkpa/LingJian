"""
从 OCR paddleocr 文本中筛「更可能为事实陈述、而非健康谣言」的句子。

说明：模型不做真假鉴定；本脚本仅用**关键词/短语白名单**（可改 FACT_SUBSTRINGS）
覆盖常见「真科普事实」类表述。其余句子默认不写入。

用法（Bert 目录）:
  python data/extract_ocr_factual_non_rumor.py
"""
from __future__ import annotations

import sys
from pathlib import Path

_BERT_ROOT = Path(__file__).resolve().parent.parent
if str(_BERT_ROOT) not in sys.path:
    sys.path.insert(0, str(_BERT_ROOT))

from merge_ocr_into_hf_train import parse_paddleocr_label_line

OCR_ROOT = _BERT_ROOT / "data" / "ocr_paddleocr_import"
OUT = _BERT_ROOT / "data" / "ocr_factual_non_rumor.txt"

# 子串命中即视为「候选事实句」（可按你的语料扩充）
FACT_SUBSTRINGS = (
    "中国天眼",
    "墨子号",
    "神威太湖之光",
    "单口径射电望远镜",
    "量子科学实验卫星",
)


def iter_ocr_texts() -> list[str]:
    texts: list[str] = []
    for sub in ("train", "val", "test"):
        p = OCR_ROOT / sub / f"{sub}_label.txt"
        if not p.is_file():
            continue
        for raw in p.read_text(encoding="utf-8").splitlines():
            t = parse_paddleocr_label_line(raw)
            if t:
                texts.append(t)
    return texts


def main() -> None:
    seen: set[str] = set()
    hits: list[str] = []
    for t in iter_ocr_texts():
        if t in seen:
            continue
        seen.add(t)
        if any(s in t for s in FACT_SUBSTRINGS):
            hits.append(t)

    lines = [
        "【说明】本文件为 OCR 语料中，命中「事实类关键词白名单」的句子（常识上多为真，而非养生谣言）。",
        "BERT 六维全 0 不等价于「非谣言」；本列表与模型预测无关，仅关键词筛选。",
        f"白名单子串: {', '.join(FACT_SUBSTRINGS)}",
        f"命中条数（去重）: {len(hits)}",
        "",
        "=== 列表 ===",
    ]
    lines.extend(hits)
    OUT.write_text("\n".join(lines), encoding="utf-8")
    print(f"Wrote {OUT.resolve()} ({len(hits)} lines)")


if __name__ == "__main__":
    main()
