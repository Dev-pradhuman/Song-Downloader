"""
Filesystem naming sanitizer and collision handler.
Protects against forbidden characters, path traversal, long filenames, and duplicate collisions.
"""

import os
import re
from pathlib import Path
from typing import Union

# Characters forbidden on Windows filesystems
FORBIDDEN_CHARS_PATTERN = re.compile(r'[<>:"/\\|?*\x00-\x1f]')
RESERVED_NAMES = {
    "CON", "PRN", "AUX", "NUL",
    "COM1", "COM2", "COM3", "COM4", "COM5", "COM6", "COM7", "COM8", "COM9",
    "LPT1", "LPT2", "LPT3", "LPT4", "LPT5", "LPT6", "LPT7", "LPT8", "LPT9"
}


def sanitize_filename(filename: str, max_length: int = 180, default: str = "untitled") -> str:
    """
    Sanitize a filename so that it is safe for Windows and Linux filesystems.
    Preserves Unicode, diacritics, and normal spaces while stripping illegal characters.
    """
    if not filename:
        return default

    # Remove illegal characters
    cleaned = FORBIDDEN_CHARS_PATTERN.sub("", filename)

    # Replace consecutive spaces and strip trailing dots/spaces (Windows restriction)
    cleaned = re.sub(r"\s+", " ", cleaned).strip(" .")

    # If completely empty or reserved name, fallback
    if not cleaned or cleaned.upper() in RESERVED_NAMES:
        cleaned = f"{default}_{cleaned}" if cleaned else default

    # Truncate length while preserving extension if present
    if len(cleaned) > max_length:
        stem, ext = os.path.splitext(cleaned)
        allowed_stem_len = max(10, max_length - len(ext))
        cleaned = stem[:allowed_stem_len].strip(" .") + ext

    return cleaned


def resolve_unique_path(target_path: Union[str, Path]) -> Path:
    """
    If target_path already exists, generates a unique filename by appending (1), (2), etc.
    Avoids silent overwriting of user files.
    """
    path = Path(target_path).resolve()
    if not path.exists():
        return path

    parent = path.parent
    stem = path.stem
    suffix = path.suffix

    counter = 1
    while True:
        candidate = parent / f"{stem} ({counter}){suffix}"
        if not candidate.exists():
            return candidate
        counter += 1
