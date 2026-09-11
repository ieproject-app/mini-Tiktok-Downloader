@echo off
title mini-TikTok-Downloader - SnipGeek Edition
set PYTHONDONTWRITEBYTECODE=1

cd /d "%~dp0"

echo ========================================================
echo   mini-TikTok-Downloader v1.0.0 - BY SNIPGEEK
echo ========================================================
echo.

python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python tidak terdeteksi!
    echo Silakan download Python 3.9+ dari https://www.python.org/
    echo.
    pause
    exit /b 1
)

python _engine\src\app.py %*

if errorlevel 1 (
    echo.
    echo [X] Terjadi error saat aplikasi berjalan.
    pause
)
