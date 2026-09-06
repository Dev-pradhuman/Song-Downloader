"""
Local dependency manager for Song Downloader.
Handles detection, secure downloading, safe archive extraction, verification,
and repair of locally-scoped application tools and runtimes.
"""

import json
import os
import platform
import shutil
import stat
import subprocess
import sys
import zipfile
from datetime import datetime
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Tuple

import requests

from .paths import (
    get_app_root,
    get_tools_dir,
    get_runtime_dir,
    get_dependencies_dir,
    get_temp_dir,
    get_dependencies_manifest_path,
    get_install_state_path,
    ensure_app_dirs,
)
from .env_manager import get_isolated_env


class DependencyError(Exception):
    """Raised when a dependency operation fails."""
    pass


class DependencyManager:
    def __init__(self):
        ensure_app_dirs()
        self.manifest_path = get_dependencies_manifest_path()
        self.install_state_path = get_install_state_path()
        self.manifest = self._load_manifest()

    def _load_manifest(self) -> Dict[str, Any]:
        """Load dependency definitions from config/dependencies.json."""
        if not self.manifest_path.exists():
            raise DependencyError(f"Missing dependency manifest at {self.manifest_path}")
        try:
            with open(self.manifest_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            raise DependencyError(f"Failed to read dependency manifest: {e}")

    def get_system_keys(self) -> Tuple[str, str]:
        """Detect normalized OS and machine architecture keys."""
        os_name = platform.system().lower()
        machine = platform.machine().lower()

        if "arm" in machine or "aarch64" in machine:
            arch = "arm64"
        elif "64" in machine or "amd64" in machine or "x86_64" in machine:
            arch = "amd64"
        else:
            arch = "x86"

        return os_name, arch

    def get_ffmpeg_path(self) -> Path:
        """Return the expected local path to ffmpeg."""
        binary_name = "ffmpeg.exe" if sys.platform == "win32" else "ffmpeg"
        return get_tools_dir() / "ffmpeg" / binary_name

    def get_deno_path(self) -> Path:
        """Return the expected local path to deno."""
        binary_name = "deno.exe" if sys.platform == "win32" else "deno"
        return get_runtime_dir() / "deno" / binary_name

    def verify_ffmpeg(self) -> Tuple[bool, str]:
        """Verify that local FFmpeg exists and functions correctly."""
        ffmpeg_exe = self.get_ffmpeg_path()
        if not ffmpeg_exe.is_file():
            return False, "FFmpeg binary is not installed locally."

        try:
            proc = subprocess.run(
                [str(ffmpeg_exe), "-version"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                timeout=10,
                creationflags=subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0,
            )
            if proc.returncode == 0:
                first_line = proc.stdout.splitlines()[0] if proc.stdout else "FFmpeg ready"
                return True, first_line
            return False, f"FFmpeg exited with error code {proc.returncode}"
        except Exception as e:
            return False, f"FFmpeg verification failed: {e}"

    def verify_deno(self) -> Tuple[bool, str]:
        """Verify that local Deno exists and functions correctly."""
        deno_exe = self.get_deno_path()
        if not deno_exe.is_file():
            return False, "Deno binary is not installed locally."

        try:
            proc = subprocess.run(
                [str(deno_exe), "--version"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                timeout=10,
                creationflags=subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0,
            )
            if proc.returncode == 0:
                first_line = proc.stdout.splitlines()[0] if proc.stdout else "Deno ready"
                return True, first_line
            return False, f"Deno exited with error code {proc.returncode}"
        except Exception as e:
            return False, f"Deno verification failed: {e}"

    def verify_python_packages(self) -> Tuple[bool, str]:
        """Verify that required python modules (spotdl, yt_dlp, customtkinter) are available."""
        required = ["spotdl", "yt_dlp", "customtkinter"]
        missing = []
        for mod in required:
            try:
                __import__(mod)
            except ImportError:
                missing.append(mod)

        if missing:
            return False, f"Missing Python modules: {', '.join(missing)}"
        return True, "All required Python engine libraries are loaded."

    def check_all(self) -> Dict[str, Dict[str, Any]]:
        """
        Check the status of all dependencies.
        Returns a dict mapping component -> {ok: bool, details: str, path: str}
        """
        ff_ok, ff_msg = self.verify_ffmpeg()
        deno_ok, deno_msg = self.verify_deno()
        py_ok, py_msg = self.verify_python_packages()

        return {
            "ffmpeg": {
                "ok": ff_ok,
                "details": ff_msg,
                "path": str(self.get_ffmpeg_path())
            },
            "deno": {
                "ok": deno_ok,
                "details": deno_msg,
                "path": str(self.get_deno_path())
            },
            "python_packages": {
                "ok": py_ok,
                "details": py_msg,
                "path": "current_environment"
            }
        }

    def is_fully_installed(self) -> bool:
        """Returns True if all required dependencies are present and verified."""
        status = self.check_all()
        return all(comp["ok"] for comp in status.values())

    def download_file(
        self,
        url: str,
        target_file: Path,
        progress_callback: Optional[Callable[[str, float], None]] = None,
        label: str = "Downloading"
    ) -> None:
        """
        Stream download a file via HTTPS with chunked progress updates.
        Recovers from interrupted downloads using a temporary file.
        """
        temp_file = target_file.with_suffix(".download.tmp")
        temp_file.parent.mkdir(parents=True, exist_ok=True)

        try:
            with requests.get(url, stream=True, timeout=30) as response:
                response.raise_for_status()
                total_size = int(response.headers.get("content-length", 0))
                downloaded = 0

                with open(temp_file, "wb") as f:
                    for chunk in response.iter_content(chunk_size=65536):
                        if chunk:
                            f.write(chunk)
                            downloaded += len(chunk)
                            if total_size > 0 and progress_callback:
                                frac = downloaded / total_size
                                progress_callback(label, frac)

            # Atomically replace target
            if target_file.exists():
                target_file.unlink()
            temp_file.replace(target_file)
        except Exception as e:
            if temp_file.exists():
                temp_file.unlink(missing_ok=True)
            raise DependencyError(f"Download failed for {url}: {e}")

    def safe_extract_zip(self, zip_path: Path, target_dir: Path) -> None:
        """
        Safely extract a zip archive preventing directory traversal (Zip Slip vulnerability).
        """
        target_dir.mkdir(parents=True, exist_ok=True)
        resolved_target = target_dir.resolve()

        with zipfile.ZipFile(zip_path, "r") as archive:
            for member in archive.infolist():
                member_path = (resolved_target / member.filename).resolve()
                if not str(member_path).startswith(str(resolved_target)):
                    raise DependencyError(f"Security error: Zip traversal detected for {member.filename}")
            archive.extractall(target_dir)

    def install_ffmpeg(self, progress_callback: Optional[Callable[[str, float], None]] = None) -> None:
        """Download and install FFmpeg into tools/ffmpeg/."""
        os_name, arch = self.get_system_keys()
        ffmpeg_cfg = self.manifest["dependencies"]["ffmpeg"]
        platform_info = ffmpeg_cfg.get("platforms", {}).get(os_name, {}).get(arch)
        if not platform_info:
            # Fallback for Windows amd64
            platform_info = ffmpeg_cfg.get("platforms", {}).get("windows", {}).get("amd64")

        url = platform_info["url"]
        target_exe = self.get_ffmpeg_path()
        target_exe.parent.mkdir(parents=True, exist_ok=True)

        # Check if already installed and working
        ok, _ = self.verify_ffmpeg()
        if ok:
            if progress_callback:
                progress_callback("FFmpeg already installed and verified", 1.0)
            return

        if progress_callback:
            progress_callback("Downloading FFmpeg binary...", 0.1)

        temp_target = get_temp_dir() / ("ffmpeg_dl.exe" if sys.platform == "win32" else "ffmpeg_dl")
        self.download_file(url, temp_target, progress_callback, label="Downloading FFmpeg")

        # Copy to destination and set executable permission
        if target_exe.exists():
            target_exe.unlink()
        shutil.move(str(temp_target), str(target_exe))

        if os.name != "nt":
            target_exe.chmod(target_exe.stat().st_mode | stat.S_IEXEC)

        # Verify
        ok, msg = self.verify_ffmpeg()
        if not ok:
            raise DependencyError(f"FFmpeg installed but failed verification: {msg}")

        if progress_callback:
            progress_callback(f"FFmpeg installed: {msg}", 1.0)

    def install_deno(self, progress_callback: Optional[Callable[[str, float], None]] = None) -> None:
        """Download and install Deno into runtime/deno/."""
        os_name, arch = self.get_system_keys()
        deno_cfg = self.manifest["dependencies"]["deno"]
        platform_info = deno_cfg.get("platforms", {}).get(os_name, {}).get(arch)
        if not platform_info:
            platform_info = deno_cfg.get("platforms", {}).get("windows", {}).get("amd64")

        url = platform_info["url"]
        target_exe = self.get_deno_path()
        target_exe.parent.mkdir(parents=True, exist_ok=True)

        # Check if already installed and working
        ok, _ = self.verify_deno()
        if ok:
            if progress_callback:
                progress_callback("Deno already installed and verified", 1.0)
            return

        if progress_callback:
            progress_callback("Downloading Deno archive...", 0.1)

        temp_zip = get_temp_dir() / "deno_download.zip"
        self.download_file(url, temp_zip, progress_callback, label="Downloading Deno")

        if progress_callback:
            progress_callback("Extracting Deno runtime...", 0.8)

        temp_extract = get_temp_dir() / "deno_extracted"
        shutil.rmtree(temp_extract, ignore_errors=True)
        self.safe_extract_zip(temp_zip, temp_extract)

        # Locate deno binary
        binary_name = platform_info.get("binary_name", "deno.exe" if sys.platform == "win32" else "deno")
        found_binary = None
        for root, _, files in os.walk(temp_extract):
            if binary_name in files:
                found_binary = Path(root) / binary_name
                break

        if not found_binary:
            raise DependencyError(f"Could not find {binary_name} in extracted Deno archive")

        if target_exe.exists():
            target_exe.unlink()
        shutil.move(str(found_binary), str(target_exe))

        if os.name != "nt":
            target_exe.chmod(target_exe.stat().st_mode | stat.S_IEXEC)

        # Cleanup
        temp_zip.unlink(missing_ok=True)
        shutil.rmtree(temp_extract, ignore_errors=True)

        # Verify
        ok, msg = self.verify_deno()
        if not ok:
            raise DependencyError(f"Deno installed but failed verification: {msg}")

        if progress_callback:
            progress_callback(f"Deno installed: {msg}", 1.0)

    def install_or_repair_all(
        self,
        progress_callback: Optional[Callable[[str, float], None]] = None,
        step_callback: Optional[Callable[[str], None]] = None
    ) -> bool:
        """
        Execute full step-by-step local installation and verification.
        Only downloads missing or broken dependencies.
        """
        ensure_app_dirs()

        # Step 1: Prepare directories
        if step_callback:
            step_callback("Preparing local directories...")
        ensure_app_dirs()

        # Step 2: Install FFmpeg
        if step_callback:
            step_callback("Installing FFmpeg...")
        self.install_ffmpeg(progress_callback)

        # Step 3: Install Deno runtime
        if step_callback:
            step_callback("Installing Deno runtime...")
        self.install_deno(progress_callback)

        # Step 4: Verify Python engine libraries
        if step_callback:
            step_callback("Verifying downloader engine...")
        py_ok, py_msg = self.verify_python_packages()
        if not py_ok:
            raise DependencyError(f"Engine library verification failed: {py_msg}")

        # Step 5: Final verification
        if step_callback:
            step_callback("Verifying complete installation...")
        checks = self.check_all()
        for comp, info in checks.items():
            if not info["ok"]:
                raise DependencyError(f"Verification failed for {comp}: {info['details']}")

        # Step 6: Persist install state manifest
        self._write_install_state(checks)

        if step_callback:
            step_callback("Song Downloader is ready.")

        return True

    def _write_install_state(self, checks: Dict[str, Any]) -> None:
        """Save installation state and component versions."""
        state = {
            "installed": True,
            "installed_at": datetime.now().isoformat(),
            "os": platform.system(),
            "arch": platform.machine(),
            "components": checks
        }
        with open(self.install_state_path, "w", encoding="utf-8") as f:
            json.dump(state, f, indent=2)
