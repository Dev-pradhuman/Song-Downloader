"""Build spotDL commands that work both from source and from PyInstaller."""

import sys
from typing import List


WORKER_FLAG = "--spotdl-worker"


def build_spotdl_command(*arguments: str) -> List[str]:
    """Return a command for running spotDL in the current application mode."""
    if getattr(sys, "frozen", False):
        # In a frozen app sys.executable is the GUI, not a Python interpreter.
        # Re-enter it through the worker dispatch implemented in src.main.
        return [sys.executable, WORKER_FLAG, *arguments]
    return [sys.executable, "-m", "spotdl", *arguments]
