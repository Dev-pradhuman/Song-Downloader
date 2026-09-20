"""
Song Downloader - Main Entry Point.
Bootstraps application path resolution, applies environment isolation,
and launches the graphical user interface.
"""

import os
import sys
import traceback
from pathlib import Path

# Ensure src parent directory is in sys.path
root_dir = Path(__file__).resolve().parent.parent
if str(root_dir) not in sys.path:
    sys.path.insert(0, str(root_dir))

from src.core.paths import ensure_app_dirs, get_logs_dir
from src.core.env_manager import apply_isolation_to_current_process
from src.core.spotdl_process import WORKER_FLAG


def run_spotdl_worker() -> int:
    """Run spotDL when the frozen executable is re-entered as a subprocess."""
    # Windowed PyInstaller applications may expose None for standard streams.
    # Prefer inherited subprocess pipes and fall back to the null device.
    for name, fd in (("stdout", 1), ("stderr", 2)):
        if getattr(sys, name) is None:
            try:
                stream = os.fdopen(
                    os.dup(fd), "w", buffering=1, encoding="utf-8", errors="replace"
                )
            except OSError:
                stream = open(os.devnull, "w", encoding="utf-8")
            setattr(sys, name, stream)

    sys.argv = [sys.argv[0], *sys.argv[2:]]
    apply_isolation_to_current_process()

    try:
        from spotdl import console_entry_point
        console_entry_point()
        return 0
    except SystemExit as exc:
        return exc.code if isinstance(exc.code, int) else 1


def main():
    try:
        # Step 1: Ensure application directories exist
        ensure_app_dirs()

        # Step 2: Apply runtime environment and cache isolation
        apply_isolation_to_current_process()

        # Step 3: Launch CustomTkinter application window
        from src.ui.app_window import AppWindow
        app = AppWindow()
        app.mainloop()

    except Exception as e:
        # Log unhandled crashes
        try:
            log_dir = get_logs_dir()
            log_dir.mkdir(parents=True, exist_ok=True)
            crash_file = log_dir / "crash.log"
            with open(crash_file, "a", encoding="utf-8") as f:
                f.write(f"=== Crash Report ===\n{traceback.format_exc()}\n\n")
        except Exception:
            pass

        # If tkinter is available, show error dialog
        try:
            import tkinter.messagebox as mb
            mb.showerror("Song Downloader Error", f"An unexpected error occurred:\n\n{e}\n\nSee logs/crash.log for details.")
        except Exception:
            print(f"FATAL ERROR: {e}", file=sys.stderr)
            traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == WORKER_FLAG:
        raise SystemExit(run_spotdl_worker())
    main()
