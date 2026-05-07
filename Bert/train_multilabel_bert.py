"""
使用 Hugging Face 官方权重 bert-base-chinese（Google 中文 BERT）
在本地 hf/*.jsonl 多标签数据上微调，并输出验证集 / 测试集指标。
"""
from __future__ import annotations

import argparse
import json
import os
from datetime import datetime
from pathlib import Path

import numpy as np
import torch
import torch.nn as nn
from sklearn.metrics import f1_score, precision_recall_fscore_support
from torch.utils.data import DataLoader, Dataset
from tqdm import tqdm
from transformers import (
    AutoModelForSequenceClassification,
    AutoTokenizer,
    get_linear_schedule_with_warmup,
)

from thresholding import (
    apply_logits_threshold,
    exact_match_rate,
    pick_threshold_on_validation,
    save_threshold_config,
)


def _metrics_for_json(m: dict) -> dict:
    """evaluate 返回的字典转为可 JSON 序列化的 float。"""
    return {k: float(v) for k, v in m.items()}


def load_jsonl(path: Path) -> list[dict]:
    rows = []
    with path.open(encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            rows.append(json.loads(line))
    return rows


class JsonlMultiLabelDataset(Dataset):
    def __init__(self, rows: list[dict], tokenizer, max_length: int):
        self.rows = rows
        self.tokenizer = tokenizer
        self.max_length = max_length

    def __len__(self):
        return len(self.rows)

    def __getitem__(self, idx: int):
        r = self.rows[idx]
        text = r["text"]
        labels = torch.tensor(r["labels"], dtype=torch.float32)
        weight = float(r.get("weight", 1.0))
        enc = self.tokenizer(
            text,
            max_length=self.max_length,
            padding="max_length",
            truncation=True,
            return_tensors="pt",
        )
        return {
            "input_ids": enc["input_ids"].squeeze(0),
            "attention_mask": enc["attention_mask"].squeeze(0),
            "labels": labels,
            "weight": torch.tensor(weight, dtype=torch.float32),
        }


def collate_fn(batch: list[dict]) -> dict:
    return {
        "input_ids": torch.stack([b["input_ids"] for b in batch]),
        "attention_mask": torch.stack([b["attention_mask"] for b in batch]),
        "labels": torch.stack([b["labels"] for b in batch]),
        "weight": torch.stack([b["weight"] for b in batch]),
    }


def compute_pos_weight_tensor(train_rows: list[dict], num_labels: int) -> torch.Tensor:
    """BCEWithLogitsLoss 的 pos_weight：负例数 / 正例数，缓解稀有标签。"""
    y = np.array([r["labels"] for r in train_rows], dtype=np.float64)
    pos = np.clip(y.sum(axis=0), 1.0, None)
    neg = len(y) - y.sum(axis=0)
    w = neg / pos
    return torch.tensor(w, dtype=torch.float32)


@torch.no_grad()
def collect_logits_and_labels(model, loader, device):
    model.eval()
    all_logits = []
    all_labels = []
    for batch in loader:
        input_ids = batch["input_ids"].to(device)
        attention_mask = batch["attention_mask"].to(device)
        out = model(input_ids=input_ids, attention_mask=attention_mask)
        all_logits.append(out.logits.detach().cpu().numpy())
        all_labels.append(batch["labels"].numpy())
    return np.concatenate(all_labels), np.concatenate(all_logits)


@torch.no_grad()
def evaluate(model, loader, device, threshold: float | np.ndarray = 0.0):
    model.eval()
    y_true, y_score = collect_logits_and_labels(model, loader, device)
    y_pred = apply_logits_threshold(y_score, threshold)
    micro_f1 = f1_score(y_true, y_pred, average="micro", zero_division=0)
    macro_f1 = f1_score(y_true, y_pred, average="macro", zero_division=0)
    p_micro, r_micro, _, _ = precision_recall_fscore_support(
        y_true, y_pred, average="micro", zero_division=0
    )
    p_macro, r_macro, _, _ = precision_recall_fscore_support(
        y_true, y_pred, average="macro", zero_division=0
    )
    return {
        "micro_f1": micro_f1,
        "macro_f1": macro_f1,
        "micro_precision": p_micro,
        "micro_recall": r_micro,
        "macro_precision": p_macro,
        "macro_recall": r_macro,
        "exact_match": exact_match_rate(y_true, y_pred),
    }


def train_epoch(
    model,
    loader,
    optimizer,
    scheduler,
    device,
    max_grad_norm: float,
    pos_weight: torch.Tensor,
):
    model.train()
    total_loss = 0.0
    pw = pos_weight.to(device)
    bce = nn.BCEWithLogitsLoss(reduction="none", pos_weight=pw)
    for batch in tqdm(loader, desc="train", leave=False):
        input_ids = batch["input_ids"].to(device)
        attention_mask = batch["attention_mask"].to(device)
        labels = batch["labels"].to(device)
        w = batch["weight"].to(device).unsqueeze(1)

        optimizer.zero_grad(set_to_none=True)
        out = model(input_ids=input_ids, attention_mask=attention_mask)
        logits = out.logits
        loss_elem = bce(logits, labels)
        loss = (loss_elem * w).sum() / (w.expand_as(loss_elem)).sum().clamp_min(1e-8)
        loss.backward()
        torch.nn.utils.clip_grad_norm_(model.parameters(), max_grad_norm)
        optimizer.step()
        scheduler.step()
        total_loss += float(loss.item())
    return total_loss / max(len(loader), 1)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--model_name",
        type=str,
        default="bert-base-chinese",
        help="Hugging Face 模型名；bert-base-chinese 为 Google 官方中文 BERT",
    )
    parser.add_argument(
        "--data_dir",
        type=str,
        default=None,
        help="含 train.jsonl / val.jsonl / test.jsonl 的目录，默认为本脚本旁 hf/",
    )
    parser.add_argument("--output_dir", type=str, default="./bert_chinese_multilabel_out")
    parser.add_argument("--max_length", type=int, default=512)
    parser.add_argument("--batch_size", type=int, default=8)
    parser.add_argument("--epochs", type=int, default=10)
    parser.add_argument("--lr", type=float, default=3e-5)
    parser.add_argument("--warmup_ratio", type=float, default=0.06)
    parser.add_argument("--weight_decay", type=float, default=0.01)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--max_grad_norm", type=float, default=1.0)
    parser.add_argument(
        "--threshold",
        type=float,
        default=0.0,
        help="训练过程中验证用的全局 logit 阈值；0 等价于 sigmoid>0.5",
    )
    parser.add_argument(
        "--best_metric",
        type=str,
        choices=("macro_f1", "exact_match"),
        default="macro_f1",
        help="按验证集哪项指标保存 best",
    )
    parser.add_argument(
        "--threshold_strategy",
        type=str,
        choices=("global_only", "auto"),
        default="global_only",
        help="训练结束写 thresholds.json 时的策略",
    )
    args = parser.parse_args()

    base = Path(__file__).resolve().parent
    data_dir = Path(args.data_dir) if args.data_dir else base / "hf"
    for name in ("train.jsonl", "val.jsonl", "test.jsonl"):
        p = data_dir / name
        if not p.is_file():
            raise FileNotFoundError(f"缺少数据文件: {p}")

    torch.manual_seed(args.seed)
    np.random.seed(args.seed)
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"设备: {device}")

    train_rows = load_jsonl(data_dir / "train.jsonl")
    val_rows = load_jsonl(data_dir / "val.jsonl")
    test_rows = load_jsonl(data_dir / "test.jsonl")
    num_labels = len(train_rows[0]["labels"])
    print(f"样本数 train/val/test: {len(train_rows)}/{len(val_rows)}/{len(test_rows)}, 标签数: {num_labels}")

    tokenizer = AutoTokenizer.from_pretrained(args.model_name)
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token

    train_ds = JsonlMultiLabelDataset(train_rows, tokenizer, args.max_length)
    val_ds = JsonlMultiLabelDataset(val_rows, tokenizer, args.max_length)
    test_ds = JsonlMultiLabelDataset(test_rows, tokenizer, args.max_length)

    train_loader = DataLoader(
        train_ds,
        batch_size=args.batch_size,
        shuffle=True,
        collate_fn=collate_fn,
        num_workers=0,
    )
    val_loader = DataLoader(
        val_ds, batch_size=args.batch_size, shuffle=False, collate_fn=collate_fn, num_workers=0
    )
    test_loader = DataLoader(
        test_ds, batch_size=args.batch_size, shuffle=False, collate_fn=collate_fn, num_workers=0
    )

    model = AutoModelForSequenceClassification.from_pretrained(
        args.model_name,
        num_labels=num_labels,
        problem_type="multi_label_classification",
    )
    model.to(device)

    pos_weight_tensor = compute_pos_weight_tensor(train_rows, num_labels)

    num_training_steps = len(train_loader) * args.epochs
    num_warmup_steps = int(num_training_steps * args.warmup_ratio)
    optimizer = torch.optim.AdamW(
        model.parameters(), lr=args.lr, weight_decay=args.weight_decay
    )
    scheduler = get_linear_schedule_with_warmup(
        optimizer,
        num_warmup_steps=num_warmup_steps,
        num_training_steps=num_training_steps,
    )

    best_score = -1.0
    best_epoch = 0
    os.makedirs(args.output_dir, exist_ok=True)
    metric_key = "macro_f1" if args.best_metric == "macro_f1" else "exact_match"

    for epoch in range(1, args.epochs + 1):
        print(f"\n===== Epoch {epoch}/{args.epochs} =====")
        avg_loss = train_epoch(
            model,
            train_loader,
            optimizer,
            scheduler,
            device,
            args.max_grad_norm,
            pos_weight_tensor,
        )
        print(f"平均训练损失: {avg_loss:.4f}")
        val_m = evaluate(model, val_loader, device, args.threshold)
        print(
            f"验证 micro-F1: {val_m['micro_f1']:.4f}  macro-F1: {val_m['macro_f1']:.4f}  "
            f"完全一致率: {val_m['exact_match']:.4f}  "
            f"micro P/R: {val_m['micro_precision']:.4f}/{val_m['micro_recall']:.4f}"
        )
        cur = val_m[metric_key]
        if cur >= best_score:
            best_score = cur
            best_epoch = epoch
            save_path = Path(args.output_dir) / "best"
            save_path.mkdir(parents=True, exist_ok=True)
            model.save_pretrained(save_path)
            tokenizer.save_pretrained(save_path)
            print(f"已保存当前最佳 ({args.best_metric}={cur:.4f}) 到 {save_path}")

    print("\n===== 测试集：加载 best，在验证集上搜索逐维 logit 阈值 =====")
    best_path = Path(args.output_dir) / "best"
    if best_path.is_dir():
        model = AutoModelForSequenceClassification.from_pretrained(best_path)
        model.to(device)
    y_val, logits_val = collect_logits_and_labels(model, val_loader, device)
    th_mode, th_val = pick_threshold_on_validation(
        y_val, logits_val, strategy=args.threshold_strategy
    )
    save_threshold_config(best_path / "thresholds.json", th_mode, th_val)
    th_disp = (
        float(th_val) if th_mode == "global_logits" else np.round(np.asarray(th_val), 3).tolist()
    )
    print(f"已写入 {best_path / 'thresholds.json'}  mode={th_mode}  -> {th_disp}")

    val_tuned = evaluate(model, val_loader, device, th_val)
    print(
        f"验证(逐维阈值) micro-F1: {val_tuned['micro_f1']:.4f}  macro-F1: {val_tuned['macro_f1']:.4f}  "
        f"完全一致率: {val_tuned['exact_match']:.4f}"
    )

    test_scalar = evaluate(model, test_loader, device, args.threshold)
    test_tuned = evaluate(model, test_loader, device, th_val)
    print(
        f"\n测试(全局阈值={args.threshold}) micro-F1: {test_scalar['micro_f1']:.4f}  "
        f"macro-F1: {test_scalar['macro_f1']:.4f}  完全一致率: {test_scalar['exact_match']:.4f}"
    )
    print(
        f"测试(逐维阈值) micro-F1: {test_tuned['micro_f1']:.4f}  "
        f"macro-F1: {test_tuned['macro_f1']:.4f}  完全一致率: {test_tuned['exact_match']:.4f}  "
        f"micro P/R: {test_tuned['micro_precision']:.4f}/{test_tuned['micro_recall']:.4f}"
    )

    if th_mode == "global_logits":
        th_saved = {"mode": th_mode, "value": float(th_val)}
    else:
        th_saved = {
            "mode": th_mode,
            "values": [float(x) for x in np.asarray(th_val).tolist()],
        }
    meta = {
        "finished_at_local": datetime.now().isoformat(timespec="seconds"),
        "model_name": args.model_name,
        "data_dir": str(data_dir.resolve()),
        "best_checkpoint_dir": str(best_path.resolve()),
        "train_samples": len(train_rows),
        "val_samples": len(val_rows),
        "test_samples": len(test_rows),
        "num_labels": num_labels,
        "hyperparams": {
            "max_length": args.max_length,
            "batch_size": args.batch_size,
            "epochs": args.epochs,
            "lr": args.lr,
            "warmup_ratio": args.warmup_ratio,
            "weight_decay": args.weight_decay,
            "seed": args.seed,
            "max_grad_norm": args.max_grad_norm,
            "train_eval_threshold": args.threshold,
            "best_metric": args.best_metric,
            "threshold_strategy": args.threshold_strategy,
        },
        "best_on_validation": {
            "epoch": best_epoch,
            "score": float(best_score),
            "metric": args.best_metric,
        },
        "saved_thresholds": th_saved,
        "validation_after_threshold_tuning": _metrics_for_json(val_tuned),
        "test_with_train_eval_threshold": _metrics_for_json(test_scalar),
        "test_with_saved_thresholds": _metrics_for_json(test_tuned),
    }
    meta_path = best_path / "training_meta.json"
    meta_path.write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"已写入训练元数据: {meta_path.resolve()}")


if __name__ == "__main__":
    main()
