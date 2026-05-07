# 下载 Qwen2.5-3B-Instruct 到 models/qwen/ 并对 ocr_sft 数据做 LoRA 微调（GPU 推荐）。
# 用法（仓库根）:
#   pwsh -NoProfile -ExecutionPolicy Bypass -File .\scripts\pull-qwen-3b-and-train.ps1
#   pwsh ... -Python "C:\Python312\python.exe"
#   pwsh ... -SkipDownload    # 已有权重时跳过下载
#   pwsh ... -TrainOnly       # 仅训练（假定权重已就绪）

param(
    [string]$Python = '',
    [switch]$SkipDownload,
    [switch]$TrainOnly
)

$ErrorActionPreference = 'Stop'
$Root = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path
Set-Location -LiteralPath $Root

. (Join-Path $PSScriptRoot 'Resolve-LingjianPython.ps1')
$PythonExe = Resolve-LingjianPython -ExplicitPython $Python
if (-not $PythonExe) {
    throw "未找到 Python 3.10+。请使用 -Python 指向 python.exe，或设置环境变量 LINGJIAN_PYTHON。"
}

function Invoke-Py {
    param([Parameter(Mandatory)][string[]]$Argv)
    & $PythonExe @Argv
    if ($LASTEXITCODE -ne 0) { throw "Python failed: $($Argv -join ' ')" }
}

$ModelDir = Join-Path $Root 'models\qwen\Qwen2.5-3B-Instruct'
$OutAdapter = Join-Path $Root 'LLM\output\qwen-lora-ocr-sft'

if (-not $TrainOnly) {
    if (-not $SkipDownload) {
        Write-Host '[pull-qwen-3b] snapshot_download ->' $ModelDir -ForegroundColor Cyan
        $dl = @'
import time
from pathlib import Path

from huggingface_hub import snapshot_download

root = Path(r"__ROOT__")
dest = root / "models" / "qwen" / "Qwen2.5-3B-Instruct"
dest.mkdir(parents=True, exist_ok=True)

last_err = None
for attempt in range(1, 9):
    try:
        print(f"[download] attempt {attempt}/8 ...")
        snapshot_download(
            repo_id="Qwen/Qwen2.5-3B-Instruct",
            local_dir=str(dest),
            resume_download=True,
            max_workers=1,
        )
        last_err = None
        break
    except Exception as e:
        last_err = e
        print(f"[download] failed: {e!r}")
        if attempt == 8:
            raise
        wait = min(30 * attempt, 180)
        print(f"[download] sleep {wait}s then resume (HF hub resumes partial files)")
        time.sleep(wait)

cfg = dest / "config.json"
assert cfg.is_file(), f"missing config.json under {dest}"
print("OK:", dest)
'@
        $dl = $dl.Replace('__ROOT__', $Root.Replace('\', '\\'))
        $tmp = Join-Path $env:TEMP 'lingjian_dl_qwen25.py'
        Set-Content -LiteralPath $tmp -Value $dl -Encoding utf8
        Invoke-Py -Argv @($tmp)
        Remove-Item -LiteralPath $tmp -Force
    }
}

if (-not (Test-Path -LiteralPath (Join-Path $ModelDir 'config.json'))) {
    throw "Missing model config.json under $ModelDir. Run without -SkipDownload."
}

Write-Host '[pull-qwen-3b] LoRA SFT ->' $OutAdapter -ForegroundColor Cyan
$trainArgs = @(
    'LLM/train_sft.py',
    '--model_path', $ModelDir,
    '--train_file', 'LLM/data/ocr_sft/train.jsonl',
    '--eval_file', 'LLM/data/ocr_sft/val.jsonl',
    '--output_dir', $OutAdapter,
    '--max_seq_length', '1536',
    '--num_train_epochs', '1',
    '--per_device_train_batch_size', '1',
    '--gradient_accumulation_steps', '4',
    '--save_steps', '100',
    '--logging_steps', '10'
)
Invoke-Py -Argv $trainArgs

Write-Host '[pull-qwen-3b] Done. 启动开发环境（已注入训练 LoRA）:' -ForegroundColor Green
Write-Host '  pwsh -NoProfile -ExecutionPolicy Bypass -File .\scripts\start-with-trained-llm.ps1 -SkipDeps' -ForegroundColor Yellow
Write-Host '  或双击 scripts\start-with-trained-llm.bat' -ForegroundColor Yellow
