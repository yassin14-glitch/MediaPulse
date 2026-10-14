@echo off
title Universal Video Downloader
echo Starting Universal Video Downloader Desktop App...
python main.py
if %ERRORLEVEL% NEQ 0 (
    echo.
    echo App closed with an error. Press any key to exit...
    pause >nul
)
