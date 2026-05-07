# 灵鉴 · Qwen 微调

本目录与 **后端推理**（`backend/app/services/llm_service.py`）独立；训练完成后，将合并目录或「基座 + LoRA」路径配置到环境变量 **`LINGJIAN_LLM_MODEL`** 即可接入服务。

## 数据格式

**JSONL**：每行一个 JSON 对象，必须包含 `messages` 数组，且 **最后一条** 为 `assistant`。

与灵鉴后端一致时，建议：

- `system`：伪科普研判专家说明 + 仅输出 JSON 的字段约定（可与 `llm_service.SYSTEM_PROMPT` 对齐）。
- `user`：「【文本】… + 【BERT报告】…」形式的拼接。
- `assistant`：**仅**模型应学习的 JSON 字符串（不要用 Markdown 代码围栏包裹）。

示例见 `data/example/train.jsonl`、`val.jsonl`。

### 使用 OCR 目录里的标签数据（推荐）

`ocr/train/augmented_label.txt`、`ocr/val/val_label.txt`、`ocr/test/test_label.txt` 为「图片相对路径 + Tab + 图中文字」。可用脚本对每条文字跑 **BERT**，自动生成与后端一致的 `messages` 并写出 JSONL：

```powershell
cd D:\LingJian
$env:PYTHONPATH = "D:\LingJian"
python LLM\build_dataset_from_ocr.py
```

默认输出：

- `LLM/data/ocr_sft/train.jsonl`
- `LLM/data/ocr_sft/val.jsonl`
- `LLM/data/ocr_sft/test.jsonl`

参数 `--limit_train` / `--limit_val` / `--limit_test` 可设为大于 0 的整数，只处理前 N 行（试跑用）。**全量**训练时不要加 limit。

生成后再训练：

```powershell
python LLM\train_sft.py `
  --train_file LLM\data\ocr_sft\train.jsonl `
  --eval_file LLM\data\ocr_sft\val.jsonl `
  --output_dir LLM\output\qwen-lora-ocr
```

说明：`assistant` 标签由 **BERT 输出映射** 得到（弱监督），用于让 Qwen 学会在相同 `system`/`user` 格式下输出与 BERT 一致的 JSON；若你有人工写的理想 `assistant`，可再替换或混合数据。

## 环境

建议在 **单独 venv** 中安装，避免与 PaddleOCR 等冲突：

```powershell
cd D:\LingJian
python -m venv .venv-llm
.\.venv-llm\Scripts\activate
pip install -r LLM/requirements-train.txt
```

需要 **GPU** 时安装对应 CUDA 的 `torch`；仅 CPU 可跑通逻辑但大模型仍较慢。

### 依赖版本（已写在 `requirements-train.txt`）

**Qwen2.5-3B-Instruct** 走 HuggingFace 标准实现，训练/推理依赖以仓库根目录 `requirement.txt` 为准即可；本目录 `requirements-train.txt` 为训练常用 pin（`transformers==4.38.2`、`peft==0.10.0` 等）。升级 `transformers` 前请对照 [PEFT](https://github.com/huggingface/peft) 与当前脚本兼容性自行验证。

### Windows 训练前环境变量（避免误拉 TensorFlow / Keras）

```powershell
$env:USE_TORCH = "1"
$env:USE_TF = "0"
```

### 本仓库内实测结论（供预期管理）

在 **无独立 GPU、内存有限** 的机器上，**仅加载 3B 权重做 LoRA 训练** 仍可能因内存/显存不足在 `Loading checkpoint shards` 中途失败。此前「推理」能跑通，不代表「训练 + 梯度 + 优化器状态」同等占用；**建议在显存充足的 GPU 机器或足够内存环境** 再执行 `train_sft.py`。成功训练后才会生成 `LLM/output/` 下的 adapter。

## 训练（LoRA）

默认基座为仓库内 `models/qwen/Qwen2.5-3B-Instruct`：

```powershell
cd D:\LingJian
python LLM/train_sft.py `
  --train_file LLM/data/example/train.jsonl `
  --eval_file LLM/data/example/val.jsonl `
  --output_dir LLM/output/qwen-lora-demo
```

常用参数：

| 参数 | 说明 |
|------|------|
| `--model_path` | 本地 Qwen 目录（含 `config.json`） |
| `--max_seq_length` | 最大序列长，默认 2048 |
| `--lora_r` / `--lora_alpha` | LoRA 秩与缩放 |
| `--num_train_epochs` | 训练轮数 |
| `--use_4bit` | 4bit 加载（需 `bitsandbytes`，Windows 常不可用） |

输出目录含 **adapter 权重**、`tokenizer` 与 `train_args.json`。

## 合并 LoRA（可选）

推理若不想用 `PeftModel` 动态挂载，可合并为完整权重：

```powershell
python LLM/merge_lora.py `
  --model_path models/qwen/Qwen2.5-3B-Instruct `
  --adapter_path LLM/output/qwen-lora-demo `
  --output_dir LLM/output/qwen-merged-demo
```

## 接入后端

```powershell
$env:LINGJIAN_LLM_MODEL = "D:\LingJian\LLM\output\qwen-merged-demo"
$env:LINGJIAN_ENABLE_LLM = "1"
```

若使用 **仅 LoRA 目录**（未合并），需改 `llm_service` 在加载时 `PeftModel.from_pretrained`；当前后端实现是直接 `from_pretrained` 单一路径，**合并后目录**最省事。

## 产物目录

`LLM/output/` 已加入 `.gitignore`，训练结果默认勿提交大文件。
