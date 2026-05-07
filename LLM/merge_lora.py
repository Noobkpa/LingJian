"""
将 LoRA adapter 与基座 Qwen 合并为单一目录，便于部署或再微调。

用法（在项目根目录）:
  python LLM/merge_lora.py --model_path models/qwen/Qwen2.5-3B-Instruct \\
    --adapter_path LLM/output/qwen-lora-run1 --output_dir LLM/output/qwen-merged
"""
from __future__ import annotations

import argparse

import torch
from peft import PeftModel
from transformers import AutoModelForCausalLM, AutoTokenizer


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--model_path", required=True, help="原始 Qwen 目录")
    p.add_argument("--adapter_path", required=True, help="train_sft.py 输出的 LoRA 目录")
    p.add_argument("--output_dir", required=True, help="合并后保存目录")
    args = p.parse_args()

    dtype = torch.float16 if torch.cuda.is_available() else torch.float32
    base = AutoModelForCausalLM.from_pretrained(
        args.model_path,
        trust_remote_code=True,
        torch_dtype=dtype,
        device_map="auto" if torch.cuda.is_available() else None,
        low_cpu_mem_usage=True,
    )
    model = PeftModel.from_pretrained(base, args.adapter_path)
    merged = model.merge_and_unload()
    merged.save_pretrained(args.output_dir)
    tok = AutoTokenizer.from_pretrained(args.model_path, trust_remote_code=True)
    tok.save_pretrained(args.output_dir)
    print(f"已保存合并模型: {args.output_dir}")


if __name__ == "__main__":
    main()
