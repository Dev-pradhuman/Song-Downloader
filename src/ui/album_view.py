"""
Album and playlist track list selection and selective downloader view.
Ensures only user-selected tracks are downloaded without fetching unwanted media.
"""

import threading
from pathlib import Path
from typing import Callable, Dict, List, Optional

import customtkinter as ctk

from ..core.metadata import CollectionInfo, TrackInfo, format_duration
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


class AlbumView(ctk.CTkFrame):
    def __init__(self, master, info: CollectionInfo, on_back: Callable[[], None], **kwargs):
        super().__init__(master, fg_color="transparent", **kwargs)
        self.info = info
        self.on_back = on_back
        self.config_mgr = ConfigManager()
        self.engine = DownloaderEngine()

        self.track_vars: Dict[int, ctk.BooleanVar] = {}
        self.downloaded_path: Optional[Path] = None

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # Card container
        self.card = ctk.CTkFrame(self, fg_color=CARD_BG, corner_radius=12)
        self.card.grid(row=0, column=0, padx=30, pady=15, sticky="nsew")
        self.card.grid_columnconfigure(0, weight=1)
        self.card.grid_rowconfigure(3, weight=1)  # Track list expands

        # Top Navigation
        self.nav_frame = ctk.CTkFrame(self.card, fg_color="transparent")
        self.nav_frame.grid(row=0, column=0, padx=25, pady=(15, 5), sticky="ew")

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

        type_label = self.info.type.capitalize()
        self.header_lbl = ctk.CTkLabel(
            self.nav_frame,
            text=f"{type_label}: {self.info.title}",
            font=ctk.CTkFont(size=16, weight="bold"),
        )
        self.header_lbl.pack(side="left", padx=15)

        self.artist_subtitle = ctk.CTkLabel(
            self.nav_frame,
            text=f"by {self.info.artist}",
            font=ctk.CTkFont(size=13),
            text_color=TEXT_MUTED,
        )
        self.artist_subtitle.pack(side="left")

        # Selection Control Bar
        self.ctrl_frame = ctk.CTkFrame(self.card, fg_color="transparent")
        self.ctrl_frame.grid(row=1, column=0, padx=25, pady=(5, 5), sticky="ew")

        self.select_all_btn = ctk.CTkButton(
            self.ctrl_frame,
            text="Select All",
            width=90,
            height=28,
            fg_color="#333333",
            hover_color="#444444",
            font=ctk.CTkFont(size=12),
            command=self.select_all,
        )
        self.select_all_btn.pack(side="left", padx=(0, 8))

        self.deselect_all_btn = ctk.CTkButton(
            self.ctrl_frame,
            text="Deselect All",
            width=90,
            height=28,
            fg_color="#333333",
            hover_color="#444444",
            font=ctk.CTkFont(size=12),
            command=self.deselect_all,
        )
        self.deselect_all_btn.pack(side="left")

        self.summary_lbl = ctk.CTkLabel(
            self.ctrl_frame,
            text="",
            font=ctk.CTkFont(size=12),
            text_color=TEXT_MUTED,
        )
        self.summary_lbl.pack(side="right")

        # Scrollable Track List
        self.track_list_frame = ctk.CTkScrollableFrame(
            self.card,
            fg_color=INPUT_BG,
            border_color=BORDER_COLOR,
            border_width=1,
            corner_radius=8,
            height=220,
        )
        self.track_list_frame.grid(row=3, column=0, padx=25, pady=5, sticky="nsew")
        self.track_list_frame.grid_columnconfigure(1, weight=1)

        self._build_track_rows()

        # Destination Picker
        default_dir = self.config_mgr.get("download_directory") or str(get_default_download_dir())
        self.dest_picker = DestinationPicker(self.card, default_path=default_dir, on_change=self._on_dest_changed)
        self.dest_picker.grid(row=4, column=0, padx=25, pady=5, sticky="ew")

        # Action & Progress
        self.action_frame = ctk.CTkFrame(self.card, fg_color="transparent")
        self.action_frame.grid(row=5, column=0, padx=25, pady=(5, 10), sticky="ew")
        self.action_frame.grid_columnconfigure(0, weight=1)

        self.download_btn = ctk.CTkButton(
            self.action_frame,
            text="Download Selected",
            height=38,
            fg_color=ACCENT_GREEN,
            hover_color=ACCENT_GREEN_HOVER,
            font=ctk.CTkFont(size=14, weight="bold"),
            command=self.start_download,
        )
        self.download_btn.grid(row=0, column=0, sticky="ew", pady=(0, 5))

        self.progress_bar = ctk.CTkProgressBar(self.action_frame, height=6)
        self.progress_bar.grid(row=1, column=0, sticky="ew", pady=(0, 4))
        self.progress_bar.set(0)

        self.status_lbl = ctk.CTkLabel(
            self.action_frame,
            text="Choose tracks and destination to download",
            font=ctk.CTkFont(size=11),
            text_color=TEXT_MUTED,
        )
        self.status_lbl.grid(row=2, column=0, sticky="ew")

        # Log Box
        self.log_box = LogBox(self.card, height=80)
        self.log_box.grid(row=6, column=0, padx=25, pady=(0, 10), sticky="nsew")

        # Completion Action Frame (hidden initially)
        self.complete_frame = ctk.CTkFrame(self.card, fg_color="transparent")
        self.complete_frame.grid(row=7, column=0, padx=25, pady=(0, 15))
        self.complete_frame.grid_remove()

        self.open_folder_btn = ctk.CTkButton(
            self.complete_frame,
            text="Show in Folder",
            width=130,
            height=32,
            fg_color="#333333",
            hover_color="#444444",
            command=self.open_destination,
        )
        self.open_folder_btn.pack(side="left", padx=8)

        self.download_another_btn = ctk.CTkButton(
            self.complete_frame,
            text="Back to Home",
            width=130,
            height=32,
            fg_color=ACCENT_GREEN,
            hover_color=ACCENT_GREEN_HOVER,
            command=self.on_back,
        )
        self.download_another_btn.pack(side="left", padx=8)

        self._update_selection_summary()

    def _build_track_rows(self):
        for idx, track in enumerate(self.info.tracks):
            var = ctk.BooleanVar(value=True)  # Default all selected
            self.track_vars[idx] = var

            row_frame = ctk.CTkFrame(self.track_list_frame, fg_color="transparent")
            row_frame.grid(row=idx, column=0, columnspan=2, sticky="ew", pady=2, padx=4)
            row_frame.grid_columnconfigure(1, weight=1)

            chk = ctk.CTkCheckBox(
                row_frame,
                text="",
                variable=var,
                width=24,
                checkbox_width=20,
                checkbox_height=20,
                fg_color=ACCENT_GREEN,
                hover_color=ACCENT_GREEN_HOVER,
                command=self._update_selection_summary,
            )
            chk.grid(row=0, column=0, padx=(0, 8))

            num_str = f"{track.track_number:02d}." if track.track_number else f"{idx+1:02d}."
            title_text = f"{num_str} {track.title}"
            title_lbl = ctk.CTkLabel(
                row_frame,
                text=title_text,
                font=ctk.CTkFont(size=12, weight="bold"),
                anchor="w",
            )
            title_lbl.grid(row=0, column=1, sticky="w")

            dur_lbl = ctk.CTkLabel(
                row_frame,
                text=track.duration_str,
                font=ctk.CTkFont(size=11),
                text_color=TEXT_MUTED,
                anchor="e",
            )
            dur_lbl.grid(row=0, column=2, sticky="e", padx=(10, 0))

    def select_all(self):
        for var in self.track_vars.values():
            var.set(True)
        self._update_selection_summary()

    def deselect_all(self):
        for var in self.track_vars.values():
            var.set(False)
        self._update_selection_summary()

    def _update_selection_summary(self):
        selected_indices = [i for i, v in self.track_vars.items() if v.get()]
        sel_count = len(selected_indices)
        total_count = len(self.info.tracks)

        selected_duration = sum(self.info.tracks[i].duration_seconds for i in selected_indices)
        dur_str = format_duration(selected_duration)

        self.summary_lbl.configure(text=f"{sel_count} of {total_count} selected • {dur_str}")
        self.download_btn.configure(
            text=f"Download Selected ({sel_count})",
            state="normal" if sel_count > 0 else "disabled",
        )

    def _on_dest_changed(self, new_path: str):
        self.config_mgr.set("download_directory", new_path)

    def start_download(self):
        selected_tracks = [self.info.tracks[i] for i, v in self.track_vars.items() if v.get()]
        if not selected_tracks:
            return

        dest_dir = Path(self.dest_picker.get_path())
        self.config_mgr.set("download_directory", str(dest_dir))

        self.download_btn.configure(state="disabled")
        self.select_all_btn.configure(state="disabled")
        self.deselect_all_btn.configure(state="disabled")
        self.back_btn.configure(state="disabled")

        self.status_lbl.configure(
            text=f"Downloading {len(selected_tracks)} selected track(s)...",
            text_color="#FFFFFF"
        )
        self.progress_bar.set(0.05)
        self.log_box.clear()

        threading.Thread(target=self._run_download_worker, args=(selected_tracks, dest_dir), daemon=True).start()

    def _run_download_worker(self, tracks: List[TrackInfo], dest_dir: Path):
        track_urls = [t.url for t in tracks if t.url]
        self.downloaded_path = dest_dir

        success = self.engine.download_tracks(
            track_urls=track_urls,
            output_dir=dest_dir,
            threads=self.config_mgr.get("threads", 4),
            log_callback=lambda msg: self.after(0, self.log_box.append, msg),
            progress_callback=lambda curr, total, msg: self.after(0, self._on_progress, curr, total, msg),
        )

        if success:
            self.after(0, self.progress_bar.set, 1.0)
            self.after(0, self.status_lbl.configure, {
                "text": f"Successfully downloaded {len(tracks)} tracks!",
                "text_color": ACCENT_GREEN
            })
            self.after(0, self.complete_frame.grid)
            self.after(0, self.download_btn.configure, {"text": "Download Completed", "state": "disabled"})
        else:
            self.after(0, self.status_lbl.configure, {
                "text": "Finished with errors or partial downloads.",
                "text_color": ERROR_RED
            })
            self.after(0, self.download_btn.configure, {"state": "normal", "text": "Retry Download"})

        self.after(0, self.back_btn.configure, {"state": "normal"})
        self.after(0, self.select_all_btn.configure, {"state": "normal"})
        self.after(0, self.deselect_all_btn.configure, {"state": "normal"})

    def _on_progress(self, curr: int, total: int, msg: str):
        self.progress_bar.set(1.0 if total == 0 else curr / total)
        self.status_lbl.configure(text=f"Downloading track {curr} of {total}...")

    def open_destination(self):
        if self.downloaded_path:
            open_in_explorer(self.downloaded_path)
