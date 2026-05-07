"""
Qwen（仓库内 Qwen2.5-3B-Instruct 等）LoRA 监督微调脚本。

数据：JSONL，每行一个对象，字段 messages 为三至多轮对话：
  [{"role":"system","content":"..."},{"role":"user","content":"..."},{"role":"assistant","content":"..."}]

最后一轮必须为 assistant，且仅对 assistant 段计算 loss（与灵鉴后端 llm_service 提示风格一致）。

用法（在项目根目录）:
  pip install -r LLM/requirements-train.txt
  python LLM/train_sft.py --model_path models/qwen/Qwen2.5-3B-Instruct \\
    --train_file LLM/data/example/train.jsonl --eval_file LLM/data/example/val.jsonl \\
    --output_dir LLM/output/qwen-lora-run1
"""
from __future__ import annotations

import argparse
import importlib.util
import json
import sys
from dataclasses import dataclass
from pathlib import Path

import torch
from datasets import Dataset
from peft import LoraConfig, TaskType, get_peft_model
from transformers import (
    AutoModelForCausalLM,
    AutoTokenizer,
    BitsAndBytesConfig,
    Trainer,
    TrainingArguments,
)


def _load_im_tokens(model_dir: Path) -> tuple[str, str]:
    """从模型目录的 tokenization_qwen 读取 ChatML 边界符，与权重一致。"""
    path = model_dir / "tokenization_qwen.py"
    if not path.is_file():
        # 与 Qwen ChatML 常见约定一致；优先以模型目录内 tokenization_qwen 为准
        return "<|im_start|>", "<|im_end|>"
    spec = importlib.util.spec_from_file_location("tokenization_qwen", path)
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    sys.modules["tokenization_qwen_runtime"] = mod
    spec.loader.exec_module(mod)
    return getattr(mod, "IMSTART", "<|im_start|>"), getattr(mod, "IMEND", "<|im_end|>")


def _build_full_text(messages: list[dict], im_start: str, im_end: str) -> str:
    parts: list[str] = []
    for m in messages:
        role, content = m.get("role", ""), m.get("content", "")
        parts.append(f"{im_start}{role}\n{content}{im_end}")
    return "\n".join(parts)


def _prefix_before_assistant_content(messages: list[dict], im_start: str, im_end: str) -> str:
    if not messages or messages[-1].get("role") != "assistant":
        raise ValueError("每条样本最后一轮须为 assistant")
    head = messages[:-1]
    asst = messages[-1].get("content", "")
    if not asst.strip():
        raise ValueError("assistant content 不能为空")
    blocks: list[str] = []
    for m in head:
        role, content = m.get("role", ""), m.get("content", "")
        blocks.append(f"{im_start}{role}\n{content}{im_end}")
    blocks.append(f"{im_start}assistant\n")
    return "\n".join(blocks)


def _encode_qwen(tok, text: str) -> list[int]:
    if hasattr(tok, "encode"):
        try:
            return tok.encode(text, add_special_tokens=False, allowed_special="all")
        except TypeError:
            return tok.encode(text, add_special_tokens=False)
    raise RuntimeError("tokenizer 无 encode")


def load_jsonl(path: Path) -> list[dict]:
    rows: list[dict] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        rows.append(json.loads(line))
    return rows


@dataclass
class Row:
    input_ids: list[int]
    labels: list[int]


def build_rows(
    records: list[dict],
    tokenizer,
    im_start: str,
    im_end: str,
    max_length: int,
) -> list[Row]:
    out: list[Row] = []
    for rec in records:
        messages = rec.get("messages")
        if not isinstance(messages, list) or len(messages) < 2:
            continue
        full = _build_full_text(messages, im_start, im_end)
        prefix = _prefix_before_assistant_content(messages, im_start, im_end)
        ids = _encode_qwen(tokenizer, full)
        pfx = _encode_qwen(tokenizer, prefix)
        if len(pfx) > len(ids) or ids[: len(pfx)] != pfx:
            # 前缀与整段编码边界不一致时，退化为只对最后 20% token 算 loss（极少见）
            cut = max(0, int(len(ids) * 0.8))
            pfx = ids[:cut]
        assistant_start = len(pfx)
        labels = [-100] * assistant_start + ids[assistant_start:]
        if len(ids) > max_length:
            ids = ids[-max_length:]
            labels = labels[-max_length:]
            n_mask = sum(1 for x in labels if x == -100)
            if n_mask >= len(labels):
                labels = [-100] * (len(labels) - 1) + [labels[-1]]
        out.append(Row(input_ids=ids, labels=labels))
    return out


def rows_to_dataset(rows: list[Row]) -> Dataset:
    return Dataset.from_dict(
        {
            "input_ids": [r.input_ids for r in rows],
            "labels": [r.labels for r in rows],
        }
    )


class CausalLMCollator:
    """仅 padding input_ids / labels（labels 用 -100 填充）。"""

    def __init__(self, pad_token_id: int) -> None:
        self.pad_token_id = int(pad_token_id)

    def __call__(self, features: list[dict]) -> dict[str, torch.Tensor]:
        max_len = max(len(f["input_ids"]) for f in features)
        input_ids: list[list[int]] = []
        attention_mask: list[list[int]] = []
        labels: list[list[int]] = []
        for f in features:
            ids = list(f["input_ids"])
            lab = list(f["labels"])
            pad_n = max_len - len(ids)
            input_ids.append(ids + [self.pad_token_id] * pad_n)
            attention_mask.append([1] * len(ids) + [0] * pad_n)
            labels.append(lab + [-100] * pad_n)
        return {
            "input_ids": torch.tensor(input_ids, dtype=torch.long),
            "attention_mask": torch.tensor(attention_mask, dtype=torch.long),
            "labels": torch.tensor(labels, dtype=torch.long),
        }


def main() -> None:
    parser = argparse.ArgumentParser(description="Qwen LoRA SFT（JSONL messages）")
    parser.add_argument(
        "--model_path",
        type=str,
        default=str(Path(__file__).resolve().parents[1] / "models" / "qwen" / "Qwen2.5-3B-Instruct"),
        help="本地 Qwen 目录（含 config.json）",
    )
    parser.add_argument("--train_file", type=str, required=True, help="训练 JSONL")
    parser.add_argument("--eval_file", type=str, default="", help="验证 JSONL（可选）")
    parser.add_argument("--output_dir", type=str, required=True, help="LoRA 与 tokenizer 输出目录")
    parser.add_argument("--max_seq_length", type=int, default=2048)
    parser.add_argument("--num_train_epochs", type=float, default=1.0)
    parser.add_argument("--per_device_train_batch_size", type=int, default=1)
    parser.add_argument("--gradient_accumulation_steps", type=int, default=8)
    parser.add_argument("--learning_rate", type=float, default=2e-4)
    parser.add_argument("--warmup_ratio", type=float, default=0.03)
    parser.add_argument("--logging_steps", type=int, default=5)
    parser.add_argument("--save_steps", type=int, default=200)
    parser.add_argument("--lora_r", type=int, default=8)
    parser.add_argument("--lora_alpha", type=int, default=32)
    parser.add_argument("--lora_dropout", type=float, default=0.05)
    parser.add_argument(
        "--target_modules",
        type=str,
        default="q_proj,k_proj,v_proj,o_proj,gate_proj,up_proj,down_proj",
        help="LoRA 目标线性层（逗号分隔）；Qwen2.5 使用 q_proj 等，勿使用 c_attn 等与当前基座不匹配的层名",
    )
    parser.add_argument(
        "--use_4bit",
        action="store_true",
        help="尝试 4bit 量化加载（需 bitsandbytes；Windows 常不可用）",
    )
    args = parser.parse_args()

    model_path = Path(args.model_path).resolve()
    if not (model_path / "config.json").is_file():
        raise SystemExit(f"未找到模型: {model_path}")

    im_start, im_end = _load_im_tokens(model_path)
    train_path = Path(args.train_file).resolve()
    if not train_path.is_file():
        raise SystemExit(f"训练文件不存在: {train_path}")

    tokenizer = AutoTokenizer.from_pretrained(str(model_path), trust_remote_code=True)
    if tokenizer.pad_token_id is None:
        tid = getattr(tokenizer, "eod_id", None) or getattr(tokenizer, "eos_token_id", None)
        if tid is not None:
            tokenizer.pad_token_id = tid
        else:
            tokenizer.pad_token_id = 151643

    bnb_config = None
    if args.use_4bit:
        bnb_config = BitsAndBytesConfig(
            load_in_4bit=True,
            bnb_4bit_quant_type="nf4",
            bnb_4bit_compute_dtype=torch.float16,
        )

    if torch.cuda.is_available():
        dtype = torch.bfloat16 if torch.cuda.is_bf16_supported() else torch.float16
        # 单卡训练不要用 device_map="auto"，否则易出现 meta 分片，Trainer.to(cuda) 报错
        model = AutoModelForCausalLM.from_pretrained(
            str(model_path),
            trust_remote_code=True,
            torch_dtype=dtype,
            device_map={"": 0},
            quantization_config=bnb_config,
        )
    else:
        dtype = torch.float32
        model = AutoModelForCausalLM.from_pretrained(
            str(model_path),
            trust_remote_code=True,
            torch_dtype=dtype,
            device_map=None,
            quantization_config=bnb_config,
            low_cpu_mem_usage=True,
        )
        model = model.to(dtype)

    target_modules = [x.strip() for x in args.target_modules.split(",") if x.strip()]
    peft_config = LoraConfig(
        task_type=TaskType.CAUSAL_LM,
        inference_mode=False,
        r=args.lora_r,
        lora_alpha=args.lora_alpha,
        lora_dropout=args.lora_dropout,
        target_modules=target_modules,
        bias="none",
    )
    model = get_peft_model(model, peft_config)
    model.enable_input_require_grads()
    if hasattr(model, "gradient_checkpointing_enable"):
        model.gradient_checkpointing_enable()

    train_records = load_jsonl(train_path)
    train_rows = build_rows(train_records, tokenizer, im_start, im_end, args.max_seq_length)
    if not train_rows:
        raise SystemExit("没有有效训练样本，请检查 JSONL 中 messages 格式")
    train_ds = rows_to_dataset(train_rows)

    eval_ds = None
    if args.eval_file:
        eval_path = Path(args.eval_file).resolve()
        if eval_path.is_file():
            eval_records = load_jsonl(eval_path)
            eval_rows = build_rows(eval_records, tokenizer, im_start, im_end, args.max_seq_length)
            if eval_rows:
                eval_ds = rows_to_dataset(eval_rows)

    pad_id = int(tokenizer.pad_token_id or 0)
    data_collator = CausalLMCollator(pad_token_id=pad_id)

    out_dir = Path(args.output_dir).resolve()
    out_dir.mkdir(parents=True, exist_ok=True)

    use_bf16 = bool(torch.cuda.is_available() and torch.cuda.is_bf16_supported())
    targs = TrainingArguments(
        output_dir=str(out_dir),
        num_train_epochs=args.num_train_epochs,
        per_device_train_batch_size=args.per_device_train_batch_size,
        per_device_eval_batch_size=1,
        gradient_accumulation_steps=args.gradient_accumulation_steps,
        learning_rate=args.learning_rate,
        warmup_ratio=args.warmup_ratio,
        logging_steps=args.logging_steps,
        save_steps=args.save_steps,
        save_total_limit=2,
        fp16=torch.cuda.is_available() and not use_bf16,
        bf16=use_bf16,
        report_to="none",
        remove_unused_columns=False,
        gradient_checkpointing=True,
    )

    trainer = Trainer(
        model=model,
        args=targs,
        train_dataset=train_ds,
        eval_dataset=eval_ds,
        data_collator=data_collator,
    )
    trainer.train()
    model.save_pretrained(str(out_dir))
    tokenizer.save_pretrained(str(out_dir))
    (out_dir / "train_args.json").write_text(
        json.dumps(vars(args), ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(f"完成。LoRA 权重与 tokenizer 已写入: {out_dir}")
    print("合并为完整权重（可选）: python LLM/merge_lora.py --base ... --adapter ... --out ...")


if __name__ == "__main__":
    main()
