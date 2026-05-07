# 中文 BERT 多标签分类（本目录说明）

基于 **Google `bert-base-chinese`**（Hugging Face）在本地 **6 维多标签** 语料上微调，用于识别文本中的多类风险表述（标签顺序见 `dataset_info.json`）。

## 环境

```bash
cd Bert
pip install -r requirements.txt
```

国内下载模型若超时，可在 PowerShell 中先设置镜像再训练：

```powershell
$env:HF_ENDPOINT="https://hf-mirror.com"
```

## 数据

| 路径 | 说明 |
|------|------|
| `hf/train.jsonl` / `val.jsonl` / `test.jsonl` | 训练用 JSONL：`text`、`labels`（6 维 0/1）、可选 `weight` |
| `train/`、`val/`、`test/` | 同数据的 CSV 等导出 |
| `dataset_info.json` | 标签名称与统计 |

## 训练

```bash
python train_multilabel_bert.py --epochs 5 --batch_size 8
```

常用参数：

- `--lr`、`--max_length`（默认 **512**，与 `bert-base-chinese` 位置上限一致）、`--output_dir`
- `--threshold`：训练过程中验证用的**全局 logit** 阈值，默认 **0.0**（等价于 `sigmoid(logit) > 0.5`）
- `--best_metric`：`macro_f1`（默认）或 `exact_match`（六维全对比例），用于挑选写入 `best/` 的权重
- 损失函数对稀有标签使用 **BCE `pos_weight`**（由训练集正负比例自动计算）

训练结束后会在 **`best/thresholds.json`** 写入在验证集上搜索的 **logit 阈值**（默认 **单标量 global_only**：验证集 macro-F1 最大，小验证集更稳）。可用 `--threshold_strategy auto` 尝试与逐维阈值竞争。脚本会打印「对比用全局阈值」与「优化阈值」下的测试集指标。

**产出**：`bert_chinese_multilabel_out/best/`（`model.safetensors`、`config.json`、分词器、`thresholds.json`）。训练正常跑完后会额外写入 **`training_meta.json`**（本地结束时间、`max_length` 等超参、验证集最佳 epoch、保存的阈值及测试集指标摘要），便于核对「这次权重是按什么配置训出来的」。

## 长文本预测（分块 + logits max）

单条 `max_length` 推理默认最多 **512 token**。正文更长时，用 **`predict_long.py`**（按字分块，多块 logits 逐维取 max 再阈值化）：

- 按 **字** 切成多段（默认每段 ≤512 字，`--chunk_overlap` 可设重叠）；
- 每段照常 `max_length≤512` 过 BERT，对多块 **logits 逐维取 max** 再阈值化。

```bash
python predict_long.py --text "……长文……"
python predict_long.py --text_file article.txt --chunk_chars 512 --chunk_overlap 64
python predict_long.py --jsonl_in hf/test.jsonl --jsonl_out pred_long.jsonl
python predict_long.py --lines_file pure_text.txt
python predict_long.py --lines_file pure_text.txt --lines_preview 80
```

**注意**：`bert-base-chinese` 的 **`max_position_embeddings` 为 512**，`--max_length` 请勿大于 512。

### 计算公式（`total_score_pct` 与相关字段）

**符号**：多段文本时，先对每个文本块得到 6 维 logits，再对**每一维取最大值**得到聚合向量 \(\ell = (\ell_1,\ldots,\ell_6)\)（实现见 `long_text.aggregate_logits_max`）。单段时 \(\ell\) 即为该段输出。

**Step 1 — clip（数值稳定）**

\[
\tilde{\ell}_i = \operatorname{clip}(\ell_i,\,-500,\,500)
\]

**Step 2 — 逐维概率（sigmoid）**

\[
p_i = \sigma(\tilde{\ell}_i) = \frac{1}{1 + e^{-\tilde{\ell}_i}}, \quad i \in \{1,\ldots,6\}
\]

**Step 3 — 六维均值与峰值**

\[
\bar{p} = \frac{1}{6}\sum_{i=1}^{6} p_i, \qquad
p_{\max} = \max_{1 \le i \le 6} p_i
\]

**Step 4 — 融合（百分制前的无量纲强度）**

设 \(w_m = 0.3\)、\(w_M = 0.7\)（对应代码 `_TOTAL_SCORE_MEAN_WEIGHT`、`_TOTAL_SCORE_MAX_WEIGHT`，以 `predict_long.py` 为准）：

\[
\text{blend} = w_m \cdot \bar{p} + w_M \cdot p_{\max}
\]

**Step 5 — 总得分（0～100，一位小数）**

\[
\text{total\_score\_pct} = \operatorname{round}\bigl(\min(100,\; 100 \times \text{blend}),\,1\bigr)
\]

**分解字段（便于对照，不是再加权后的总分）**

\[
\text{score\_mean\_prob\_pct} = \operatorname{round}(100 \cdot \bar{p},\,1), \qquad
\text{score\_max\_prob\_pct} = \operatorname{round}(100 \cdot p_{\max},\,1)
\]

**命中占比（依赖阈值后的 `pred`）**

设 \(y_i \in \{0,1\}\) 为第 \(i\) 维预测，\(N=6\)：

\[
\text{hit\_rate\_pct} = \operatorname{round}\left(100 \cdot \frac{1}{N}\sum_{i=1}^{N} y_i,\,1\right)
\]

**与阈值的关系**：\(\ell\) 经 `thresholds.json`（或 `--threshold`）与 `apply_logits_threshold` 得到 \(y\)；**`total_score_pct` 只用 \(\ell\) → \(p\)**，不经过阈值。

### `--lines_file`（终端表）

- UTF-8 文本文件：**非空行**逐条调用与 `--text` 相同的推理路径，在终端打印**行号、总得分、命中%、六维缩写、命中标签、原文预览**。
- `--lines_preview`：原文预览最大字符数（默认 **56**），仅影响**显示**，推理仍用**整行**。
- 与 `--jsonl_in`、`--text`、`--text_file` **四选一**，不要混用。

## 脚本一览（推理后端相关）

| 文件 | 作用 |
|------|------|
| `train_multilabel_bert.py` | 微调多标签 BERT（可选，与线上推理解耦） |
| `thresholding.py` | 阈值搜索（训练侧）与推理时应用 `thresholds.json` |
| `long_text.py` | 长文本按字分块、logits max 聚合（供 `predict_long`） |
| `predict_long.py` | 长文本分块预测；`--text` / `--text_file` / `--jsonl_in`→`--jsonl_out` / `--lines_file` |
| `requirements.txt` | Python 依赖 |
