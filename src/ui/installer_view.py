"""
Dependency installer and repair UI view.
Handles first-run component check, user confirmation, real-time installation progress,
and post-installation verification.
"""

import sys
import threading
from typing import Callable, Optional

import customtkinter as ctk

from ..core.dependency_manager import DependencyManager, DependencyError
from .components import ACCENT_GREEN, ACCENT_GREEN_HOVER, CARD_BG, ERROR_RED, TEXT_MUTED, LogBox


class InstallerView(ctk.CTkFrame):
    def __init__(self, master, on_success: Callable[[], None], on_exit: Callable[[], None], repair_mode: bool = False, **kwargs):
        super().__init__(master, fg_color="transparent", **kwargs)
        self.on_success = on_success
        self.on_exit = on_exit
        self.repair_mode = repair_mode
        self.dep_manager = DependencyManager()

        self.grid_columnconfigure(0, weight=1)

        # Card container
        self.card = ctk.CTkFrame(self, fg_color=CARD_BG, corner_radius=12)
        self.card.grid(row=0, column=0, padx=40, pady=40, sticky="nsew")
        self.card.grid_columnconfigure(0, weight=1)

        # Title
        title_text = "Repair Dependencies" if self.repair_mode else "Song Downloader"
        self.title_lbl = ctk.CTkLabel(
            self.card,
            text=title_text,
            font=ctk.CTkFont(size=26, weight="bold"),
        )
        self.title_lbl.grid(row=0, column=0, padx=20, pady=(30, 10))

        # Subtitle
        sub_text = (
            "Verify and repair required application components."
            if self.repair_mode
            else "Required components are not installed.\nSong Downloader installs its dependencies locally inside this folder."
        )
        self.subtitle_lbl = ctk.CTkLabel(
            self.card,
            text=sub_text,
            font=ctk.CTkFont(size=14),
            text_color=TEXT_MUTED,
            justify="center",
        )
        self.subtitle_lbl.grid(row=1, column=0, padx=20, pady=(0, 20))

        # Checklist frame
        self.checklist_frame = ctk.CTkFrame(self.card, fg_color="transparent")
        self.checklist_frame.grid(row=2, column=0, padx=40, pady=10, sticky="ew")
        self.checklist_frame.grid_columnconfigure(0, weight=1)

        self.steps = [
            ("dirs", "Preparing local directories"),
            ("ffmpeg", "Installing local FFmpeg"),
            ("deno", "Installing local Deno runtime"),
            ("engine", "Verifying downloader engine"),
            ("verify", "Verifying installation"),
        ]
        self.step_labels = {}
        for idx, (key, label) in enumerate(self.steps):
            lbl = ctk.CTkLabel(
                self.checklist_frame,
                text=f"○  {label}",
                font=ctk.CTkFont(size=13),
                text_color=TEXT_MUTED,
                anchor="w",
            )
            lbl.grid(row=idx, column=0, sticky="w", pady=3)
            self.step_labels[key] = lbl

        # Progress bar
        self.progress_bar = ctk.CTkProgressBar(self.card, height=10, corner_radius=5)
        self.progress_bar.grid(row=3, column=0, padx=40, pady=(20, 10), sticky="ew")
        self.progress_bar.set(0)

        # Status text
        self.status_lbl = ctk.CTkLabel(
            self.card,
            text="Ready to install" if not self.repair_mode else "Ready to repair",
            font=ctk.CTkFont(size=12),
            text_color=TEXT_MUTED,
        )
        self.status_lbl.grid(row=4, column=0, padx=20, pady=(0, 15))

        # Log box (initially collapsed/small)
        self.log_box = LogBox(self.card, height=100)
        self.log_box.grid(row=5, column=0, padx=40, pady=(0, 20), sticky="nsew")

        # Action Buttons
        self.btn_frame = ctk.CTkFrame(self.card, fg_color="transparent")
        self.btn_frame.grid(row=6, column=0, padx=40, pady=(0, 30))

        btn_action_text = "Repair Dependencies" if self.repair_mode else "Install Dependencies"
        self.action_btn = ctk.CTkButton(
            self.btn_frame,
            text=btn_action_text,
            width=180,
            height=40,
            fg_color=ACCENT_GREEN,
            hover_color=ACCENT_GREEN_HOVER,
            font=ctk.CTkFont(size=14, weight="bold"),
            command=self.start_installation,
        )
        self.action_btn.grid(row=0, column=0, padx=10)

        self.exit_btn = ctk.CTkButton(
            self.btn_frame,
            text="Exit",
            width=100,
            height=40,
            fg_color="#333333",
            hover_color="#444444",
            command=self.on_exit,
        )
        self.exit_btn.grid(row=0, column=1, padx=10)

    def set_step_status(self, step_key: str, state: str, label_override: Optional[str] = None):
        """Update step icon and color (state: 'pending', 'active', 'done', 'failed')."""
        if step_key not in self.step_labels:
            return
        lbl = self.step_labels[step_key]
        base_name = label_override or next((text for k, text in self.steps if k == step_key), "")
        if state == "done":
            lbl.configure(text=f"✓  {base_name}", text_color=ACCENT_GREEN)
        elif state == "active":
            lbl.configure(text=f"▶  {base_name}", text_color="#FFFFFF")
        elif state == "failed":
            lbl.configure(text=f"✗  {base_name}", text_color=ERROR_RED)
        else:
            lbl.configure(text=f"○  {base_name}", text_color=TEXT_MUTED)

    def start_installation(self):
        self.action_btn.configure(state="disabled")
        self.exit_btn.configure(state="disabled")
        self.log_box.clear()
        self.status_lbl.configure(text="Installing dependencies...", text_color="#FFFFFF")

        threading.Thread(target=self._run_install_worker, daemon=True).start()

    def _run_install_worker(self):
        try:
            # Step 1: Dirs
            self.after(0, self.set_step_status, "dirs", "active")
            self.after(0, self.progress_bar.set, 0.1)
            self.after(0, self.log_box.append, "Preparing local directories...")
            self.dep_manager.install_or_repair_all(
                progress_callback=self._on_download_progress,
                step_callback=self._on_step_change
            )

            # Mark all complete
            for k, _ in self.steps:
                self.after(0, self.set_step_status, k, "done")
            self.after(0, self.progress_bar.set, 1.0)
            self.after(0, self.status_lbl.configure, {"text": "Song Downloader is ready.", "text_color": ACCENT_GREEN})
            self.after(0, self.log_box.append, "All components verified successfully.")

            # Switch action button to Continue
            self.after(0, self._show_continue_button)

        except Exception as e:
            self.after(0, self.status_lbl.configure, {"text": f"Error: {e}", "text_color": ERROR_RED})
            self.after(0, self.log_box.append, f"Installation failed: {e}")
            self.after(0, self.action_btn.configure, {"state": "normal", "text": "Retry Installation"})
            self.after(0, self.exit_btn.configure, {"state": "normal"})

    def _on_step_change(self, step_name: str):
        self.after(0, self.log_box.append, step_name)
        if "directories" in step_name.lower():
            self.after(0, self.set_step_status, "dirs", "done")
            self.after(0, self.set_step_status, "ffmpeg", "active")
        elif "ffmpeg" in step_name.lower():
            self.after(0, self.set_step_status, "ffmpeg", "done")
            self.after(0, self.set_step_status, "deno", "active")
        elif "deno" in step_name.lower():
            self.after(0, self.set_step_status, "deno", "done")
            self.after(0, self.set_step_status, "engine", "active")
        elif "engine" in step_name.lower():
            self.after(0, self.set_step_status, "engine", "done")
            self.after(0, self.set_step_status, "verify", "active")
        elif "ready" in step_name.lower():
            self.after(0, self.set_step_status, "verify", "done")

    def _on_download_progress(self, label: str, fraction: float):
        self.after(0, self.progress_bar.set, fraction)
        self.after(0, self.status_lbl.configure, {"text": f"{label} ({int(fraction * 100)}%)"})

    def _show_continue_button(self):
        self.action_btn.configure(
            state="normal",
            text="Continue to App",
            command=self.on_success
        )
        self.exit_btn.configure(state="normal")
