"""
Process environment manager for runtime dependency and cache isolation.
Ensures child processes and external tools store runtime data inside the application directory.
"""

import os
import sys
from pathlib import Path
from typing import Dict, Optional

from .paths import (
    get_tools_dir,
    get_runtime_dir,
    get_cache_dir,
    get_temp_dir,
    get_logs_dir,
    ensure_app_dirs
)


def get_isolated_env(extra_env: Optional[Dict[str, str]] = None) -> Dict[str, str]:
    """
    Construct an environment dictionary with strict local paths prepended to PATH
    and caches redirected inside the application folder.
    """
    ensure_app_dirs()
    env = os.environ.copy()

    tools_dir = get_tools_dir()
    runtime_dir = get_runtime_dir()
    cache_dir = get_cache_dir()
    temp_dir = get_temp_dir()

    ffmpeg_dir = tools_dir / "ffmpeg"
    deno_dir = runtime_dir / "deno"

    # Prepend local tool paths to PATH
    path_entries = [str(ffmpeg_dir), str(deno_dir)]
    
    # If local python virtual environment exists, prepend its Scripts / bin folder
    if sys.platform == "win32":
        venv_bin = runtime_dir / "python_env" / "Scripts"
    else:
        venv_bin = runtime_dir / "python_env" / "bin"
    if venv_bin.exists():
        path_entries.insert(0, str(venv_bin))

    existing_path = env.get("PATH", "")
    separator = ";" if sys.platform == "win32" else ":"
    env["PATH"] = separator.join(path_entries) + separator + existing_path

    # Cache & runtime redirection
    env["DENO_DIR"] = str(cache_dir / "deno")
    env["SPOTDL_CACHE_DIR"] = str(cache_dir / "spotdl")
    env["TEMP"] = str(temp_dir)
    env["TMP"] = str(temp_dir)
    env["PYTHONPYCACHEPREFIX"] = str(cache_dir / "pycache")

    if extra_env:
        env.update(extra_env)

    return env


def apply_isolation_to_current_process() -> None:
    """Apply environment isolation directly to the currently running Python process."""
    isolated = get_isolated_env()
    for key, value in isolated.items():
        os.environ[key] = value
