$ErrorActionPreference = "Stop"

$Root = Split-Path -Parent $MyInvocation.MyCommand.Path
$VenvPython = Join-Path $Root ".venv\Scripts\python.exe"
$Python = if (Test-Path $VenvPython) {
  $VenvPython
} else {
  "C:\Users\28079\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe"
}
$Deps = Join-Path $Root ".pydeps"
$Best = Join-Path $Root "bert_chinese_multilabel_out\best"
$Out = Join-Path $Root "bert_chinese_multilabel_retrained"

if (-not (Test-Path $Python)) {
  throw "找不到 Python: $Python"
}

if (Test-Path $Deps) {
  $env:PYTHONPATH = "$Deps;$env:PYTHONPATH"
}

if (-not (Test-Path (Join-Path $Best "model.safetensors"))) {
  throw "找不到本地 best 模型: $Best"
}

& $Python (Join-Path $Root "train_multilabel_bert.py") `
  --model_name $Best `
  --data_dir (Join-Path $Root "hf") `
  --output_dir $Out `
  --epochs 8 `
  --batch_size 4 `
  --lr 1e-5 `
  --warmup_ratio 0.08 `
  --weight_decay 0.02 `
  --threshold_strategy auto `
  --best_metric macro_f1

if ($LASTEXITCODE -ne 0) {
  exit $LASTEXITCODE
}
