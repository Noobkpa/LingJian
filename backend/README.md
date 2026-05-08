# 灵鉴后端服务

FastAPI 后端骨架，用于串联 OCR、BERT、LLM 三个模型：

```text
文本/图片/图文混合输入
-> OCR 文本化
-> BERT 多标签风险初判
-> LLM 结构化综合研判
-> 统一 JSON 输出
```

## 启动

```powershell
cd D:\LingJian
py -3.12 -m pip install -r requirement.txt
py -3.12 -m uvicorn backend.app.main:app --host 127.0.0.1 --port 8000
```

可选：`pip install -r backend/requirements.txt` 会包含根目录 `requirement.txt`（单一依赖清单）。

模型栈亦已在根目录 `requirement.txt` 中（numpy、tqdm、Paddle、torch 等）。若当前环境已装好 CUDA 版 `torch`，可避免重复覆盖：按需注释掉根目录文件中对应行再安装，或仅补装缺项（参见 `backend/requirements-model.txt` 说明）。

不再建议使用与其它包冲突的版本盲目覆盖；参见下文「当前已验证的本机组合」。

当前已验证的本机组合：

- Python: `C:\Users\HP\AppData\Local\Programs\Python\Python312\python.exe`
- PaddleOCR: `3.5.0`
- PaddlePaddle: `3.0.0`
- numpy: `2.3.5`
- torch: `2.9.1+cpu`

注意：PaddlePaddle `3.3.1` 在当前 Windows CPU 环境下触发 oneDNN 推理错误，已降到 `3.0.0`。

## 主要接口

- `GET /health`
- `POST /api/analyze/text`
- `POST /api/analyze/image`
- `POST /api/analyze/mixed`

接口文档：`http://127.0.0.1:8000/docs`

## 一键冒烟（可选）

启动服务后（建议设置 `LINGJIAN_LLM_MAX_NEW_TOKENS=384` 或按需调整）：

```powershell
python backend\scripts\e2e_pipeline_http.py --skip-mixed
```

`--skip-mixed`：跳过 `/api/analyze/mixed`，避免部分 Windows 环境下 Paddle 与 PyTorch 同进程不稳定；完整图文可使用默认命令（不设 `--skip-mixed`）。

结果写入 `backend\uploads\_e2e_pipeline_result.json`。

## 环境变量

| 变量 | 默认值 | 说明 |
| --- | --- | --- |
| `LINGJIAN_BERT_CHECKPOINT` | `Bert/bert_chinese_multilabel_out/best` | BERT checkpoint |
| `LINGJIAN_LLM_MODEL` | 若存在 `models/qwen/Qwen2.5-3B-Instruct` 则指向该目录，否则 `qwen/Qwen2.5-3B-Instruct` | HuggingFace 模型 id、或本地权重目录绝对路径 |
| `LINGJIAN_ENABLE_LLM` | 若本地 `Qwen2.5-3B-Instruct` 目录存在则为 `1`，否则 `0` | 是否启用真实 LLM 推理 |
| `LINGJIAN_LLM_PROVIDER` | `local` | `local` 走本地 Qwen，`external` 走 OpenAI-compatible 外部 API |
| `LINGJIAN_LLM_ADAPTER` | （空） | LoRA 目录；存在 `adapter_model.safetensors`（或 `.bin`）时自动挂载到基座 |
| `LINGJIAN_LLM_MAX_NEW_TOKENS` | `384` | 单次生成上限；过大易导致 `/analyze` 耗时很长 |
| `LINGJIAN_LLM_QUANTIZATION` | `8bit` | GPU：`8bit`（bitsandbytes）或 `16bit`（fp16）；CPU 始终 float32。不兼容时改 `16bit` |
| `LINGJIAN_EXTERNAL_LLM_BASE_URL` | `https://dashscope.aliyuncs.com/compatible-mode/v1` | 外部 LLM 的 OpenAI-compatible 基址 |
| `LINGJIAN_EXTERNAL_LLM_API_KEY` | （空） | 外部 LLM 的 API Key |
| `LINGJIAN_EXTERNAL_LLM_MODEL` | `qwen-plus` | 外部 LLM 模型名 |
| `LINGJIAN_EXTERNAL_LLM_TIMEOUT` | `120` | 外部 API 超时时间（秒） |
| `LINGJIAN_EXTERNAL_LLM_MAX_TOKENS` | `1024` | 外部 API 生成上限，避免结构化 JSON 被截断 |
| `LINGJIAN_EXTERNAL_LLM_JSON_MODE` | `0` | 部分兼容接口支持时可开启 JSON mode |
| `LINGJIAN_OCR_DEVICE` | `gpu` | PaddleOCR 设备，失败会自动尝试 CPU |

当仓库内已放置 `models/qwen/Qwen2.5-3B-Instruct`（含 `config.json`）时，**默认启用真实 Qwen**，首次命中分析接口时会加载权重。无该目录时仍默认关闭，避免误拉 Hugging Face 大模型。临时关闭可设 `LINGJIAN_ENABLE_LLM=0`。

### 外部 LLM API

如果你想在阿里云 Ubuntu / 普通 CPU 服务器上跑完整流程，推荐改成外部 API：

```env
LINGJIAN_ENABLE_LLM=1
LINGJIAN_LLM_PROVIDER=external
LINGJIAN_EXTERNAL_LLM_BASE_URL=https://dashscope.aliyuncs.com/compatible-mode/v1
LINGJIAN_EXTERNAL_LLM_API_KEY=你的百炼API_KEY
LINGJIAN_EXTERNAL_LLM_MODEL=qwen-plus
```

这样后端不再依赖本地 `models/qwen/...` 大模型权重，只要网络能访问外部接口即可。

### LLM 权重放置

1. 将 **Qwen2.5-3B-Instruct** 完整下载到仓库内 **`models/qwen/Qwen2.5-3B-Instruct/`**（与 HuggingFace 仓库目录结构一致，根目录含 `config.json`）。可用 `huggingface-cli download Qwen/Qwen2.5-3B-Instruct --local-dir models/qwen/Qwen2.5-3B-Instruct` 等方式。
2. 若设置了 `LINGJIAN_LLM_MODEL`，请指向该目录的绝对路径、或 HuggingFace 模型 id；也可留空走默认检测逻辑。
3. 更换模型后建议重启后端；若启用 Redis 推理缓存且需丢弃旧结果，可设置 `LINGJIAN_INFER_CACHE_VERSION` 或清理对应缓存键。
