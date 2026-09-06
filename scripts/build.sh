#!/usr/bin/env bash
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR/.."
ROOT_DIR="$(pwd)"

echo "==================================================="
echo "           Building Song Downloader"
echo "==================================================="

# Step 1: Clean
echo "[1/4] Cleaning previous build artifacts..."
rm -rf build dist *.spec

# Step 2: Validate
echo "[2/4] Validating source..."
python3 -m py_compile src/main.py src/core/*.py src/ui/*.py

# Step 3: Package
echo "[3/4] Packaging executable via PyInstaller..."
python3 -m PyInstaller \
    --noconfirm \
    --onefile \
    --name "Song Downloader" \
    --collect-all customtkinter \
    --collect-all spotdl \
    --collect-all yt_dlp \
    --collect-submodules src \
    --add-data "config:config" \
    --paths "src" \
    src/main.py

# Step 4: Deploy
echo "[4/4] Deploying executable..."
if [ -f "dist/Song Downloader" ]; then
    mv "dist/Song Downloader" "$ROOT_DIR/Song Downloader"
    chmod +x "$ROOT_DIR/Song Downloader"
fi
rm -rf build dist *.spec

echo "Build complete."
