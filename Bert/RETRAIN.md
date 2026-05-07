# BERT 重新训练说明

本项目的 BERT 是 6 维多标签分类模型，标签顺序见 `dataset_info.json`：

1. 绝对化用语
2. 术语堆砌
3. 虚假疗效
4. 标点异常
5. 数据篡改
6. 权威伪造

## 推荐重训方式

先准备训练环境：

```powershell
cd D:\codexproject\lingjian\Bert
.\install_train_env.ps1
```

优先从当前本地最优模型继续微调，而不是重新下载 `bert-base-chinese`：

```powershell
cd D:\codexproject\lingjian\Bert
.\retrain_local.ps1
```

输出目录：

```text
Bert\bert_chinese_multilabel_retrained\best
```

这套参数做了几件事：

- 使用本地 `bert_chinese_multilabel_out\best` 继续训练，避免重新下载基础模型。
- 学习率降到 `1e-5`，减少小数据集继续微调时的灾难性遗忘。
- 使用 `--threshold_strategy auto`，在验证集上比较全局阈值与逐标签阈值，缓解多标签任务中某些标签过报的问题。
- 输出新的 `thresholds.json` 和 `training_meta.json`，方便核对这次模型的指标与阈值。

## 当前阻塞

当前 Codex 沙箱运行时 Python 缺少训练依赖：

```text
torch
transformers
scikit-learn
tqdm
```

安装依赖时，沙箱环境对 pip 临时解包目录返回了权限错误，因此这次没有实际开训成功。在本机 PowerShell 中运行 `install_train_env.ps1` 后，再运行 `retrain_local.ps1` 即可。

## 精度继续提升建议

如果重新训练后仍不精准，优先检查数据而不是盲目加 epoch：

- 增加“正常科普但含专业术语”的硬负例，降低 `术语堆砌` 误报。
- 增加“提到治疗但表达审慎”的硬负例，降低 `虚假疗效` 误报。
- 为 `数据篡改`、`标点异常` 补充更多正例，当前这两类样本明显偏少。
- 对线上误判样本追加到 `hf/train.jsonl`，并保持 `val/test` 各有代表性误判样本。
