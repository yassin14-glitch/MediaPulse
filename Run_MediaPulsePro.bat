@echo off
cd /d "%~dp0"
if exist "dist\MediaPulsePro\MediaPulsePro.exe" (
    start "" "%~dp0dist\MediaPulsePro\MediaPulsePro.exe"
) else (
    echo [ERROR] Application not found at dist\MediaPulsePro\MediaPulsePro.exe
    echo Please run build.bat first to compile the application.
    pause
)
