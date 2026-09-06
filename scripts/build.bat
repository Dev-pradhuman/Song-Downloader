@echo off
setlocal enabledelayedexpansion

:: Determine project root
set "SCRIPT_DIR=%~dp0"
cd /d "%SCRIPT_DIR%.."
set "ROOT_DIR=%CD%"

echo ===================================================
echo           Building Song Downloader Executable
echo ===================================================
echo Project Root: %ROOT_DIR%

:: Step 1: Clean stale build artifacts
echo [1/5] Cleaning previous build artifacts...
if exist "build" rd /s /q "build"
if exist "dist" rd /s /q "dist"
if exist "Song Downloader.spec" del /f /q "Song Downloader.spec"
if exist "Song Downloader.exe" del /f /q "Song Downloader.exe"

:: Step 2: Validate source syntax
echo [2/5] Validating Python source files...
python -m py_compile src\main.py src\core\paths.py src\core\env_manager.py src\core\dependency_manager.py src\core\metadata.py src\core\downloader_engine.py src\core\sanitizer.py src\core\config_manager.py src\ui\app_window.py src\ui\main_view.py src\ui\song_view.py src\ui\album_view.py src\ui\installer_view.py src\ui\components.py
if !errorlevel! neq 0 (
    echo [ERROR] Source code validation failed!
    exit /b 1
)
echo Source validated successfully.

:: Step 3: Package application via PyInstaller
echo [3/5] Building Song Downloader.exe via PyInstaller...
python -m PyInstaller ^
    --noconfirm ^
    --onefile ^
    --windowed ^
    --name "Song Downloader" ^
    --collect-all customtkinter ^
    --collect-all spotdl ^
    --collect-all yt_dlp ^
    --collect-submodules src ^
    --add-data "config;config" ^
    --paths "src" ^
    src\main.py

if !errorlevel! neq 0 (
    echo [ERROR] PyInstaller compilation failed!
    exit /b 1
)

:: Step 4: Move executable to project root
echo [4/5] Deploying Song Downloader.exe to project root...
if exist "dist\Song Downloader.exe" (
    move /y "dist\Song Downloader.exe" "%ROOT_DIR%\Song Downloader.exe"
    echo Successfully created "%ROOT_DIR%\Song Downloader.exe"
) else (
    echo [ERROR] Executable was not found in dist folder.
    exit /b 1
)

:: Step 5: Clean temporary build directories
echo [5/5] Cleaning temporary build folders...
if exist "build" rd /s /q "build"
if exist "dist" rd /s /q "dist"
if exist "Song Downloader.spec" del /f /q "Song Downloader.spec"

echo.
echo ===================================================
echo      Build Complete: Song Downloader.exe is ready!
echo ===================================================
