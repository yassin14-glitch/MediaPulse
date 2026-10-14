"""Modern Sidebar Navigation Desktop Application built with CustomTkinter."""
import json
import os
import sys
import tkinter as tk
from tkinter import messagebox
from typing import Dict, Optional

import customtkinter as ctk
from PIL import Image

from core.ffmpeg_manager import FFmpegManager
from core.history_manager import HistoryManager
from ui.history_tab import HistoryTab
from ui.settings_tab import SettingsTab
from ui.web_tab import WebVideoTab
from ui.youtube_tab import YouTubeTab


class ModernMainWindow(ctk.CTk):
    """Next-Gen Desktop Application with modern left sidebar navigation and cards."""

    CONFIG_FILE = os.path.join(os.path.expanduser("~"), ".multimedia_downloader", "config.json")

    # Sleek Modern Dark Theme Palette
    COLOR_BG_DARK = "#090d16"         # Deep Obsidian Background
    COLOR_SIDEBAR = "#0f172a"         # Rich Slate Sidebar
    COLOR_CARD = "#1e293b"            # Elevated Surface
    COLOR_CARD_HOVER = "#334155"      # Interactive Surface
    COLOR_ACCENT = "#3b82f6"          # Electric Blue
    COLOR_ACCENT_HOVER = "#2563eb"
    COLOR_SUCCESS = "#10b981"         # Emerald Green
    COLOR_SUCCESS_HOVER = "#059669"
    COLOR_DANGER = "#ef4444"          # Crimson Red
    COLOR_TEXT_PRIMARY = "#f8fafc"
    COLOR_TEXT_MUTED = "#94a3b8"

    def __init__(self):
        super().__init__()

        # Appearance configuration
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")

        # Window properties
        self.title("Universal Video Downloader Pro • YouTube & Any Website")
        self.geometry("1060x760")
        self.minsize(920, 640)
        self.configure(fg_color=self.COLOR_BG_DARK)

        # Config & storage setup
        self.config = self._load_config()
        self.default_download_dir = self.config.get(
            "download_dir",
            os.path.join(os.path.expanduser("~"), "Downloads", "VideoDownloads")
        )
        os.makedirs(self.default_download_dir, exist_ok=True)
        self.history_mgr = HistoryManager()

        self.nav_buttons: Dict[str, ctk.CTkButton] = {}
        self.views: Dict[str, ctk.CTkFrame] = {}
        self.current_view_key = "youtube"

        # Set application icon
        icon_candidates = []
        if getattr(sys, "frozen", False):
            meipass = getattr(sys, "_MEIPASS", "")
            if meipass:
                icon_candidates.append(os.path.join(meipass, "assets", "icon.ico"))
            exe_dir = os.path.dirname(sys.executable)
            icon_candidates.append(os.path.join(exe_dir, "_internal", "assets", "icon.ico"))
            icon_candidates.append(os.path.join(exe_dir, "assets", "icon.ico"))
        icon_candidates.append(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "assets", "icon.ico"))
        for ic in icon_candidates:
            if os.path.exists(ic):
                try:
                    self.iconbitmap(ic)
                    break
                except Exception:
                    pass


        self._build_layout()
        self.switch_view("youtube")
        self.protocol("WM_DELETE_WINDOW", self._on_window_close)

    def _on_window_close(self):
        try:
            if hasattr(self, "views"):
                for v in self.views.values():
                    if hasattr(v, "downloader") and v.downloader:
                        v.downloader.cancel()
        except Exception:
            pass
        self.destroy()

    def _load_config(self) -> dict:
        try:
            if os.path.exists(self.CONFIG_FILE):
                with open(self.CONFIG_FILE, "r", encoding="utf-8") as f:
                    return json.load(f)
        except Exception:
            pass
        return {}

    def _save_config(self):
        try:
            os.makedirs(os.path.dirname(self.CONFIG_FILE), exist_ok=True)
            with open(self.CONFIG_FILE, "w", encoding="utf-8") as f:
                json.dump(self.config, f, indent=2)
        except Exception as e:
            print(f"Error saving config: {e}")

    def _build_layout(self):
        # Master grid layout: column 0 = Sidebar, column 1 = Content
        self.grid_columnconfigure(0, weight=0)
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # 1. Left Sidebar
        self.sidebar_frame = ctk.CTkFrame(
            self,
            width=230,
            corner_radius=0,
            fg_color=self.COLOR_SIDEBAR
        )
        self.sidebar_frame.grid(row=0, column=0, sticky="nsew")
        self.sidebar_frame.grid_propagate(False)

        self._build_sidebar()

        # 2. Right Content View Container
        self.content_container = ctk.CTkFrame(
            self,
            corner_radius=0,
            fg_color="transparent"
        )
        self.content_container.grid(row=0, column=1, sticky="nsew", padx=10, pady=10)
        self.content_container.grid_rowconfigure(0, weight=1)
        self.content_container.grid_columnconfigure(0, weight=1)

        # Instantiate View Frames
        self.views["youtube"] = YouTubeTab(
            self.content_container,
            history_mgr=self.history_mgr,
            default_download_dir=self.default_download_dir
        )
        self.views["web"] = WebVideoTab(
            self.content_container,
            history_mgr=self.history_mgr,
            default_download_dir=self.default_download_dir
        )
        self.views["history"] = HistoryTab(
            self.content_container,
            history_mgr=self.history_mgr,
            default_download_dir=self.default_download_dir
        )
        self.views["settings"] = SettingsTab(
            self.content_container,
            current_download_dir=self.default_download_dir,
            on_dir_change=self._on_download_dir_change
        )

        for view in self.views.values():
            view.grid(row=0, column=0, sticky="nsew")

    def _build_sidebar(self):
        # App Branding Logo
        logo_frame = ctk.CTkFrame(self.sidebar_frame, fg_color="transparent")
        logo_frame.pack(fill="x", padx=16, pady=(20, 24))

        ctk.CTkLabel(
            logo_frame,
            text="⚡ MediaPulse",
            font=ctk.CTkFont(size=20, weight="bold"),
            text_color="#60a5fa",
            anchor="w"
        ).pack(anchor="w")

        ctk.CTkLabel(
            logo_frame,
            text="Universal Video Downloader",
            font=ctk.CTkFont(size=11),
            text_color=self.COLOR_TEXT_MUTED,
            anchor="w"
        ).pack(anchor="w", pady=(2, 0))

        # Nav Section Label
        ctk.CTkLabel(
            self.sidebar_frame,
            text="MENU",
            font=ctk.CTkFont(size=10, weight="bold"),
            text_color="gray50",
            anchor="w"
        ).pack(anchor="w", padx=20, pady=(0, 8))

        # Navigation Buttons
        nav_items = [
            ("youtube", "📺  YouTube Downloader"),
            ("web", "🌐  Any Website Video"),
            ("history", "📁  Download History"),
            ("settings", "⚙️  Settings & FFmpeg"),
        ]

        for key, label in nav_items:
            btn = ctk.CTkButton(
                self.sidebar_frame,
                text=label,
                height=42,
                corner_radius=8,
                anchor="w",
                font=ctk.CTkFont(size=13, weight="bold"),
                fg_color="transparent",
                text_color=self.COLOR_TEXT_MUTED,
                hover_color=self.COLOR_CARD_HOVER,
                command=lambda k=key: self.switch_view(k)
            )
            btn.pack(fill="x", padx=12, pady=4)
            self.nav_buttons[key] = btn

        # Spacer to push bottom status box down
        spacer = ctk.CTkFrame(self.sidebar_frame, fg_color="transparent")
        spacer.pack(fill="both", expand=True)

        # Bottom FFmpeg & Storage Info Badge
        avail, ver_str, _ = FFmpegManager.get_status()
        status_box = ctk.CTkFrame(
            self.sidebar_frame,
            corner_radius=10,
            fg_color="#0b1120",
            border_width=1,
            border_color="#1e293b"
        )
        status_box.pack(fill="x", padx=12, pady=16)

        ff_badge = ctk.CTkFrame(status_box, fg_color="transparent")
        ff_badge.pack(fill="x", padx=10, pady=(10, 4))

        status_dot = "🟢" if avail else "🔴"
        ctk.CTkLabel(
            ff_badge,
            text=f"{status_dot} FFmpeg 7.1",
            font=ctk.CTkFont(size=11, weight="bold"),
            text_color="#34d399" if avail else "#f87171"
        ).pack(side="left")

        ctk.CTkLabel(
            ff_badge,
            text="Active" if avail else "Missing",
            font=ctk.CTkFont(size=10),
            text_color="gray"
        ).pack(side="right")

        btn_quick_folder = ctk.CTkButton(
            status_box,
            text="📂 Open Downloads",
            height=28,
            corner_radius=6,
            font=ctk.CTkFont(size=11),
            fg_color="#1e293b",
            hover_color="#334155",
            command=lambda: HistoryManager.open_folder(self.default_download_dir)
        )
        btn_quick_folder.pack(fill="x", padx=10, pady=(4, 10))

    def switch_view(self, key: str):
        self.current_view_key = key

        # Update button highlights
        for k, btn in self.nav_buttons.items():
            if k == key:
                btn.configure(
                    fg_color=self.COLOR_ACCENT,
                    text_color="#ffffff",
                    hover_color=self.COLOR_ACCENT_HOVER
                )
            else:
                btn.configure(
                    fg_color="transparent",
                    text_color=self.COLOR_TEXT_MUTED,
                    hover_color=self.COLOR_CARD_HOVER
                )

        # Lift selected view to top
        if key in self.views:
            view = self.views[key]
            view.tkraise()
            if key == "history":
                self.views["history"].refresh_list()

    def _on_download_dir_change(self, new_dir: str):
        self.default_download_dir = new_dir
        self.config["download_dir"] = new_dir
        self._save_config()

        # Synchronize directory across all tabs
        self.views["youtube"].download_dir = new_dir
        self.views["youtube"].lbl_dest_path.configure(text=new_dir)
        self.views["web"].download_dir = new_dir
        self.views["history"].download_dir = new_dir


MainWindow = ModernMainWindow
