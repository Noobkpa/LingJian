"""
从 OCR 去重文本中筛：六维二值预测全 0，且按「非典型养生谣言 / 偏可核对事实」规则保留 Top-N。

规则（可改 TRUTH_RULES）：
- 先取 pred == [0,0,0,0,0,0]
- 再命中任一「偏事实」子串（营养/毒理常识、问号辟谣体、已报道事件等）

若命中不足 N，脚本会退出并提示需放宽规则或接受「仅 pred 全 0」池。

用法（Bert 根目录）:
  # 从已保存的弱标签对比结果解析（快；pred 与当时 list_ocr_texts_bert_match_weak.py 一致）
  python data/export_ocr_pred_zero_non_rumor_topn.py --from-mismatch data/ocr_bert_mismatch_weak_label.txt --n 10
  # 或对当前 checkpoint 全量重算
  python data/export_ocr_pred_zero_non_rumor_topn.py --n 10
"""
from __future__ import annotations

import argparse
import ast
import json
import re
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

from merge_ocr_into_hf_train import parse_paddleocr_label_line

REPO_OCR = _BERT_ROOT / "data" / "ocr_paddleocr_import"
ZERO = [0, 0, 0, 0, 0, 0]

# 子串命中即进入「非谣言候选」（与六维标签正交；用于在 pred 全 0 池里系统捞取）
TRUTH_RULES: tuple[str, ...] = (
    "大米越精细",
    "葡萄颜色越深",
    "车厘子核仁",
    "鱼肉比猪肉",
    "泡发木耳",
    "睡夠八小時",
    "睡够八小时",
    "反季节蔬菜",
    "咖啡.*贫血",
    "没有咸味",
    "味精.*化工",
)


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


def dedupe_preserve(texts: list[str]) -> list[str]:
    seen: set[str] = set()
    out: list[str] = []
    for t in texts:
        if t in seen:
            continue
        seen.add(t)
        out.append(t)
    return out


def matches_truth_rule(text: str) -> bool:
    for pat in TRUTH_RULES:
        if re.search(pat, text):
            return True
    return False


_ROW_RE = re.compile(
    r"^(\d+)\tscore=([\d.]+)\tpred=(\[[\d, ]+\])\tgold=(\[[\d, ]+\])\t(.*)$"
)


def parse_mismatch_rows(path: Path) -> list[dict]:
    rows: list[dict] = []
    for raw in path.read_text(encoding="utf-8").splitlines():
        m = _ROW_RE.match(raw.strip())
        if not m:
            continue
        idx_s, score_s, pred_s, _gold_s, text = m.groups()
        try:
            pred = ast.literal_eval(pred_s.replace(" ", ""))
        except (SyntaxError, ValueError):
            continue
        rows.append(
            {
                "idx": int(idx_s),
                "total_score_pct": float(score_s),
                "pred": pred,
                "text": text,
            }
        )
    return rows


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--n", type=int, default=10)
    ap.add_argument("--ocr_dir", type=str, default=str(REPO_OCR))
    ap.add_argument(
        "--checkpoint",
        type=str,
        default=str(_BERT_ROOT / "bert_chinese_multilabel_out" / "best"),
    )
    ap.add_argument(
        "--out",
        type=str,
        default=str(_BERT_ROOT / "data" / "ocr_non_rumor_pred_zero_top10.txt"),
    )
    ap.add_argument(
        "--from-mismatch",
        type=str,
        default="",
        help="若指定，则从该 mismatch 文件解析 pred/score，不重跑模型",
    )
    args = ap.parse_args()

    ocr_root = Path(args.ocr_dir)
    ckpt = Path(args.checkpoint)
    if not ocr_root.is_dir():
        raise SystemExit(f"OCR 目录不存在: {ocr_root}")

    zero_hits: list[dict] = []
    picked: list[dict] = []
    th: float | str = 0.0
    source_note = ""

    if args.from_mismatch.strip():
        mm_path = Path(args.from_mismatch)
        if not mm_path.is_file():
            raise SystemExit(f"未找到 mismatch 文件: {mm_path}")
        rows = parse_mismatch_rows(mm_path)
        for r in rows:
            if r["pred"] == ZERO:
                zero_hits.append(r)
        rule_rows = [r for r in zero_hits if matches_truth_rule(r["text"])]
        rule_rows.sort(key=lambda x: x["idx"])
        picked = rule_rows[: args.n]
        source_note = f"pred/score 来源（缓存）: {mm_path.resolve()}"
    else:
        import torch
        from transformers import AutoModelForSequenceClassification, AutoTokenizer

        from predict_long import predict_long
        from thresholding import load_inference_threshold

        th = load_inference_threshold(ckpt)
        if th is None:
            th = 0.0

        texts = dedupe_preserve(iter_ocr_texts(ocr_root))
        device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        tok = AutoTokenizer.from_pretrained(str(ckpt))
        model = AutoModelForSequenceClassification.from_pretrained(str(ckpt))
        model.to(device)
        model.eval()

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
                "total_score_pct": pr["total_score_pct"],
            }
            if pred == ZERO:
                zero_hits.append(row)
                if matches_truth_rule(text):
                    picked.append(row)

        source_note = f"pred/score 来源: 现场推理 checkpoint={ckpt.resolve()}"

    if len(picked) < args.n:
        raise SystemExit(
            f"pred 全 0 且命中 TRUTH_RULES 仅 {len(picked)} 条（需要 {args.n}）。"
            f" pred 全 0 总数: {len(zero_hits)}。请放宽 TRUTH_RULES 或降低 n。"
        )

    picked = picked[: args.n]
    out_path = Path(args.out)

    lines = [
        "【说明】",
        "1) pred 指 BERT 六维二值预测（阈值见 thresholds.json / 默认 0）；全 0 表示六类话术均未过阈。",
        "2) 「非谣言」在此 = 命中 TRUTH_RULES 子串的候选（营养/毒理可核对、问号议题等），非医学结论；带「？」的常为误区/辟谣类标题，未必整句为真。",
        f"3) {source_note}",
        f"4) checkpoint（弱评估脚本默认）: {ckpt.resolve()}",
        f"5) OCR 去重顺序参考: {ocr_root.resolve()}",
        f"6) 本批 pred 全 0 条数（来源内）: {len(zero_hits)}；取规则命中按 idx 升序前 {args.n} 条。",
        "",
        "TRUTH_RULES (正则子串):",
        *[f"  - {r}" for r in TRUTH_RULES],
        "",
        "=== 十条（score = total_score_pct）===",
    ]
    for r in picked:
        lines.append(f"{r['idx']}\tscore={r['total_score_pct']}\tpred={r['pred']}\t{r['text']}")

    meta = {
        "n": args.n,
        "zero_pred_count": len(zero_hits),
        "picked_count": len(picked),
        "checkpoint": str(ckpt.resolve()),
        "ocr_root": str(ocr_root.resolve()),
        "threshold": float(th) if isinstance(th, (int, float)) else str(th),
        "from_mismatch": args.from_mismatch.strip() or None,
        "rows": picked,
    }
    out_path.write_text("\n".join(lines), encoding="utf-8")
    (out_path.with_suffix(".json")).write_text(
        json.dumps(meta, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print(f"Wrote {out_path.resolve()} and {out_path.with_suffix('.json').resolve()}")


if __name__ == "__main__":
    main()
