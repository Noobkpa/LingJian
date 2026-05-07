$ErrorActionPreference = "Stop"

$Root = Split-Path -Parent $MyInvocation.MyCommand.Path
$BasePython = "C:\Users\28079\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe"
$Venv = Join-Path $Root ".venv"
$VenvPython = Join-Path $Venv "Scripts\python.exe"

if (-not (Test-Path $BasePython)) {
  throw "找不到 Python: $BasePython"
}

if (-not (Test-Path $VenvPython)) {
  & $BasePython -m venv $Venv
}

& $VenvPython -m pip install --upgrade pip
& $VenvPython -m pip install -r (Join-Path $Root "requirements.txt")

if ($LASTEXITCODE -ne 0) {
  exit $LASTEXITCODE
}

Write-Host "训练环境已准备好: $VenvPython"
Write-Host "现在可以运行: powershell -ExecutionPolicy Bypass -File .\retrain_local.ps1"
