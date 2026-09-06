#!/usr/bin/env bash
set -e

# Determine directory where run.sh is located
APP_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$APP_DIR"

echo "==================================================="
echo "              Starting Song Downloader"
echo "==================================================="

# Ensure local directories exist
mkdir -p "$APP_DIR/tools/ffmpeg"
mkdir -p "$APP_DIR/runtime/deno"
mkdir -p "$APP_DIR/runtime/python_env"
mkdir -p "$APP_DIR/cache/deno"
mkdir -p "$APP_DIR/cache/spotdl"
mkdir -p "$APP_DIR/logs"
mkdir -p "$APP_DIR/temp"

# Prepend local tools to PATH
export PATH="$APP_DIR/tools/ffmpeg:$APP_DIR/runtime/deno:$PATH"
export DENO_DIR="$APP_DIR/cache/deno"
export SPOTDL_CACHE_DIR="$APP_DIR/cache/spotdl"
export TEMP="$APP_DIR/temp"
export TMP="$APP_DIR/temp"

# Locate Python
PYTHON_BIN=""
if [ -f "$APP_DIR/runtime/python_env/bin/python3" ]; then
    PYTHON_BIN="$APP_DIR/runtime/python_env/bin/python3"
    export PATH="$APP_DIR/runtime/python_env/bin:$PATH"
elif command -v python3 >/dev/null 2>&1; then
    PYTHON_BIN="python3"
elif command -v python >/dev/null 2>&1; then
    PYTHON_BIN="python"
fi

if [ -z "$PYTHON_BIN" ]; then
    echo "[ERROR] Python 3 was not found on this system."
    exit 1
fi

"$PYTHON_BIN" "$APP_DIR/src/main.py"
