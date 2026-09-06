"""
Single song metadata display and download view.
"""

import threading
from pathlib import Path
from typing import Callable, Optional

import customtkinter as ctk

from ..core.metadata import CollectionInfo
from ..core.downloader_engine import DownloaderEngine
from ..core.config_manager import ConfigManager
from ..core.paths import get_default_download_dir
from .components import (
    ACCENT_GREEN,
    ACCENT_GREEN_HOVER,
    CARD_BG,
    INPUT_BG,
    BORDER_COLOR,
    ERROR_RED,
    TEXT_MUTED,
    DestinationPicker,
    LogBox,
    open_in_explorer
)


class SongView(ctk.CTkFrame):
    def __init__(self, master, info: CollectionInfo, on_back: Callable[[], None], **kwargs):
        super().__init__(master, fg_color="transparent", **kwargs)
        self.info = info
        self.on_back = on_back
        self.config_mgr = ConfigManager()
        self.engine = DownloaderEngine()

        self.track = info.tracks[0] if info.tracks else None
        self.downloaded_path: Optional[Path] = None

        self.grid_columnconfigure(0, weight=1)

        # Card container
        self.card = ctk.CTkFrame(self, fg_color=CARD_BG, corner_radius=12)
        self.card.grid(row=0, column=0, padx=40, pady=20, sticky="nsew")
        self.card.grid_columnconfigure(0, weight=1)

        # Top Navigation
        self.nav_frame = ctk.CTkFrame(self.card, fg_color="transparent")
        self.nav_frame.grid(row=0, column=0, padx=25, pady=(20, 10), sticky="ew")

        self.back_btn = ctk.CTkButton(
            self.nav_frame,
            text="← Back",
            width=70,
            height=30,
            fg_color="#333333",
            hover_color="#444444",
            command=self.on_back,
        )
        self.back_btn.pack(side="left")

        self.view_title = ctk.CTkLabel(
            self.nav_frame,
            text="Song Details",
            font=ctk.CTkFont(size=16, weight="bold"),
        )
        self.view_title.pack(side="left", padx=15)

        # Song Metadata Card
        self.meta_frame = ctk.CTkFrame(self.card, fg_color=INPUT_BG, corner_radius=8)
        self.meta_frame.grid(row=1, column=0, padx=25, pady=10, sticky="ew")
        self.meta_frame.grid_columnconfigure(1, weight=1)

        track_title = self.track.title if self.track else "Unknown Track"
        track_artist = self.track.artist if self.track else "Unknown Artist"
        track_album = self.track.album if self.track else "Unknown Album"
        track_duration = self.track.duration_str if self.track else "0:00"

        # Track Icon / Placeholder
        self.icon_lbl = ctk.CTkLabel(
            self.meta_frame,
            text="🎵",
            font=ctk.CTkFont(size=36),
            width=60,
        )
        self.icon_lbl.grid(row=0, column=0, rowspan=3, padx=(15, 10), pady=15)

        self.title_lbl = ctk.CTkLabel(
            self.meta_frame,
            text=track_title,
            font=ctk.CTkFont(size=18, weight="bold"),
            anchor="w",
        )
        self.title_lbl.grid(row=0, column=1, sticky="w", padx=5, pady=(12, 2))

        self.artist_lbl = ctk.CTkLabel(
            self.meta_frame,
            text=f"{track_artist} • {track_album}",
            font=ctk.CTkFont(size=13),
            text_color=TEXT_MUTED,
            anchor="w",
        )
        self.artist_lbl.grid(row=1, column=1, sticky="w", padx=5, pady=0)

        self.duration_lbl = ctk.CTkLabel(
            self.meta_frame,
            text=f"Duration: {track_duration}",
            font=ctk.CTkFont(size=12),
            text_color=TEXT_MUTED,
            anchor="w",
        )
        self.duration_lbl.grid(row=2, column=1, sticky="w", padx=5, pady=(2, 12))

        # Destination Picker
        default_dir = self.config_mgr.get("download_directory") or str(get_default_download_dir())
        self.dest_picker = DestinationPicker(self.card, default_path=default_dir, on_change=self._on_dest_changed)
        self.dest_picker.grid(row=2, column=0, padx=25, pady=10, sticky="ew")

        # Action Button
        self.download_btn = ctk.CTkButton(
            self.card,
            text="Download Song",
            height=40,
            fg_color=ACCENT_GREEN,
            hover_color=ACCENT_GREEN_HOVER,
            font=ctk.CTkFont(size=14, weight="bold"),
            command=self.start_download,
        )
        self.download_btn.grid(row=3, column=0, padx=25, pady=15, sticky="ew")

        # Progress bar & Status
        self.progress_bar = ctk.CTkProgressBar(self.card, height=8)
        self.progress_bar.grid(row=4, column=0, padx=25, pady=(5, 5), sticky="ew")
        self.progress_bar.set(0)

        self.status_lbl = ctk.CTkLabel(
            self.card,
            text="Ready to download",
            font=ctk.CTkFont(size=12),
            text_color=TEXT_MUTED,
        )
        self.status_lbl.grid(row=5, column=0, padx=25, pady=(0, 10))

        # Log box
        self.log_box = LogBox(self.card, height=90)
        self.log_box.grid(row=6, column=0, padx=25, pady=(0, 15), sticky="nsew")

        # Completion Action Frame (hidden initially)
        self.complete_frame = ctk.CTkFrame(self.card, fg_color="transparent")
        self.complete_frame.grid(row=7, column=0, padx=25, pady=(0, 20))
        self.complete_frame.grid_remove()

        self.open_folder_btn = ctk.CTkButton(
            self.complete_frame,
            text="Show in Folder",
            width=140,
            height=36,
            fg_color="#333333",
            hover_color="#444444",
            command=self.open_destination,
        )
        self.open_folder_btn.pack(side="left", padx=10)

        self.download_another_btn = ctk.CTkButton(
            self.complete_frame,
            text="Download Another",
            width=140,
            height=36,
            fg_color=ACCENT_GREEN,
            hover_color=ACCENT_GREEN_HOVER,
            command=self.on_back,
        )
        self.download_another_btn.pack(side="left", padx=10)

    def _on_dest_changed(self, new_path: str):
        self.config_mgr.set("download_directory", new_path)

    def start_download(self):
        if not self.track:
            return

        dest_dir = Path(self.dest_picker.get_path())
        self.config_mgr.set("download_directory", str(dest_dir))

        self.download_btn.configure(state="disabled")
        self.back_btn.configure(state="disabled")
        self.progress_bar.set(0.1)
        self.status_lbl.configure(text="Downloading song audio and metadata...", text_color="#FFFFFF")
        self.log_box.clear()

        threading.Thread(target=self._run_download_worker, args=(dest_dir,), daemon=True).start()

    def _run_download_worker(self, dest_dir: Path):
        success = self.engine.download_tracks(
            track_urls=[self.track.url],
            output_dir=dest_dir,
            threads=self.config_mgr.get("threads", 4),
            log_callback=lambda msg: self.after(0, self.log_box.append, msg),
            progress_callback=lambda curr, total, msg: self.after(0, self._on_progress, curr, total, msg),
        )

        self.downloaded_path = dest_dir

        if success:
            self.after(0, self.progress_bar.set, 1.0)
            self.after(0, self.status_lbl.configure, {"text": "Download complete!", "text_color": ACCENT_GREEN})
            self.after(0, self.complete_frame.grid)
            self.after(0, self.download_btn.configure, {"text": "Downloaded", "state": "disabled"})
        else:
            self.after(0, self.status_lbl.configure, {"text": "Download failed or finished with errors.", "text_color": ERROR_RED})
            self.after(0, self.download_btn.configure, {"state": "normal", "text": "Retry Download"})

        self.after(0, self.back_btn.configure, {"state": "normal"})

    def _on_progress(self, curr: int, total: int, msg: str):
        self.progress_bar.set(1.0 if total == 0 else curr / total)

    def open_destination(self):
        if self.downloaded_path:
            open_in_explorer(self.downloaded_path)
