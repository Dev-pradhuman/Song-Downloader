"""
Configuration manager for user settings.
Handles persistent user preferences such as the preferred download directory, bitrate, and UI theme.
"""

import json
from pathlib import Path
from typing import Any, Dict

from .paths import (
    get_settings_path,
    get_default_settings_path,
    get_default_download_dir,
    ensure_app_dirs
)


class ConfigManager:
    def __init__(self):
        ensure_app_dirs()
        self.settings_file = get_settings_path()
        self.default_file = get_default_settings_path()
        self._settings: Dict[str, Any] = self._load()

    def _load(self) -> Dict[str, Any]:
        """Load settings from JSON file with fallback to defaults."""
        defaults: Dict[str, Any] = {
            "version": 1,
            "download_directory": str(get_default_download_dir()),
            "audio_format": "mp3",
            "bitrate": "auto",
            "threads": 4,
            "theme": "dark"
        }

        if self.default_file.exists():
            try:
                with open(self.default_file, "r", encoding="utf-8") as f:
                    file_defaults = json.load(f)
                    defaults.update(file_defaults)
            except Exception:
                pass

        # If user settings file exists, overlay it
        if self.settings_file.exists():
            try:
                with open(self.settings_file, "r", encoding="utf-8") as f:
                    user_settings = json.load(f)
                    defaults.update(user_settings)
            except Exception:
                pass

        # Guarantee download_directory is a valid path string
        if not defaults.get("download_directory"):
            defaults["download_directory"] = str(get_default_download_dir())

        return defaults

    def get(self, key: str, default: Any = None) -> Any:
        """Get a configuration value."""
        return self._settings.get(key, default)

    def set(self, key: str, value: Any) -> None:
        """Set a configuration value and save to disk."""
        self._settings[key] = value
        self.save()

    def save(self) -> None:
        """Save settings safely via temporary file replacement."""
        temp_file = self.settings_file.with_suffix(".tmp")
        try:
            with open(temp_file, "w", encoding="utf-8") as f:
                json.dump(self._settings, f, indent=2, ensure_ascii=False)
            temp_file.replace(self.settings_file)
        except Exception as e:
            if temp_file.exists():
                temp_file.unlink(missing_ok=True)
            raise IOError(f"Failed to save settings: {e}")
