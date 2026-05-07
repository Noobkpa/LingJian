# LAN start wrapper with trained LoRA.

param(
    [string]$Python = '',
    [switch]$BackendOnly,
    [switch]$SkipDeps,
    [int]$BackendPort = 8000,
    [string]$HostIp = ''
)

$ErrorActionPreference = 'Stop'
$here = $PSScriptRoot
$start = Join-Path $here 'start-lan.ps1'

if ($Python -and $Python.Trim()) {
    & pwsh -NoProfile -ExecutionPolicy Bypass -File $start `
        -UseTrainedLlm `
        -BackendOnly:$BackendOnly `
        -SkipDeps:$SkipDeps `
        -BackendPort $BackendPort `
        -HostIp $HostIp `
        -Python $Python.Trim()
}
else {
    & pwsh -NoProfile -ExecutionPolicy Bypass -File $start `
        -UseTrainedLlm `
        -BackendOnly:$BackendOnly `
        -SkipDeps:$SkipDeps `
        -BackendPort $BackendPort `
        -HostIp $HostIp
}
