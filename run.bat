@echo off
setlocal enabledelayedexpansion

:: Determine directory where run.bat is located
set "APP_DIR=%~dp0"
cd /d "%APP_DIR%"

echo ===================================================
echo               Starting Song Downloader
echo ===================================================

:: Ensure local directories exist
if not exist "tools\ffmpeg" mkdir "tools\ffmpeg"
if not exist "runtime\deno" mkdir "runtime\deno"
if not exist "runtime\python_env" mkdir "runtime\python_env"
if not exist "cache\deno" mkdir "cache\deno"
if not exist "cache\spotdl" mkdir "cache\spotdl"
if not exist "logs" mkdir "logs"
if not exist "temp" mkdir "temp"

:: Setup isolated process environment variables
set "PATH=%APP_DIR%tools\ffmpeg;%APP_DIR%runtime\deno;%PATH%"
set "DENO_DIR=%APP_DIR%cache\deno"
set "SPOTDL_CACHE_DIR=%APP_DIR%cache\spotdl"
set "TEMP=%APP_DIR%temp"
set "TMP=%APP_DIR%temp"

:: Determine Python executable
set "PYTHON_EXE="

:: Check if local virtual environment exists
if exist "%APP_DIR%runtime\python_env\Scripts\python.exe" (
    set "PYTHON_EXE=%APP_DIR%runtime\python_env\Scripts\python.exe"
    set "PATH=%APP_DIR%runtime\python_env\Scripts;!PATH!"
) else (
    :: Check system python
    where python >nul 2>&1
    if !errorlevel! equ 0 (
        set "PYTHON_EXE=python"
    ) else (
        where py >nul 2>&1
        if !errorlevel! equ 0 (
            set "PYTHON_EXE=py"
        )
    )
)

if "%PYTHON_EXE%"=="" (
    echo [ERROR] Python was not found on this system.
    echo Please install Python 3.9+ or run "Song Downloader.exe" directly.
    pause
    exit /b 1
)

:: Check if Song Downloader.exe exists
if exist "%APP_DIR%Song Downloader.exe" (
    echo Launching Song Downloader executable...
    start "" "%APP_DIR%Song Downloader.exe"
    exit /b 0
)

:: Launch via Python script
echo Launching application via Python...
"%PYTHON_EXE%" "%APP_DIR%src\main.py"
if !errorlevel! neq 0 (
    echo.
    echo [ERROR] Application exited with error code !errorlevel!.
    echo Check logs\crash.log for details.
    pause
)
