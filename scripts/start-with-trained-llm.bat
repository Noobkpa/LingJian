@echo off
chcp 65001 >nul
cd /d "%~dp0.."
echo Working dir: %CD%
echo.
set "PSRUN=powershell"
where pwsh >nul 2>&1 && set "PSRUN=pwsh"
%PSRUN% -NoProfile -ExecutionPolicy Bypass -File "%~dp0start-with-trained-llm.ps1" %*
set ERR=%ERRORLEVEL%
if %ERR% neq 0 goto fail
exit /b 0

:fail
echo.
echo Script exited with code %ERR%. Scroll up for PowerShell or pip errors.
pause
exit /b %ERR%
