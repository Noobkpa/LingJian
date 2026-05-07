# 供 start-dev.ps1、pull-qwen-3b-and-train.ps1 点源共用：解析用户指定的 Python，或自动探测。
# 优先级：调用方传入的 -Python  >  环境变量 LINGJIAN_PYTHON  >  自动候选（py -3.13 … python3）。

function Resolve-LingjianPythonFromUserSpec {
    param([Parameter(Mandatory)][string]$Spec)
    $s = $Spec.Trim()
    if (-not $s) { return $null }

    $exePath = $null
    try {
        if (Test-Path -LiteralPath $s -PathType Leaf) {
            $exePath = (Resolve-Path -LiteralPath $s).Path
        }
    }
    catch { }
    if (-not $exePath) {
        $gc = Get-Command $s -ErrorAction SilentlyContinue
        if ($gc -and $gc.Source) { $exePath = $gc.Source }
    }
    if (-not $exePath) {
        Write-Host ('ERROR: 无法解析 Python，请检查路径或命令名：' + $s) -ForegroundColor Red
        return $null
    }

    $chk = 'import sys; v=sys.version_info; assert v.major==3 and (v.major,v.minor)>=(3,10), "need py3.10+"; print(sys.executable)'
    $out = & $exePath -c $chk 2>$null
    if ($LASTEXITCODE -ne 0) {
        Write-Host ('ERROR: 该解释器不可用或版本低于 3.10：' + $exePath) -ForegroundColor Red
        return $null
    }
    $line = ($out | Select-Object -Last 1).ToString().Trim()
    if (-not $line -or -not (Test-Path -LiteralPath $line)) {
        Write-Host ('ERROR: 校验脚本未返回可执行路径：' + $exePath) -ForegroundColor Red
        return $null
    }
    return $line
}

function Resolve-LingjianPythonAuto {
    $candidates = @(
        @('py', '-3.13'),
        @('py', '-3.12'),
        @('py', '-3.11'),
        @('py', '-3.10'),
        @('py'),
        @('python'),
        @('python3')
    )
    $check = 'import sys; v=sys.version_info; assert v.major==3 and (v.major,v.minor)>=(3,10); print(sys.executable)'
    foreach ($c in $candidates) {
        $argv = [System.Collections.Generic.List[string]]::new()
        foreach ($x in $c) { [void]$argv.Add($x) }
        [void]$argv.Add('-c')
        [void]$argv.Add($check)
        $exe = & $argv[0] $argv[1..($argv.Count - 1)] 2>$null
        if ($LASTEXITCODE -eq 0 -and $exe) {
            $path = ($exe | Select-Object -Last 1).ToString().Trim()
            if ($path -and (Test-Path -LiteralPath $path)) {
                return $path
            }
        }
    }
    return $null
}

function Resolve-LingjianPython {
    param([string]$ExplicitPython = '')
    $t = if ($null -ne $ExplicitPython) { $ExplicitPython.Trim() } else { '' }
    if (-not $t) {
        $ev = $env:LINGJIAN_PYTHON
        if ($null -ne $ev -and $ev.Trim()) { $t = $ev.Trim() }
    }
    if ($t) {
        Write-Host ('[python] 使用指定解释器（-Python 或 LINGJIAN_PYTHON）：' + $t) -ForegroundColor Cyan
        return (Resolve-LingjianPythonFromUserSpec $t)
    }
    Write-Host '[python] 未指定 -Python/LINGJIAN_PYTHON，按顺序自动探测 py -3.13 … python3 …' -ForegroundColor DarkGray
    return (Resolve-LingjianPythonAuto)
}
