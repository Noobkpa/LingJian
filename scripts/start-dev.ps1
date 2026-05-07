# Lingjian: pip + migrate + backend + portal (3080) + three Vite apps (3000/3001/3002).
#
# LLM (LINGJIAN_ENABLE_LLM): not set by default; backend config enables when Qwen bundle exists.
#   -EnableLlm      force env LINGJIAN_ENABLE_LLM=1
#   -DisableLlm     force env LINGJIAN_ENABLE_LLM=0
#   -UseTrainedLlm   inject LINGJIAN_LLM_MODEL + LINGJIAN_LLM_ADAPTER (qwen-lora-ocr-sft) + ENABLE + cache bump
#   -SkipDeps        skip pip / npm install
#
# Usage (prefer PowerShell 7: pwsh):
#   pwsh -NoProfile -ExecutionPolicy Bypass -File .\scripts\start-dev.ps1
#   pwsh ... -Python "C:\Path\python.exe"     # 或先 set LINGJIAN_PYTHON=同路径，再运行脚本
#   pwsh ... -SkipDeps -BackendOnly
#   pwsh -NoProfile -ExecutionPolicy Bypass -File .\scripts\start-with-trained-llm.ps1 -SkipDeps
# start-dev.bat picks pwsh when installed, else Windows PowerShell 5.
# 未指定 -Python 且未设置 LINGJIAN_PYTHON 时，将依次尝试 py -3.13 … python3（见 scripts\Resolve-LingjianPython.ps1）。

param(
    [string]$Python = '',
    [switch]$BackendOnly,
    [switch]$SkipDeps,
    [int]$BackendPort = 8000,
    [switch]$EnableLlm,
    [switch]$DisableLlm,
    [switch]$UseTrainedLlm
)

$ErrorActionPreference = 'Stop'
[Console]::OutputEncoding = [System.Text.UTF8Encoding]::new()

$Root = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path
Set-Location -LiteralPath $Root

. (Join-Path $PSScriptRoot 'Resolve-LingjianPython.ps1')

$RunDir = Join-Path $env:TEMP 'LingJian-StartDev'
New-Item -ItemType Directory -Path $RunDir -Force | Out-Null

function New-CmdSetLine {
    param([Parameter(Mandatory)][string]$Name, [Parameter(Mandatory)][string]$Value)
    return 'set "' + $Name + '=' + ($Value -replace '"', '""') + '"'
}

function Write-DevCmd {
    param(
        [Parameter(Mandatory)][string]$Path,
        [Parameter(Mandatory)][string[]]$Lines
    )
    Set-Content -LiteralPath $Path -Value $Lines -Encoding ascii
}

function Start-DevCmdWindow {
    param([Parameter(Mandatory)][string]$CmdPath)
    Start-Process -FilePath $CmdPath
}

if ($EnableLlm -and $DisableLlm) {
    Write-Host 'ERROR: use only one of -EnableLlm or -DisableLlm.' -ForegroundColor Red
    exit 1
}
if ($UseTrainedLlm -and $DisableLlm) {
    Write-Host 'ERROR: -UseTrainedLlm conflicts with -DisableLlm.' -ForegroundColor Red
    exit 1
}

Write-Host '========================================' -ForegroundColor Cyan
Write-Host (' Lingjian dev start  Root=' + $Root) -ForegroundColor Cyan
Write-Host '========================================' -ForegroundColor Cyan

$PythonExe = Resolve-LingjianPython -ExplicitPython $Python
if (-not $PythonExe) {
    Write-Host 'ERROR: 未找到可用的 Python 3.10+。请安装后重试，或使用：' -ForegroundColor Red
    Write-Host '  -Python "C:\Path\python.exe"   或   $env:LINGJIAN_PYTHON="同上"' -ForegroundColor Yellow
    exit 1
}
Write-Host ('python: ' + $PythonExe) -ForegroundColor Yellow
Write-Host '  (Backend uses this Python; uvicorn from another interpreter will not match these deps.)' -ForegroundColor DarkGray

$env:PYTHONPATH = $Root

if (-not $SkipDeps) {
    Write-Host 'STEP: pip install -r requirement.txt ...' -ForegroundColor Yellow
    & $PythonExe -m pip install -r (Join-Path $Root 'requirement.txt')
    if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
    if ($EnableLlm) {
        Write-Host 'STEP: LLM stack sync (transformers<4.57 + einops + stream gen) ...' -ForegroundColor Yellow
        & $PythonExe -m pip install @(
            'transformers>=4.38,<4.57'
            'einops>=0.7.0'
            'transformers_stream_generator>=0.0.4'
            'tiktoken>=0.7.0'
        )
        if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
        Write-Host 'STEP: verify LLM imports (backend/scripts/check_llm_env.py) ...' -ForegroundColor Yellow
        & $PythonExe (Join-Path $Root 'backend\scripts\check_llm_env.py')
        if ($LASTEXITCODE -ne 0) {
            Write-Host 'ERROR: LLM env does not match this Python; fix deps for the python path printed above.' -ForegroundColor Red
            exit $LASTEXITCODE
        }
    }
}
else {
    Write-Host 'STEP: skipped pip (-SkipDeps)' -ForegroundColor DarkGray
}

Write-Host 'STEP: alembic upgrade head ...' -ForegroundColor Yellow
& $PythonExe -m alembic -c (Join-Path $Root 'backend\alembic.ini') upgrade head
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

$backendCmd = Join-Path $RunDir 'lingjian-backend.cmd'
$backendLines = [System.Collections.Generic.List[string]]::new()
[void]$backendLines.Add('@echo off')
[void]$backendLines.Add('setlocal')
[void]$backendLines.Add('chcp 65001>nul')
[void]$backendLines.Add((New-CmdSetLine 'LINGJIAN_ROOT' $Root))
[void]$backendLines.Add((New-CmdSetLine 'LINGJIAN_PY' $PythonExe))
[void]$backendLines.Add('cd /d "%LINGJIAN_ROOT%"')
[void]$backendLines.Add('set "PYTHONPATH=%LINGJIAN_ROOT%"')

if ($EnableLlm) {
    Write-Host 'LLM: LINGJIAN_ENABLE_LLM=1 [EnableLlm]' -ForegroundColor Yellow
    [void]$backendLines.Add('set "LINGJIAN_ENABLE_LLM=1"')
    [void]$backendLines.Add('echo LINGJIAN_ENABLE_LLM=1 (start-dev -EnableLlm)')
}
elseif ($DisableLlm) {
    Write-Host 'LLM: LINGJIAN_ENABLE_LLM=0 [DisableLlm]' -ForegroundColor Yellow
    [void]$backendLines.Add('set "LINGJIAN_ENABLE_LLM=0"')
    [void]$backendLines.Add('echo LINGJIAN_ENABLE_LLM=0 (start-dev -DisableLlm)')
}
else {
    $qwenCfg = Join-Path $Root 'models\qwen\Qwen2.5-3B-Instruct\config.json'
    if (Test-Path -LiteralPath $qwenCfg) {
        Write-Host '[LLM] Qwen bundle found; backend may enable LLM. Override with -EnableLlm or -DisableLlm.' -ForegroundColor DarkGray
    }
    else {
        Write-Host '[LLM] No local Qwen bundle; heuristic mode unless you pass -EnableLlm.' -ForegroundColor DarkGray
    }
}

if ($UseTrainedLlm) {
    $llmModelDir = Join-Path $Root 'models\qwen\Qwen2.5-3B-Instruct'
    $llmAdapterDir = Join-Path $Root 'LLM\output\qwen-lora-ocr-sft'
    $llmCfg = Join-Path $llmModelDir 'config.json'
    $llmAdapterW = Join-Path $llmAdapterDir 'adapter_model.safetensors'
    if (-not (Test-Path -LiteralPath $llmCfg)) {
        Write-Host ('ERROR: -UseTrainedLlm requires ' + $llmCfg) -ForegroundColor Red
        exit 1
    }
    if (-not (Test-Path -LiteralPath $llmAdapterW)) {
        Write-Host ('ERROR: -UseTrainedLlm requires ' + $llmAdapterW + ' (run scripts\\pull-qwen-3b-and-train.ps1 first).') -ForegroundColor Red
        exit 1
    }
    $llmModelAbs = (Resolve-Path -LiteralPath $llmModelDir).Path
    $llmAdapterAbs = (Resolve-Path -LiteralPath $llmAdapterDir).Path
    Write-Host ('[LLM] Using trained LoRA: ' + $llmAdapterAbs) -ForegroundColor Green
    [void]$backendLines.Add((New-CmdSetLine 'LINGJIAN_LLM_MODEL' $llmModelAbs))
    [void]$backendLines.Add((New-CmdSetLine 'LINGJIAN_LLM_ADAPTER' $llmAdapterAbs))
    [void]$backendLines.Add((New-CmdSetLine 'LINGJIAN_ENABLE_LLM' '1'))
    [void]$backendLines.Add((New-CmdSetLine 'LINGJIAN_INFER_CACHE_VERSION' '2'))
}

[void]$backendLines.Add(('title Lingjian Backend :' + $BackendPort))
[void]$backendLines.Add('call "%LINGJIAN_PY%" -m uvicorn backend.app.main:app --host 127.0.0.1 --port ' + [string]$BackendPort)
[void]$backendLines.Add('echo.')
[void]$backendLines.Add('echo Backend exited. Press any key to close.')
[void]$backendLines.Add('pause >nul')

Write-DevCmd -Path $backendCmd -Lines $backendLines

Write-Host ('STEP: starting backend (see new window). Docs: http://127.0.0.1:' + [string]$BackendPort + '/docs') -ForegroundColor Green
Start-DevCmdWindow -CmdPath $backendCmd

if ($BackendOnly) {
    Write-Host 'Done (backend only). Run npm run dev in each frontend folder.' -ForegroundColor Green
    exit 0
}

$node = Get-Command node -ErrorAction SilentlyContinue
$npm = Get-Command npm -ErrorAction SilentlyContinue
if (-not $node -or -not $npm) {
    Write-Host 'ERROR: node or npm not in PATH. Install Node 18+ then retry.' -ForegroundColor Red
    Write-Host 'Backend window is already open.' -ForegroundColor DarkYellow
    exit 1
}

$apps = @(
    @{ Dir = 'fake-science-identify-all'; Title = 'Lingjian Portal (main) :3080' },
    @{ Dir = 'fake-science-identify-user';  Title = 'Lingjian User :3000' },
    @{ Dir = 'fake-science-identify-admin'; Title = 'Lingjian Admin :3001' },
    @{ Dir = 'fake-science-identify-audit'; Title = 'Lingjian Audit :3002' }
)

foreach ($a in $apps) {
    $dirPath = Join-Path $Root $a.Dir
    if (-not (Test-Path -LiteralPath $dirPath)) {
        Write-Host ('SKIP: missing dir ' + $a.Dir) -ForegroundColor DarkYellow
        continue
    }

    if (-not $SkipDeps) {
        $nm = Join-Path $dirPath 'node_modules'
        if (-not (Test-Path -LiteralPath $nm)) {
            Write-Host ('STEP: npm install in ' + $a.Dir + ' ...') -ForegroundColor Yellow
            Push-Location -LiteralPath $dirPath
            npm install
            if ($LASTEXITCODE -ne 0) {
                Pop-Location
                exit $LASTEXITCODE
            }
            Pop-Location
        }
    }

    $safeName = ($a.Dir -replace '[^a-zA-Z0-9_-]', '_')
    $viteCmd = Join-Path $RunDir ('lingjian-vite-' + $safeName + '.cmd')
    $viteLines = @(
        '@echo off'
        'setlocal'
        'chcp 65001>nul'
        (New-CmdSetLine 'APP_DIR' $dirPath)
        'cd /d "%APP_DIR%"'
        ('title ' + $a.Title)
        'npm run dev -- --host 127.0.0.1'
        'echo.'
        'echo Vite exited. Press any key to close.'
        'pause >nul'
    )
    Write-DevCmd -Path $viteCmd -Lines $viteLines
    Write-Host $a.Title -ForegroundColor Green
    Start-DevCmdWindow -CmdPath $viteCmd
}

Write-Host
Write-Host 'Started in new windows.' -ForegroundColor Cyan
Write-Host ('  API docs    http://127.0.0.1:' + [string]$BackendPort + '/docs')
Write-Host '  Portal (main)  http://127.0.0.1:3080   ← 灵鉴统一入口（仅此端 Vite 会尝试自动打开浏览器）'
Write-Host '  User UI        http://127.0.0.1:3000   （从门户进入，或手动打开）'
Write-Host '  Admin UI       http://127.0.0.1:3001'
Write-Host '  Audit UI       http://127.0.0.1:3002'
Write-Host
Write-Host 'Close the cmd windows to stop servers.' -ForegroundColor DarkGray
