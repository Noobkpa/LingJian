"""从 ocr_bert_match_weak_label.txt 按 total_score_pct 再筛一版「高置信」子集（默认 ≥65）。"""
from __future__ import annotations

import argparse
import re
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
SRC = BASE / "data" / "ocr_bert_match_weak_label.txt"
OUT = BASE / "data" / "ocr_bert_match_weak_label_highconf.txt"
LINE_RE = re.compile(r"^(\d+)\tscore=([\d.]+)\t(.+)$")


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--min_score", type=float, default=65.0, help="总得分下限（predict_long 的 total_score_pct）")
    p.add_argument("--src", type=str, default=str(SRC))
    p.add_argument("--out", type=str, default=str(OUT))
    args = p.parse_args()

    src = Path(args.src)
    if not src.is_file():
        raise SystemExit(f"请先运行 list_ocr_texts_bert_match_weak.py 生成: {src}")

    kept: list[tuple[int, float, str]] = []
    all_match: list[tuple[int, float, str]] = []
    for line in src.read_text(encoding="utf-8").splitlines():
        m = LINE_RE.match(line.strip())
        if not m:
            continue
        idx, sc, text = int(m.group(1)), float(m.group(2)), m.group(3)
        all_match.append((idx, sc, text))
        if sc >= args.min_score:
            kept.append((idx, sc, text))

    lines = [
        f"来源: {src.name} 中与弱标签 [0,1,1,0,0,0] 六维全一致的句子，再筛 total_score_pct >= {args.min_score}",
        f"全一致条数: {len(all_match)}  本文件条数: {len(kept)}",
        "",
    ]
    for idx, sc, text in sorted(kept, key=lambda x: -x[1]):
        lines.append(f"{idx}\tscore={sc}\t{text}")

    Path(args.out).write_text("\n".join(lines), encoding="utf-8")
    print(f"Wrote {Path(args.out).resolve()}  ({len(kept)} lines)")


if __name__ == "__main__":
    main()
