@echo off
setlocal enabledelayedexpansion

echo ===================================================
echo   MediaPulse Pro - Windows Build and Package Script
echo ===================================================

:: Detect python executable (prefer .venv if available)
set PY_CMD=python
if exist ".venv\Scripts\python.exe" (
    set PY_CMD=.venv\Scripts\python.exe
    echo Using clean virtual environment: .venv
)

echo [1/4] Ensuring build assets and FFmpeg binary...
if not exist "assets\icon.ico" (
    echo Generating application icon...
    %PY_CMD% scripts\generate_icon.py
)

if not exist "bin\ffmpeg.exe" (
    echo Downloading static FFmpeg essentials to bin\ffmpeg.exe...
    %PY_CMD% -c "from core.ffmpeg_manager import FFmpegManager; FFmpegManager.download_ffmpeg()"
)

echo [2/4] Running test suite verification...
%PY_CMD% -m pytest tests -m "not slow" -q
if errorlevel 1 (
    echo [ERROR] Test suite failed! Halting build.
    exit /b 1
)

echo [3/4] Building MediaPulse Pro with PyInstaller (Onedir mode)...
%PY_CMD% -m PyInstaller --clean MediaPulsePro.spec --noconfirm
if errorlevel 1 (
    echo [ERROR] PyInstaller build failed!
    exit /b 1
)

echo [4/4] Verifying build output...
if exist "dist\MediaPulsePro\MediaPulsePro.exe" (
    echo.
    echo ===================================================
    echo   BUILD SUCCESSFUL!
    echo   Output directory: dist\MediaPulsePro
    echo   Executable: dist\MediaPulsePro\MediaPulsePro.exe
    echo ===================================================
) else (
    echo [ERROR] Build output not found!
    exit /b 1
)

echo.
echo Cleaning up temporary build directory...
if exist "build" rmdir /s /q "build"

echo.
echo Updating Desktop shortcut...
powershell -Command "$wsh = New-Object -ComObject WScript.Shell; $s = $wsh.CreateShortcut(\"$([Environment]::GetFolderPath('Desktop'))\MediaPulse Pro.lnk\"); $s.TargetPath = '%CD%\dist\MediaPulsePro\MediaPulsePro.exe'; $s.WorkingDirectory = '%CD%\dist\MediaPulsePro'; $s.IconLocation = '%CD%\dist\MediaPulsePro\assets\icon.ico'; $s.Description = 'MediaPulse Pro - Universal Video & Audio Downloader'; $s.Save()"

echo Done!
exit /b 0
