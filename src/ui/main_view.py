"""
Main URL input and navigation view for Song Downloader.
"""

import threading
from pathlib import Path
from typing import Callable, Optional

import customtkinter as ctk

from ..core.metadata import fetch_metadata, CollectionInfo
from ..core.paths import get_default_download_dir
from ..core.config_manager import ConfigManager
from .components import (
    ACCENT_GREEN,
    ACCENT_GREEN_HOVER,
    CARD_BG,
    INPUT_BG,
    BORDER_COLOR,
    ERROR_RED,
    TEXT_MUTED,
    open_in_explorer
)


class MainView(ctk.CTkFrame):
    def __init__(
        self,
        master,
        on_track_loaded: Callable[[CollectionInfo], None],
        on_album_loaded: Callable[[CollectionInfo], None],
        on_repair_requested: Callable[[], None],
        **kwargs
    ):
        super().__init__(master, fg_color="transparent", **kwargs)
        self.on_track_loaded = on_track_loaded
        self.on_album_loaded = on_album_loaded
        self.on_repair_requested = on_repair_requested
        self.config_mgr = ConfigManager()

        self.grid_columnconfigure(0, weight=1)

        # Card container
        self.card = ctk.CTkFrame(self, fg_color=CARD_BG, corner_radius=12)
        self.card.grid(row=0, column=0, padx=40, pady=30, sticky="nsew")
        self.card.grid_columnconfigure(0, weight=1)

        # Title
        self.title_lbl = ctk.CTkLabel(
            self.card,
            text="Song Downloader",
            font=ctk.CTkFont(size=28, weight="bold"),
        )
        self.title_lbl.grid(row=0, column=0, padx=20, pady=(35, 6))

        self.subtitle_lbl = ctk.CTkLabel(
            self.card,
            text="Download Spotify songs, albums, and playlists with local dependency isolation",
            font=ctk.CTkFont(size=13),
            text_color=TEXT_MUTED,
        )
        self.subtitle_lbl.grid(row=1, column=0, padx=20, pady=(0, 25))

        # URL Input Section
        self.input_frame = ctk.CTkFrame(self.card, fg_color="transparent")
        self.input_frame.grid(row=2, column=0, padx=40, pady=10, sticky="ew")
        self.input_frame.grid_columnconfigure(0, weight=1)

        self.url_label = ctk.CTkLabel(
            self.input_frame,
            text="Paste song / album / playlist URL:",
            font=ctk.CTkFont(size=14, weight="bold"),
            anchor="w",
        )
        self.url_label.grid(row=0, column=0, sticky="w", pady=(0, 8))

        self.url_entry = ctk.CTkEntry(
            self.input_frame,
            placeholder_text="https://open.spotify.com/track/... or .../album/...",
            height=44,
            fg_color=INPUT_BG,
            border_color=BORDER_COLOR,
            font=ctk.CTkFont(size=13),
        )
        self.url_entry.grid(row=1, column=0, sticky="ew", pady=(0, 15))
        self.url_entry.bind("<Return>", lambda e: self.on_continue())

        # Continue Button
        self.continue_btn = ctk.CTkButton(
            self.input_frame,
            text="Continue",
            height=42,
            fg_color=ACCENT_GREEN,
            hover_color=ACCENT_GREEN_HOVER,
            font=ctk.CTkFont(size=15, weight="bold"),
            command=self.on_continue,
        )
        self.continue_btn.grid(row=2, column=0, sticky="ew")

        # Status Label
        self.status_lbl = ctk.CTkLabel(
            self.card,
            text="",
            font=ctk.CTkFont(size=12),
            text_color=TEXT_MUTED,
        )
        self.status_lbl.grid(row=3, column=0, padx=20, pady=(15, 20))

        # Footer Actions
        self.footer_frame = ctk.CTkFrame(self.card, fg_color="transparent")
        self.footer_frame.grid(row=4, column=0, padx=40, pady=(10, 25))

        self.repair_btn = ctk.CTkButton(
            self.footer_frame,
            text="Repair Dependencies",
            fg_color="transparent",
            text_color=TEXT_MUTED,
            hover_color="#2A2A2A",
            font=ctk.CTkFont(size=12),
            command=self.on_repair_requested,
        )
        self.repair_btn.grid(row=0, column=0, padx=8)

        self.open_downloads_btn = ctk.CTkButton(
            self.footer_frame,
            text="Open Downloads",
            fg_color="transparent",
            text_color=TEXT_MUTED,
            hover_color="#2A2A2A",
            font=ctk.CTkFont(size=12),
            command=self.open_downloads_folder,
        )
        self.open_downloads_btn.grid(row=0, column=1, padx=8)

        self.about_btn = ctk.CTkButton(
            self.footer_frame,
            text="About",
            fg_color="transparent",
            text_color=TEXT_MUTED,
            hover_color="#2A2A2A",
            font=ctk.CTkFont(size=12),
            command=self.show_about,
        )
        self.about_btn.grid(row=0, column=2, padx=8)

    def on_continue(self):
        url = self.url_entry.get().strip()
        if not url:
            self.status_lbl.configure(text="Please paste a Spotify URL.", text_color=ERROR_RED)
            return

        if "spotify.com" not in url:
            self.status_lbl.configure(text="Invalid URL: Please enter a valid Spotify link.", text_color=ERROR_RED)
            return

        self.continue_btn.configure(state="disabled")
        self.status_lbl.configure(text="Analyzing URL and retrieving metadata...", text_color="#FFFFFF")

        threading.Thread(target=self._analyze_worker, args=(url,), daemon=True).start()

    def _analyze_worker(self, url: str):
        try:
            info = fetch_metadata(url)
            if info.type == "track":
                self.after(0, self.on_track_loaded, info)
            else:
                self.after(0, self.on_album_loaded, info)
        except Exception as e:
            self.after(0, self._on_analyze_error, str(e))
        finally:
            self.after(0, lambda: self.continue_btn.configure(state="normal"))

    def _on_analyze_error(self, err_msg: str):
        self.status_lbl.configure(text=f"Error: {err_msg}", text_color=ERROR_RED)

    def open_downloads_folder(self):
        target = self.config_mgr.get("download_directory") or str(get_default_download_dir())
        open_in_explorer(Path(target))

    def show_about(self):
        self.status_lbl.configure(
            text="Song Downloader v1.0.0 — Clean, portable, self-contained media downloader.",
            text_color=TEXT_MUTED,
        )
