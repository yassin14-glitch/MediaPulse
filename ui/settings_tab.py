import json
import os
import tkinter as tk
from tkinter import filedialog, messagebox
from typing import Callable

import customtkinter as ctk
from core.downloader_engine import CONFIG_PATH, DownloaderEngine, get_browser_cookies_setting, get_installed_browsers
from core.ffmpeg_manager import FFmpegManager
from core.history_manager import HistoryManager



class SettingsTab(ctk.CTkFrame):
    """Tab for managing application settings, themes, and FFmpeg diagnostics."""

    def __init__(self, master, current_download_dir: str, on_dir_change: Callable[[str], None]):
        super().__init__(master, fg_color="transparent")
        self.download_dir = current_download_dir
        self.on_dir_change = on_dir_change

        self._build_ui()

    def _build_ui(self):
        scroll = ctk.CTkScrollableFrame(self, corner_radius=10)
        scroll.pack(fill="both", expand=True, padx=10, pady=10)

        # 1. Title
        title_box = ctk.CTkFrame(scroll, corner_radius=8)
        title_box.pack(fill="x", padx=10, pady=(0, 10))

        ctk.CTkLabel(
            title_box,
            text="⚙️ Application Settings & Diagnostics",
            font=ctk.CTkFont(size=18, weight="bold")
        ).pack(anchor="w", padx=15, pady=12)

        # 2. General Settings Card
        gen_card = ctk.CTkFrame(scroll, corner_radius=8)
        gen_card.pack(fill="x", padx=10, pady=8)

        ctk.CTkLabel(
            gen_card,
            text="General Settings",
            font=ctk.CTkFont(size=14, weight="bold")
        ).pack(anchor="w", padx=15, pady=(12, 8))

        # Default Folder
        dir_row = ctk.CTkFrame(gen_card, fg_color="transparent")
        dir_row.pack(fill="x", padx=15, pady=(0, 15))

        ctk.CTkLabel(
            dir_row,
            text="Default Download Directory:",
            font=ctk.CTkFont(size=12, weight="bold")
        ).pack(anchor="w", pady=(0, 4))

        input_box = ctk.CTkFrame(dir_row, fg_color="transparent")
        input_box.pack(fill="x")

        self.lbl_path = ctk.CTkLabel(
            input_box,
            text=self.download_dir,
            font=ctk.CTkFont(size=12),
            anchor="w",
            text_color="#3B8ED0"
        )
        self.lbl_path.pack(side="left", fill="x", expand=True, padx=(0, 10))

        ctk.CTkButton(
            input_box,
            text="Change Folder",
            width=120,
            command=self.change_folder
        ).pack(side="right")

        # 3. Appearance Card
        app_card = ctk.CTkFrame(scroll, corner_radius=8)
        app_card.pack(fill="x", padx=10, pady=8)

        ctk.CTkLabel(
            app_card,
            text="Appearance & Theme",
            font=ctk.CTkFont(size=14, weight="bold")
        ).pack(anchor="w", padx=15, pady=(12, 8))

        theme_row = ctk.CTkFrame(app_card, fg_color="transparent")
        theme_row.pack(fill="x", padx=15, pady=(0, 15))

        # Mode
        mode_box = ctk.CTkFrame(theme_row, fg_color="transparent")
        mode_box.pack(side="left", padx=(0, 30))

        ctk.CTkLabel(mode_box, text="Appearance Mode:", font=ctk.CTkFont(size=12, weight="bold")).pack(anchor="w", pady=(0, 4))
        self.mode_menu = ctk.CTkOptionMenu(
            mode_box,
            values=["Dark", "Light", "System"],
            command=self.change_appearance_mode
        )
        self.mode_menu.set("Dark")
        self.mode_menu.pack()

        # Color theme
        color_box = ctk.CTkFrame(theme_row, fg_color="transparent")
        color_box.pack(side="left")

        ctk.CTkLabel(color_box, text="Accent Color:", font=ctk.CTkFont(size=12, weight="bold")).pack(anchor="w", pady=(0, 4))
        self.color_menu = ctk.CTkOptionMenu(
            color_box,
            values=["blue", "green", "dark-blue"],
            command=self.change_color_theme
        )
        self.color_menu.set("blue")
        self.color_menu.pack()

        # 4. Browser Cookies Card
        cookie_card = ctk.CTkFrame(scroll, corner_radius=8)
        cookie_card.pack(fill="x", padx=10, pady=8)

        ctk.CTkLabel(
            cookie_card,
            text="🍪 Browser Cookies & Authentication (Instagram / Facebook / Restricted Sites)",
            font=ctk.CTkFont(size=14, weight="bold")
        ).pack(anchor="w", padx=15, pady=(12, 4))

        ctk.CTkLabel(
            cookie_card,
            text="Extract cookies from your installed browser to download Instagram Reels, private, or login-only videos.",
            font=ctk.CTkFont(size=11),
            text_color="gray"
        ).pack(anchor="w", padx=15, pady=(0, 8))

        cookie_row = ctk.CTkFrame(cookie_card, fg_color="transparent")
        cookie_row.pack(fill="x", padx=15, pady=(0, 15))

        installed = get_installed_browsers()
        options = ["Auto-Detect (Recommended)"] + [b.capitalize() for b in installed] + ["None (No Cookies)"]

        self.cookie_menu = ctk.CTkOptionMenu(
            cookie_row,
            values=options,
            command=self.change_browser_cookies
        )
        current = get_browser_cookies_setting()
        if current == "auto":
            self.cookie_menu.set("Auto-Detect (Recommended)")
        elif current == "none":
            self.cookie_menu.set("None (No Cookies)")
        else:
            self.cookie_menu.set(current.capitalize())
        self.cookie_menu.pack(side="left")

        # 5. FFmpeg Diagnostics Card
        ff_card = ctk.CTkFrame(scroll, corner_radius=8)
        ff_card.pack(fill="x", padx=10, pady=8)

        ctk.CTkLabel(
            ff_card,
            text="FFmpeg Media Processor Diagnostics",
            font=ctk.CTkFont(size=14, weight="bold")
        ).pack(anchor="w", padx=15, pady=(12, 8))

        avail, ver_str, ff_path = FFmpegManager.get_status()

        status_box = ctk.CTkFrame(ff_card, fg_color=("gray85", "gray17"), corner_radius=6)
        status_box.pack(fill="x", padx=15, pady=(0, 15))

        status_icon = "✔️ Active & Ready" if avail else "❌ Missing"
        status_color = "#2FA572" if avail else "#D32F2F"

        top_s = ctk.CTkFrame(status_box, fg_color="transparent")
        top_s.pack(fill="x", padx=12, pady=(10, 4))

        ctk.CTkLabel(top_s, text="Status:", font=ctk.CTkFont(size=12, weight="bold")).pack(side="left", padx=(0, 8))
        ctk.CTkLabel(top_s, text=status_icon, font=ctk.CTkFont(size=12, weight="bold"), text_color=status_color).pack(side="left")

        v_row = ctk.CTkFrame(status_box, fg_color="transparent")
        v_row.pack(fill="x", padx=12, pady=(0, 4))
        ctk.CTkLabel(v_row, text="Version:", font=ctk.CTkFont(size=12, weight="bold")).pack(side="left", padx=(0, 8))
        ctk.CTkLabel(v_row, text=ver_str[:70], font=ctk.CTkFont(size=11), text_color="gray").pack(side="left")

        p_row = ctk.CTkFrame(status_box, fg_color="transparent")
        p_row.pack(fill="x", padx=12, pady=(0, 10))
        ctk.CTkLabel(p_row, text="Path:", font=ctk.CTkFont(size=12, weight="bold")).pack(side="left", padx=(0, 8))
        ctk.CTkLabel(p_row, text=ff_path or "N/A", font=ctk.CTkFont(size=11), text_color="#3B8ED0").pack(side="left")

        # 5. About & Capabilities Card
        about_card = ctk.CTkFrame(scroll, corner_radius=8)
        about_card.pack(fill="x", padx=10, pady=8)

        ctk.CTkLabel(
            about_card,
            text="Supported Formats & Sites",
            font=ctk.CTkFont(size=14, weight="bold")
        ).pack(anchor="w", padx=15, pady=(12, 6))

        info_text = (
            "• YouTube: 4K, 2K, 1080p Full HD, 720p, 480p, Playlists, MP3 audio 320kbps, Subtitles.\n"
            "• Universal Web Extractor: TikTok, Vimeo, Twitter/X, Reddit, Instagram, Facebook,\n"
            "  Dailymotion, Twitch, Rumble, Bilibili, and any webpage with HTML5 <video> or HLS/m3u8.\n"
            "• Fast multi-threaded processing with live speed, ETA, and progress estimation."
        )
        ctk.CTkLabel(
            about_card,
            text=info_text,
            font=ctk.CTkFont(size=12),
            text_color="gray",
            justify="left"
        ).pack(anchor="w", padx=15, pady=(0, 15))

    def change_folder(self):
        new_dir = filedialog.askdirectory(initialdir=self.download_dir)
        if new_dir:
            self.download_dir = new_dir
            self.lbl_path.configure(text=new_dir)
            self.on_dir_change(new_dir)

    def change_appearance_mode(self, new_mode: str):
        ctk.set_appearance_mode(new_mode)

    def change_color_theme(self, new_theme: str):
        ctk.set_default_color_theme(new_theme)
        messagebox.showinfo("Theme Changed", f"Theme set to {new_theme}. Please restart the application to apply full color scheme changes.")

    def change_browser_cookies(self, selection: str):
        val = "auto"
        if "None" in selection:
            val = "none"
        elif "Auto" in selection:
            val = "auto"
        else:
            val = selection.lower().strip()
        try:
            os.makedirs(os.path.dirname(CONFIG_PATH), exist_ok=True)
            cfg = {}
            if os.path.exists(CONFIG_PATH):
                with open(CONFIG_PATH, "r", encoding="utf-8") as f:
                    cfg = json.load(f)
            cfg["browser_cookies"] = val
            with open(CONFIG_PATH, "w", encoding="utf-8") as f:
                json.dump(cfg, f, indent=2)
            DownloaderEngine._cached_working_browser = None
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save cookie setting: {e}")

