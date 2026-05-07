# 一键开发启动：后端 + 三端 Vite，并注入本仓库训练产物（Qwen2.5-3B + qwen-lora-ocr-sft）。
# 需已存在 models\qwen\Qwen2.5-3B-Instruct\config.json 与 LLM\output\qwen-lora-ocr-sft\adapter_model.safetensors。
#
# 用法（仓库根）:
#   pwsh -NoProfile -ExecutionPolicy Bypass -File .\scripts\start-with-trained-llm.ps1
#   pwsh ... -Python "C:\Python312\python.exe"
#   pwsh ... -SkipDeps -BackendOnly

param(
    [string]$Python = '',
    [switch]$BackendOnly,
    [switch]$SkipDeps,
    [int]$BackendPort = 8000
)

$ErrorActionPreference = 'Stop'
$here = $PSScriptRoot
$start = Join-Path $here 'start-dev.ps1'
if ($Python -and $Python.Trim()) {
    & pwsh -NoProfile -ExecutionPolicy Bypass -File $start `
        -UseTrainedLlm `
        -BackendOnly:$BackendOnly `
        -SkipDeps:$SkipDeps `
        -BackendPort $BackendPort `
        -Python $Python.Trim()
}
else {
    & pwsh -NoProfile -ExecutionPolicy Bypass -File $start `
        -UseTrainedLlm `
        -BackendOnly:$BackendOnly `
        -SkipDeps:$SkipDeps `
        -BackendPort $BackendPort
}
