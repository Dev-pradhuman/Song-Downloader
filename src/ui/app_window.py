"""
Main application window and view controller for Song Downloader.
"""

import sys
from typing import Optional

import customtkinter as ctk

from ..core.dependency_manager import DependencyManager
from ..core.metadata import CollectionInfo
from .components import DARK_BG
from .installer_view import InstallerView
from .main_view import MainView
from .song_view import SongView
from .album_view import AlbumView


class AppWindow(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("Song Downloader")
        self.geometry("780x660")
        self.minsize(680, 560)
        ctk.set_appearance_mode("Dark")
        ctk.set_default_color_theme("green")

        self.configure(fg_color=DARK_BG)
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)

        self.dep_manager = DependencyManager()
        self.current_view: Optional[ctk.CTkFrame] = None

        # Route to initial view based on dependency health
        self._route_initial_view()

    def _route_initial_view(self):
        if self.dep_manager.is_fully_installed():
            self.show_main_view()
        else:
            self.show_installer_view(repair_mode=False)

    def switch_view(self, new_view: ctk.CTkFrame):
        """Cleanly transition to a new view."""
        if self.current_view:
            self.current_view.destroy()
        self.current_view = new_view
        self.current_view.grid(row=0, column=0, sticky="nsew")

    def show_main_view(self):
        view = MainView(
            self,
            on_track_loaded=self.show_song_view,
            on_album_loaded=self.show_album_view,
            on_repair_requested=lambda: self.show_installer_view(repair_mode=True),
        )
        self.switch_view(view)

    def show_installer_view(self, repair_mode: bool = False):
        view = InstallerView(
            self,
            on_success=self.show_main_view,
            on_exit=self.destroy,
            repair_mode=repair_mode,
        )
        self.switch_view(view)

    def show_song_view(self, info: CollectionInfo):
        view = SongView(
            self,
            info=info,
            on_back=self.show_main_view,
        )
        self.switch_view(view)

    def show_album_view(self, info: CollectionInfo):
        view = AlbumView(
            self,
            info=info,
            on_back=self.show_main_view,
        )
        self.switch_view(view)
