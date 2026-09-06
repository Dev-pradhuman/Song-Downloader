"""
Dynamic application path resolution.
Ensures all internal application paths are derived dynamically from the application root.
No hardcoded developer paths are permitted.
"""

import os
import sys
from pathlib import Path
from typing import Optional


def get_app_root() -> Path:
    """
    Return the root directory of the Song Downloader application.
    Supports running as a script, inside a package, or compiled as a PyInstaller executable.
    """
    if getattr(sys, "frozen", False):
        # Running as PyInstaller executable
        return Path(sys.executable).resolve().parent
    else:
        # Running from source (src/core/paths.py -> root is 3 levels up)
        return Path(__file__).resolve().parent.parent.parent


def get_tools_dir() -> Path:
    """Return tools directory for locally managed binaries (e.g. ffmpeg)."""
    return get_app_root() / "tools"


def get_runtime_dir() -> Path:
    """Return runtime directory for locally managed runtimes (e.g. deno, local python env)."""
    return get_app_root() / "runtime"


def get_dependencies_dir() -> Path:
    """Return dependencies directory."""
    return get_app_root() / "dependencies"


def get_cache_dir() -> Path:
    """Return local cache directory for spotdl, yt-dlp, and deno caches."""
    return get_app_root() / "cache"


def get_logs_dir() -> Path:
    """Return local application logs directory."""
    return get_app_root() / "logs"


def get_temp_dir() -> Path:
    """Return local temporary directory for scratch downloads and extractions."""
    return get_app_root() / "temp"


def get_config_dir() -> Path:
    """Return application configuration directory."""
    return get_app_root() / "config"


def get_assets_dir() -> Path:
    """Return assets directory."""
    return get_app_root() / "assets"


def get_dependencies_manifest_path() -> Path:
    """Return path to dependencies manifest."""
    return get_config_dir() / "dependencies.json"


def get_install_state_path() -> Path:
    """Return path to install state / version manifest."""
    return get_config_dir() / "install_state.json"


def get_settings_path() -> Path:
    """Return path to user settings JSON."""
    return get_config_dir() / "settings.json"


def get_default_settings_path() -> Path:
    """Return path to default settings JSON."""
    return get_config_dir() / "settings.default.json"


def get_default_download_dir() -> Path:
    """
    Return the user's default OS Downloads directory.
    Never defaults to inside the application directory.
    """
    downloads_path = Path.home() / "Downloads"
    if downloads_path.exists():
        return downloads_path
    return Path.home()


def ensure_app_dirs() -> None:
    """Ensure all required local directories exist."""
    dirs = [
        get_tools_dir(),
        get_tools_dir() / "ffmpeg",
        get_runtime_dir(),
        get_runtime_dir() / "deno",
        get_dependencies_dir(),
        get_cache_dir(),
        get_cache_dir() / "deno",
        get_cache_dir() / "spotdl",
        get_logs_dir(),
        get_temp_dir(),
        get_config_dir(),
        get_assets_dir(),
    ]
    for d in dirs:
        d.mkdir(parents=True, exist_ok=True)
