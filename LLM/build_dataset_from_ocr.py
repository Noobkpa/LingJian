"""
从 ocr 目录下的图文标签文件生成 train_sft.py 用的 JSONL。

标签格式：每行「相对路径<Tab>图中文字」
  - ocr/train/augmented_label.txt
  - ocr/val/val_label.txt
  - ocr/test/test_label.txt（可选）

对每条「文字」调用仓库内 BERT，构造与后端一致的 system/user，assistant 为
由 BERT 结果映射得到的 JSON（弱监督：教模型对齐 BERT 与灵鉴字段）。

在项目根目录执行：
  set PYTHONPATH=D:\\codexproject
  python LLM/build_dataset_from_ocr.py
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def _read_label_file(path: Path) -> list[str]:
    if not path.is_file():
        return []
    texts: list[str] = []
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line:
            continue
        if "\t" in line:
            _, text = line.split("\t", 1)
        else:
            parts = line.split(maxsplit=1)
            text = parts[1] if len(parts) == 2 else ""
        text = text.strip()
        if text:
            texts.append(text)
    return texts


def _risk_to_final(risk: str) -> str:
    return {"高": "高风险", "中": "中风险", "低": "低风险", "未知": "低风险"}.get(
        (risk or "").strip(), "中风险"
    )


def _make_record(text: str, bert_service) -> dict | None:
    from backend.app.services.llm_service import SYSTEM_PROMPT

    t = text.strip()
    if not t:
        return None
    bert = bert_service.predict(t)
    slim = {
        "risk_level": bert.risk_level,
        "predicted_label_names": bert.predicted_label_names,
        "total_score_pct": bert.total_score_pct,
        "prediction_summary_zh": bert.prediction_summary_zh,
        "probs": [round(float(x), 4) for x in (bert.probs or [])],
    }
    user = (
        "请根据以下文本和 BERT 检测报告输出最终研判 JSON。\n【文本】\n"
        f"{t}\n\n【BERT报告】\n"
        f"{json.dumps(slim, ensure_ascii=False)}"
    )
    basis = (bert.prediction_summary_zh or "与 BERT 研判一致").replace("；", ";")
    assistant_obj = {
        "risk_level": _risk_to_final(bert.risk_level),
        "comprehensive_score": int(round(float(bert.total_score_pct))),
        "judgment_basis": basis,
        "features": list(bert.predicted_label_names),
    }
    assistant = json.dumps(assistant_obj, ensure_ascii=False)
    return {
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user},
            {"role": "assistant", "content": assistant},
        ]
    }


def _write_jsonl(path: Path, records: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as fout:
        for rec in records:
            fout.write(json.dumps(rec, ensure_ascii=False) + "\n")


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument(
        "--train_label",
        type=str,
        default=str(ROOT / "ocr" / "train" / "augmented_label.txt"),
    )
    p.add_argument(
        "--val_label",
        type=str,
        default=str(ROOT / "ocr" / "val" / "val_label.txt"),
    )
    p.add_argument(
        "--test_label",
        type=str,
        default=str(ROOT / "ocr" / "test" / "test_label.txt"),
    )
    p.add_argument(
        "--out_train",
        type=str,
        default=str(ROOT / "LLM" / "data" / "ocr_sft" / "train.jsonl"),
    )
    p.add_argument(
        "--out_val",
        type=str,
        default=str(ROOT / "LLM" / "data" / "ocr_sft" / "val.jsonl"),
    )
    p.add_argument(
        "--out_test",
        type=str,
        default=str(ROOT / "LLM" / "data" / "ocr_sft" / "test.jsonl"),
    )
    p.add_argument("--limit_train", type=int, default=0, help="仅处理前 N 条训练样本，0 表示全部")
    p.add_argument("--limit_val", type=int, default=0)
    p.add_argument("--limit_test", type=int, default=0)
    args = p.parse_args()

    from backend.app.services.bert_service import bert_service

    train_texts = _read_label_file(Path(args.train_label))
    val_texts = _read_label_file(Path(args.val_label))
    test_texts = _read_label_file(Path(args.test_label))

    if args.limit_train > 0:
        train_texts = train_texts[: args.limit_train]
    if args.limit_val > 0:
        val_texts = val_texts[: args.limit_val]
    if args.limit_test > 0:
        test_texts = test_texts[: args.limit_test]

    def build_all(texts: list[str]) -> list[dict]:
        out: list[dict] = []
        for i, tx in enumerate(texts):
            rec = _make_record(tx, bert_service)
            if rec:
                out.append(rec)
            if (i + 1) % 100 == 0:
                print(f"  ... {i + 1}/{len(texts)}")
        return out

    print(f"训练条数: {len(train_texts)} <- {args.train_label}")
    train_recs = build_all(train_texts)
    print(f"验证条数: {len(val_texts)} <- {args.val_label}")
    val_recs = build_all(val_texts)
    print(f"测试条数: {len(test_texts)} <- {args.test_label}")
    test_recs = build_all(test_texts)

    _write_jsonl(Path(args.out_train), train_recs)
    _write_jsonl(Path(args.out_val), val_recs)
    _write_jsonl(Path(args.out_test), test_recs)
    print(f"已写入:\n  {args.out_train} ({len(train_recs)})\n  {args.out_val} ({len(val_recs)})\n  {args.out_test} ({len(test_recs)})")


if __name__ == "__main__":
    main()
