"""
Downloader engine for executing media downloads using spotdl and yt-dlp
with local dependency isolation, real-time logging, and progress reporting.
"""

import os
import subprocess
import sys
import threading
from datetime import datetime
from pathlib import Path
from typing import Callable, List, Optional

from .paths import get_logs_dir, ensure_app_dirs
from .env_manager import get_isolated_env
from .sanitizer import sanitize_filename


class DownloaderEngine:
    def __init__(self):
        ensure_app_dirs()
        self.log_file = get_logs_dir() / "download.log"
        self._current_process: Optional[subprocess.Popen] = None
        self._is_cancelled = False

    def log(self, message: str) -> None:
        """Append log message to logs/download.log."""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        entry = f"[{timestamp}] {message}\n"
        try:
            with open(self.log_file, "a", encoding="utf-8") as f:
                f.write(entry)
        except Exception:
            pass

    def cancel(self) -> None:
        """Cancel the currently active download."""
        self._is_cancelled = True
        if self._current_process and self._current_process.poll() is None:
            try:
                self._current_process.terminate()
            except Exception:
                pass

    def download_tracks(
        self,
        track_urls: List[str],
        output_dir: Path,
        threads: int = 4,
        log_callback: Optional[Callable[[str], None]] = None,
        progress_callback: Optional[Callable[[int, int, str], None]] = None,
    ) -> bool:
        """
        Download a specific list of track URLs to output_dir.
        Selective downloading: only URLs in track_urls are downloaded.
        """
        if not track_urls:
            if log_callback:
                log_callback("No tracks selected for download.")
            return False

        output_dir = Path(output_dir).resolve()
        output_dir.mkdir(parents=True, exist_ok=True)

        self._is_cancelled = False
        total_tracks = len(track_urls)
        completed_count = 0

        self.log(f"Starting download of {total_tracks} track(s) to: {output_dir}")
        if log_callback:
            log_callback(f"Target directory: {output_dir}")
            log_callback(f"Downloading {total_tracks} selected track(s)...")

        env = get_isolated_env()

        # Build spotdl download command
        cmd = [
            sys.executable,
            "-m",
            "spotdl",
            "download",
            *track_urls,
            "--threads",
            str(threads),
        ]

        try:
            self._current_process = subprocess.Popen(
                cmd,
                cwd=str(output_dir),
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,
                env=env,
                creationflags=subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0,
            )

            for line in self._current_process.stdout:
                line_str = line.strip()
                if not line_str:
                    continue

                self.log(line_str)
                if log_callback:
                    log_callback(line_str)

                # Check if a track was completed
                if "Downloaded " in line_str or "Skipping " in line_str:
                    completed_count += 1
                    if progress_callback:
                        progress_callback(min(completed_count, total_tracks), total_tracks, line_str)

            self._current_process.wait()
            return_code = self._current_process.returncode

            if self._is_cancelled:
                self.log("Download was cancelled by user.")
                if log_callback:
                    log_callback("Download cancelled.")
                return False

            if return_code == 0:
                self.log(f"Successfully finished downloading {completed_count}/{total_tracks} tracks.")
                if progress_callback:
                    progress_callback(total_tracks, total_tracks, "Complete")
                if log_callback:
                    log_callback(f"Download complete! Saved to {output_dir}")
                return True
            else:
                self.log(f"Process finished with return code {return_code}")
                if log_callback:
                    log_callback(f"Download finished with warnings or errors (code {return_code}).")
                return completed_count > 0

        except Exception as e:
            self.log(f"Error during download: {e}")
            if log_callback:
                log_callback(f"Error: {e}")
            return False
        finally:
            self._current_process = None
