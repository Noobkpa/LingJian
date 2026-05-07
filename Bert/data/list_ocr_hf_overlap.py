"""
列出：
1) OCR 三份（train/val/test 的 *_label.txt）内部重复出现的文本（合并时第二次及以后会被跳过）
2) 与合并前 hf/train.jsonl.bak 的 text 完全一致的重合（若有）
3) 与 hf/train+val+test 中「非 ocr-import」行的完全一致重合（若有）
"""
from __future__ import annotations

import json
from collections import Counter
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
OCR_ROOT = BASE / "data" / "ocr_paddleocr_import"
OUT = BASE / "data" / "ocr_bert_text_overlap.txt"


def parse_ocr_texts_ordered() -> list[str]:
    texts: list[str] = []
    for sub in ("train", "val", "test"):
        p = OCR_ROOT / sub / f"{sub}_label.txt"
        if not p.is_file():
            continue
        for raw in p.read_text(encoding="utf-8").splitlines():
            raw = raw.strip()
            if not raw:
                continue
            parts = raw.split("\t", 1)
            if len(parts) < 2:
                continue
            t = parts[1].strip()
            if t:
                texts.append(t)
    return texts


def load_jsonl_texts(path: Path) -> set[str]:
    s: set[str] = set()
    if not path.is_file():
        return s
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        d = json.loads(line)
        t = d.get("text", "")
        if isinstance(t, str) and t.strip():
            s.add(t.strip())
    return s


def load_hf_union_exclude_ocr_import() -> set[str]:
    s: set[str] = set()
    for name in ("train.jsonl", "val.jsonl", "test.jsonl"):
        p = BASE / "hf" / name
        if not p.is_file():
            continue
        for line in p.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line:
                continue
            d = json.loads(line)
            if str(d.get("id", "")).startswith("ocr-import"):
                continue
            t = d.get("text", "")
            if isinstance(t, str) and t.strip():
                s.add(t.strip())
    return s


def main() -> None:
    ocr_list = parse_ocr_texts_ordered()
    ocr_set = set(ocr_list)
    cnt = Counter(ocr_list)
    dups = [(t, n) for t, n in cnt.items() if n > 1]
    dups.sort(key=lambda x: (-x[1], x[0]))

    train_bak = load_jsonl_texts(BASE / "hf" / "train.jsonl.bak")
    bert_no_ocr = load_hf_union_exclude_ocr_import()
    inter_bak = sorted(ocr_set & train_bak)
    inter_bert = sorted(ocr_set & bert_no_ocr)

    lines: list[str] = []
    lines.append("【说明】合并脚本 merge_ocr_into_hf_train.py 对 OCR 文本按顺序处理：")
    lines.append("  seen 初始为原 train 全部 text；若当前句已在 seen 则跳过（不写入新行）。")
    lines.append("  因此「跳过」= 要么已在原 BERT train 中，要么与前面已处理的 OCR 句重复。")
    lines.append("")
    lines.append("【统计】OCR 解析总行数: %d；不同文本数: %d；重复行数: %d" % (len(ocr_list), len(ocr_set), len(ocr_list) - len(ocr_set)))
    lines.append("与 train.jsonl.bak 完全一致: %d 条" % len(inter_bak))
    lines.append("与 hf(train+val+test) 非 ocr-import 完全一致: %d 条" % len(inter_bert))
    lines.append("")

    lines.append("=" * 60)
    lines.append("一、OCR 语料内部重复（同一句在 train/val/test 多份或多次出现，出现次数>1）")
    lines.append("=" * 60)
    for t, n in dups:
        lines.append("%d\t%s" % (n, t))
    lines.append("")
    lines.append("（共 %d 种字符串重复，合计多出来 %d 行）" % (len(dups), sum(n - 1 for _, n in dups)))

    lines.append("")
    lines.append("=" * 60)
    lines.append("二、与合并前 hf/train.jsonl.bak 逐字重合（若有）")
    lines.append("=" * 60)
    if not inter_bak:
        lines.append("（无）")
    else:
        lines.extend(inter_bak)

    lines.append("")
    lines.append("=" * 60)
    lines.append("三、与当前 hf/train+val+test 中非 ocr-import 行逐字重合（若有）")
    lines.append("=" * 60)
    if not inter_bert:
        lines.append("（无）")
    else:
        lines.extend(inter_bert)

    OUT.write_text("\n".join(lines), encoding="utf-8")
    print("Wrote", OUT.resolve())


if __name__ == "__main__":
    main()
