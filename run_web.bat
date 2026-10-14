@echo off
title Universal Video Downloader - Web Dashboard
echo Starting Universal Video Downloader Web Dashboard...
python main.py --web
if %ERRORLEVEL% NEQ 0 (
    echo.
    echo Server closed with an error. Press any key to exit...
    pause >nul
)
