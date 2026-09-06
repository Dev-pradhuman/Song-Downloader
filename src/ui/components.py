"""
Reusable UI styling and widgets for Song Downloader.
"""

import os
import subprocess
import sys
import tkinter.filedialog as fd
from pathlib import Path
from typing import Callable, Optional

import customtkinter as ctk

# Color Palette
ACCENT_GREEN = "#1DB954"       # Spotify Green
ACCENT_GREEN_HOVER = "#1AA34A"
DARK_BG = "#121212"
CARD_BG = "#1E1E1E"
INPUT_BG = "#2A2A2A"
BORDER_COLOR = "#333333"
TEXT_MUTED = "#A0A0A0"
ERROR_RED = "#E74C3C"
WARNING_ORANGE = "#F39C12"


def open_in_explorer(path: Path) -> None:
    """Open a file or directory in the system file explorer."""
    path = Path(path).resolve()
    if sys.platform == "win32":
        if path.is_file():
            subprocess.run(["explorer", f"/select,{str(path)}"], check=False)
        else:
            subprocess.run(["explorer", str(path)], check=False)
    elif sys.platform == "darwin":
        subprocess.run(["open", str(path)], check=False)
    else:
        subprocess.run(["xdg-open", str(path)], check=False)


class DestinationPicker(ctk.CTkFrame):
    """Destination folder selection widget with path entry and browse button."""
    def __init__(self, master, default_path: str, on_change: Optional[Callable[[str], None]] = None, **kwargs):
        super().__init__(master, fg_color="transparent", **kwargs)
        self.on_change = on_change

        self.path_var = ctk.StringVar(value=default_path)

        self.grid_columnconfigure(0, weight=1)

        self.label = ctk.CTkLabel(self, text="Save to folder:", font=ctk.CTkFont(size=12, weight="bold"), text_color=TEXT_MUTED)
        self.label.grid(row=0, column=0, columnspan=2, sticky="w", pady=(0, 4))

        self.entry = ctk.CTkEntry(self, textvariable=self.path_var, height=36, fg_color=INPUT_BG, border_color=BORDER_COLOR)
        self.entry.grid(row=1, column=0, sticky="ew", padx=(0, 8))

        self.browse_btn = ctk.CTkButton(
            self,
            text="Browse",
            width=90,
            height=36,
            fg_color="#333333",
            hover_color="#444444",
            command=self._browse
        )
        self.browse_btn.grid(row=1, column=1, sticky="e")

    def _browse(self):
        chosen = fd.askdirectory(initialdir=self.path_var.get())
        if chosen:
            self.path_var.set(chosen)
            if self.on_change:
                self.on_change(chosen)

    def get_path(self) -> str:
        return self.path_var.get().strip()


class LogBox(ctk.CTkFrame):
    """Collapsible or dedicated log viewer box."""
    def __init__(self, master, height: int = 140, **kwargs):
        super().__init__(master, fg_color="transparent", **kwargs)
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)

        self.textbox = ctk.CTkTextbox(
            self,
            height=height,
            fg_color=INPUT_BG,
            text_color="#DDDDDD",
            font=ctk.CTkFont(family="Consolas", size=11),
            border_color=BORDER_COLOR,
            border_width=1,
            wrap="word",
        )
        self.textbox.grid(row=0, column=0, sticky="nsew")
        self.textbox.configure(state="disabled")

    def append(self, text: str):
        self.textbox.configure(state="normal")
        self.textbox.insert("end", text + "\n")
        self.textbox.see("end")
        self.textbox.configure(state="disabled")

    def clear(self):
        self.textbox.configure(state="normal")
        self.textbox.delete("1.0", "end")
        self.textbox.configure(state="disabled")
