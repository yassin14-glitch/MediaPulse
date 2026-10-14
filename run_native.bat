@echo off
title Universal Video Downloader - Native GUI
echo Starting Native CustomTkinter Sidebar Application...
python main.py --native
if %ERRORLEVEL% NEQ 0 (
    echo.
    echo App closed with an error. Press any key to exit...
    pause >nul
)
