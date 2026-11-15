@echo off
chcp 65001 >nul
cd /d "%~dp0"

set "PY="
where python >nul 2>nul && set "PY=python"
if not defined PY where py >nul 2>nul && set "PY=py -3"
if not defined PY (
    echo [NETWATCH] Python was not found. Install Python 3.8+ from https://www.python.org/downloads/
    echo           and tick "Add python.exe to PATH" during setup.
    pause
    exit /b 1
)

%PY% "app\netwatch.py"
if errorlevel 1 pause
