"""Enhanced YouTube Downloader Tab with modern card styling and high-DPI visuals."""
import io
import os
import threading
import tkinter as tk
from tkinter import filedialog, messagebox
from typing import Any, Dict, Optional
from urllib.request import Request, urlopen

import customtkinter as ctk
from PIL import Image
from core.downloader_engine import DownloaderEngine
from core.history_manager import HistoryManager


class YouTubeTab(ctk.CTkFrame):
    """Tab dedicated to YouTube video and playlist downloading."""

    COLOR_CARD = "#131c2e"
    COLOR_CARD_SECONDARY = "#1a253b"
    COLOR_BORDER = "#23334d"
    COLOR_ACCENT = "#3b82f6"
    COLOR_SUCCESS = "#10b981"
    COLOR_SUCCESS_HOVER = "#059669"
    COLOR_DANGER = "#ef4444"

    def __init__(self, master, history_mgr: HistoryManager, default_download_dir: str):
        super().__init__(master, fg_color="transparent")
        self.history_mgr = history_mgr
        self.download_dir = default_download_dir
        self.downloader = DownloaderEngine()
        self.current_info: Optional[Dict[str, Any]] = None
        self.is_downloading = False

        self._build_ui()

    def _build_ui(self):
        # 1. Top URL Card
        url_card = ctk.CTkFrame(
            self,
            corner_radius=12,
            fg_color=self.COLOR_CARD,
            border_width=1,
            border_color=self.COLOR_BORDER
        )
        url_card.pack(fill="x", padx=10, pady=(4, 8))

        top_row = ctk.CTkFrame(url_card, fg_color="transparent")
        top_row.pack(fill="x", padx=16, pady=(14, 8))

        lbl_header = ctk.CTkLabel(
            top_row,
            text="📺  YouTube Downloader",
            font=ctk.CTkFont(size=18, weight="bold"),
            text_color="#ffffff"
        )
        lbl_header.pack(side="left")

        ctk.CTkLabel(
            top_row,
            text="Single Videos • Playlists • 4K/1080p • MP3 320kbps",
            font=ctk.CTkFont(size=12),
            text_color="#94a3b8"
        ).pack(side="left", padx=(12, 0), pady=(3, 0))

        # URL Input Row
        input_row = ctk.CTkFrame(url_card, fg_color="transparent")
        input_row.pack(fill="x", padx=16, pady=(0, 14))

        self.url_entry = ctk.CTkEntry(
            input_row,
            placeholder_text="Paste YouTube URL here (e.g. https://www.youtube.com/watch?v=...)",
            height=44,
            corner_radius=8,
            border_width=1,
            border_color=self.COLOR_BORDER,
            fg_color="#0b1120",
            font=ctk.CTkFont(size=13)
        )
        self.url_entry.pack(side="left", fill="x", expand=True, padx=(0, 10))
        self.url_entry.bind("<Return>", lambda e: self.fetch_info())

        btn_paste = ctk.CTkButton(
            input_row,
            text="📋 Paste",
            width=85,
            height=44,
            corner_radius=8,
            fg_color="#1e293b",
            hover_color="#334155",
            font=ctk.CTkFont(size=12, weight="bold"),
            command=self.paste_url
        )
        btn_paste.pack(side="left", padx=(0, 8))

        self.btn_fetch = ctk.CTkButton(
            input_row,
            text="🔍 Fetch Info",
            width=115,
            height=44,
            corner_radius=8,
            font=ctk.CTkFont(size=13, weight="bold"),
            fg_color=self.COLOR_ACCENT,
            hover_color="#2563eb",
            command=self.fetch_info
        )
        self.btn_fetch.pack(side="left")

        # 2. Main Scrollable Container for Preview & Config
        self.scroll_container = ctk.CTkScrollableFrame(self, corner_radius=12, fg_color="transparent")
        self.scroll_container.pack(fill="both", expand=True, padx=4, pady=4)

        # Video Preview Card
        self.preview_card = ctk.CTkFrame(
            self.scroll_container,
            corner_radius=12,
            fg_color=self.COLOR_CARD,
            border_width=1,
            border_color=self.COLOR_BORDER
        )
        self.preview_card.pack(fill="x", padx=6, pady=6)

        # Left: Thumbnail Box
        self.thumb_container = ctk.CTkFrame(
            self.preview_card,
            width=230,
            height=130,
            corner_radius=8,
            fg_color="#0b1120"
        )
        self.thumb_container.pack(side="left", padx=14, pady=14)
        self.thumb_container.pack_propagate(False)

        self.thumb_label = ctk.CTkLabel(
            self.thumb_container,
            text="🎬 Preview\nThumbnail",
            font=ctk.CTkFont(size=12),
            text_color="#64748b"
        )
        self.thumb_label.pack(expand=True)

        # Right: Info Column
        self.info_col = ctk.CTkFrame(self.preview_card, fg_color="transparent")
        self.info_col.pack(side="left", fill="both", expand=True, padx=(0, 14), pady=14)

        self.lbl_video_title = ctk.CTkLabel(
            self.info_col,
            text="No video loaded yet",
            font=ctk.CTkFont(size=15, weight="bold"),
            text_color="#ffffff",
            anchor="w",
            wraplength=480,
            justify="left"
        )
        self.lbl_video_title.pack(anchor="w", pady=(0, 6))

        # Badges row
        self.badges_row = ctk.CTkFrame(self.info_col, fg_color="transparent")
        self.badges_row.pack(anchor="w", pady=(0, 6))

        self.channel_badge = ctk.CTkLabel(
            self.badges_row,
            text="Channel: --",
            font=ctk.CTkFont(size=11, weight="bold"),
            text_color="#93c5fd",
            fg_color="#1e3a8a",
            corner_radius=4,
            padx=8,
            pady=3
        )
        self.channel_badge.pack(side="left", padx=(0, 8))

        self.duration_badge = ctk.CTkLabel(
            self.badges_row,
            text="Duration: --",
            font=ctk.CTkFont(size=11),
            text_color="#94a3b8",
            fg_color="#1e293b",
            corner_radius=4,
            padx=8,
            pady=3
        )
        self.duration_badge.pack(side="left", padx=(0, 8))

        self.views_badge = ctk.CTkLabel(
            self.badges_row,
            text="Views: --",
            font=ctk.CTkFont(size=11),
            text_color="#94a3b8",
            fg_color="#1e293b",
            corner_radius=4,
            padx=8,
            pady=3
        )
        self.views_badge.pack(side="left")

        self.playlist_checkbox = ctk.CTkCheckBox(
            self.info_col,
            text="Download entire playlist",
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color="#f8fafc"
        )

        # 3. Download Format & Quality Card
        options_card = ctk.CTkFrame(
            self.scroll_container,
            corner_radius=12,
            fg_color=self.COLOR_CARD,
            border_width=1,
            border_color=self.COLOR_BORDER
        )
        options_card.pack(fill="x", padx=6, pady=6)

        opt_header = ctk.CTkLabel(
            options_card,
            text="⚙️  Format & Quality Settings",
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color="#ffffff"
        )
        opt_header.pack(anchor="w", padx=16, pady=(12, 10))

        row_options = ctk.CTkFrame(options_card, fg_color="transparent")
        row_options.pack(fill="x", padx=16, pady=(0, 12))

        # Mode Selector
        col1 = ctk.CTkFrame(row_options, fg_color="transparent")
        col1.pack(side="left", padx=(0, 20))
        ctk.CTkLabel(col1, text="Download Mode:", font=ctk.CTkFont(size=11, weight="bold"), text_color="#94a3b8").pack(anchor="w", pady=(0, 4))
        self.mode_switch = ctk.CTkSegmentedButton(
            col1,
            values=["🎬 Video (MP4/MKV)", "🎵 Audio Only (MP3)"],
            font=ctk.CTkFont(size=12, weight="bold"),
            command=self._on_mode_change
        )
        self.mode_switch.set("🎬 Video (MP4/MKV)")
        self.mode_switch.pack()

        # Quality Selector
        col2 = ctk.CTkFrame(row_options, fg_color="transparent")
        col2.pack(side="left", padx=(0, 20))
        ctk.CTkLabel(col2, text="Quality / Resolution:", font=ctk.CTkFont(size=11, weight="bold"), text_color="#94a3b8").pack(anchor="w", pady=(0, 4))
        self.quality_options = [
            "Best Available",
            "4K (2160p)",
            "2K (1440p)",
            "1080p (Full HD)",
            "720p (HD)",
            "480p",
            "360p"
        ]
        self.quality_dropdown = ctk.CTkOptionMenu(
            col2,
            values=self.quality_options,
            width=170,
            height=36,
            corner_radius=8,
            fg_color="#1e293b",
            button_color=self.COLOR_ACCENT
        )
        self.quality_dropdown.set("Best Available")
        self.quality_dropdown.pack()

        # Container Selector
        col3 = ctk.CTkFrame(row_options, fg_color="transparent")
        col3.pack(side="left", padx=(0, 20))
        ctk.CTkLabel(col3, text="Container:", font=ctk.CTkFont(size=11, weight="bold"), text_color="#94a3b8").pack(anchor="w", pady=(0, 4))
        self.container_dropdown = ctk.CTkOptionMenu(
            col3,
            values=["mp4", "mkv", "webm"],
            width=100,
            height=36,
            corner_radius=8,
            fg_color="#1e293b",
            button_color=self.COLOR_ACCENT
        )
        self.container_dropdown.set("mp4")
        self.container_dropdown.pack()

        # Toggles Row
        toggles_row = ctk.CTkFrame(options_card, fg_color="transparent")
        toggles_row.pack(fill="x", padx=16, pady=(0, 14))

        self.cb_subs = ctk.CTkCheckBox(
            toggles_row,
            text="Embed Subtitles (English / Auto)",
            font=ctk.CTkFont(size=12),
            text_color="#f8fafc"
        )
        self.cb_subs.pack(side="left", padx=(0, 24))

        self.cb_thumb = ctk.CTkCheckBox(
            toggles_row,
            text="Embed Thumbnail / Cover Art",
            font=ctk.CTkFont(size=12),
            text_color="#f8fafc"
        )
        self.cb_thumb.pack(side="left")

        # 4. Save Folder Row
        dest_card = ctk.CTkFrame(
            self.scroll_container,
            corner_radius=12,
            fg_color=self.COLOR_CARD,
            border_width=1,
            border_color=self.COLOR_BORDER
        )
        dest_card.pack(fill="x", padx=6, pady=6)

        dest_row = ctk.CTkFrame(dest_card, fg_color="transparent")
        dest_row.pack(fill="x", padx=16, pady=12)

        ctk.CTkLabel(
            dest_row,
            text="📁 Destination:",
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color="#94a3b8"
        ).pack(side="left", padx=(0, 10))

        self.lbl_dest_path = ctk.CTkLabel(
            dest_row,
            text=self.download_dir,
            font=ctk.CTkFont(size=12),
            anchor="w",
            text_color="#60a5fa"
        )
        self.lbl_dest_path.pack(side="left", fill="x", expand=True, padx=(0, 10))

        ctk.CTkButton(
            dest_row,
            text="Browse...",
            width=85,
            height=32,
            corner_radius=6,
            fg_color="#1e293b",
            hover_color="#334155",
            command=self.browse_folder
        ).pack(side="right", padx=(6, 0))

        ctk.CTkButton(
            dest_row,
            text="Open Folder",
            width=95,
            height=32,
            corner_radius=6,
            fg_color="#1e293b",
            hover_color="#334155",
            command=self.open_current_folder
        ).pack(side="right")

        # 5. Bottom Fixed Download & Progress Bar
        bottom_frame = ctk.CTkFrame(
            self,
            corner_radius=12,
            fg_color=self.COLOR_CARD,
            border_width=1,
            border_color=self.COLOR_BORDER
        )
        bottom_frame.pack(fill="x", padx=10, pady=(6, 4))

        self.progress_bar = ctk.CTkProgressBar(
            bottom_frame,
            height=12,
            corner_radius=6,
            progress_color=self.COLOR_SUCCESS
        )
        self.progress_bar.set(0)
        self.progress_bar.pack(fill="x", padx=16, pady=(12, 6))

        # Status text row
        stat_row = ctk.CTkFrame(bottom_frame, fg_color="transparent")
        stat_row.pack(fill="x", padx=16, pady=(0, 8))

        self.lbl_status = ctk.CTkLabel(
            stat_row,
            text="Ready to download",
            font=ctk.CTkFont(size=12),
            text_color="#cbd5e1",
            anchor="w"
        )
        self.lbl_status.pack(side="left")

        self.lbl_stats = ctk.CTkLabel(
            stat_row,
            text="",
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color="#38bdf8",
            anchor="e"
        )
        self.lbl_stats.pack(side="right")

        # Buttons row
        action_row = ctk.CTkFrame(bottom_frame, fg_color="transparent")
        action_row.pack(fill="x", padx=16, pady=(0, 12))

        self.btn_download = ctk.CTkButton(
            action_row,
            text="🚀  Download Video Now",
            height=44,
            corner_radius=8,
            font=ctk.CTkFont(size=14, weight="bold"),
            fg_color=self.COLOR_SUCCESS,
            hover_color=self.COLOR_SUCCESS_HOVER,
            command=self.start_download
        )
        self.btn_download.pack(side="left", fill="x", expand=True, padx=(0, 10))

        self.btn_cancel = ctk.CTkButton(
            action_row,
            text="⏹️ Cancel",
            height=44,
            width=110,
            corner_radius=8,
            font=ctk.CTkFont(size=13, weight="bold"),
            fg_color=self.COLOR_DANGER,
            hover_color="#b91c1c",
            state="disabled",
            command=self.cancel_download
        )
        self.btn_cancel.pack(side="right")

    def paste_url(self):
        try:
            clipboard = self.clipboard_get().strip()
            self.url_entry.delete(0, "end")
            self.url_entry.insert(0, clipboard)
            self.fetch_info()
        except Exception:
            pass

    def browse_folder(self):
        selected = filedialog.askdirectory(initialdir=self.download_dir)
        if selected:
            self.download_dir = selected
            self.lbl_dest_path.configure(text=selected)

    def open_current_folder(self):
        HistoryManager.open_folder(self.download_dir)

    def _on_mode_change(self, mode_str: str):
        if "Audio" in mode_str:
            self.quality_dropdown.configure(values=["MP3 (320 kbps)", "M4A (AAC)", "WAV", "FLAC"])
            self.quality_dropdown.set("MP3 (320 kbps)")
            self.container_dropdown.configure(values=["mp3", "m4a", "wav", "flac"])
            self.container_dropdown.set("mp3")
            self.btn_download.configure(text="🎵  Download Audio Now")
        else:
            self.quality_dropdown.configure(values=self.quality_options)
            self.quality_dropdown.set("Best Available")
            self.container_dropdown.configure(values=["mp4", "mkv", "webm"])
            self.container_dropdown.set("mp4")
            self.btn_download.configure(text="🚀  Download Video Now")

    def fetch_info(self):
        url = self.url_entry.get().strip()
        if not url:
            messagebox.showwarning("Input Required", "Please enter a valid YouTube URL.")
            return

        self.btn_fetch.configure(state="disabled", text="Fetching...")
        self.lbl_status.configure(text="🔍 Fetching metadata from YouTube...")
        self.progress_bar.set(0)

        threading.Thread(target=self._fetch_info_worker, args=(url,), daemon=True).start()

    def _fetch_info_worker(self, url: str):
        try:
            info = self.downloader.fetch_info(url)
            self.current_info = info
            self.after(0, lambda: self._update_preview_ui(info))
        except Exception as e:
            self.after(0, lambda: self._handle_fetch_error(str(e)))

    def _update_preview_ui(self, info: Dict[str, Any]):
        self.btn_fetch.configure(state="normal", text="🔍 Fetch Info")
        self.lbl_status.configure(text="Ready to download.")

        # Update title & uploader
        self.lbl_video_title.configure(text=info.get("title", "YouTube Video"))
        self.channel_badge.configure(text=f"📺 {info.get('uploader', 'Unknown Channel')}")

        if info.get("is_playlist"):
            self.duration_badge.configure(text=f"📑 {info.get('count', 0)} videos")
            self.views_badge.configure(text="Playlist")
            self.playlist_checkbox.pack(anchor="w", pady=(6, 0))
            self.playlist_checkbox.select()
        else:
            self.playlist_checkbox.pack_forget()
            duration_sec = info.get("duration", 0)
            m, s = divmod(duration_sec, 60)
            h, m = divmod(m, 60)
            dur_str = f"{h:02d}:{m:02d}:{s:02d}" if h > 0 else f"{m:02d}:{s:02d}"
            views = f"{info.get('view_count', 0):,}"
            self.duration_badge.configure(text=f"⏱️ {dur_str}")
            self.views_badge.configure(text=f"👁️ {views} views")

        # Update resolutions
        available_res = info.get("available_resolutions", [])
        if available_res:
            opts = ["Best Available"] + available_res
            self.quality_options = opts
            if "Video" in self.mode_switch.get():
                self.quality_dropdown.configure(values=opts)
                self.quality_dropdown.set("Best Available")

        # Load thumbnail
        thumb_url = info.get("thumbnail")
        if thumb_url:
            threading.Thread(target=self._load_thumbnail, args=(thumb_url,), daemon=True).start()

    def _load_thumbnail(self, thumb_url: str):
        try:
            req = Request(thumb_url, headers={"User-Agent": "Mozilla/5.0"})
            with urlopen(req, timeout=8) as response:
                image_data = response.read()
            pil_img = Image.open(io.BytesIO(image_data))
            pil_img.thumbnail((230, 130), Image.Resampling.LANCZOS)
            ctk_img = ctk.CTkImage(light_image=pil_img, dark_image=pil_img, size=(230, 130))
            self.after(0, lambda: self.thumb_label.configure(image=ctk_img, text=""))
        except Exception:
            pass

    def _handle_fetch_error(self, err_msg: str):
        self.btn_fetch.configure(state="normal", text="🔍 Fetch Info")
        self.lbl_status.configure(text="Failed to fetch info.")
        messagebox.showerror("Fetch Error", f"Unable to fetch video details:\n{err_msg}")

    def start_download(self):
        url = self.url_entry.get().strip()
        if not url:
            messagebox.showwarning("URL Required", "Please enter a YouTube URL.")
            return

        if self.is_downloading:
            return

        self.is_downloading = True
        self.btn_download.configure(state="disabled")
        self.btn_cancel.configure(state="normal")
        self.progress_bar.set(0)
        self.lbl_status.configure(text="Connecting to video streams...")
        self.lbl_stats.configure(text="")

        mode = "audio" if "Audio" in self.mode_switch.get() else "video"
        quality_val = self.quality_dropdown.get()
        container_val = self.container_dropdown.get()
        embed_subs = bool(self.cb_subs.get())
        embed_thumb = bool(self.cb_thumb.get())
        download_playlist = bool(self.playlist_checkbox.get()) if self.current_info and self.current_info.get("is_playlist") else False

        threading.Thread(
            target=self._download_worker,
            args=(url, self.download_dir, mode, quality_val, container_val, embed_subs, embed_thumb, download_playlist),
            daemon=True
        ).start()

    def _download_worker(self, url, out_dir, mode, quality, container, subs, thumb, playlist):
        def progress_cb(data: Dict[str, Any]):
            self.after(0, lambda: self._on_progress_update(data))

        result = self.downloader.download(
            url=url,
            output_dir=out_dir,
            mode=mode,
            quality=quality,
            container=container,
            embed_subs=subs,
            embed_thumbnail=thumb,
            download_playlist=playlist,
            progress_callback=progress_cb
        )

        self.after(0, lambda: self._on_download_complete(result))

    def _on_progress_update(self, data: Dict[str, Any]):
        status = data.get("status")
        percent = data.get("percent", 0.0) / 100.0
        self.progress_bar.set(percent)

        if status == "downloading":
            self.lbl_status.configure(text=f"⬇️ {data.get('filename', '')} ({data.get('percent', 0):.1f}%)")
            self.lbl_stats.configure(
                text=f"{data.get('downloaded_str', '')} / {data.get('total_str', '')}  |  ⚡ {data.get('speed_str', '')}  |  ⏳ {data.get('eta_str', '')}"
            )
        elif status == "processing":
            self.lbl_status.configure(text="⚙️ Merging streams with FFmpeg 7.1...")
            self.lbl_stats.configure(text="Processing...")
        elif status == "cancelled":
            self.lbl_status.configure(text="❌ Download Cancelled.")
            self.lbl_stats.configure(text="")

    def _on_download_complete(self, result: Dict[str, Any]):
        self.is_downloading = False
        self.btn_download.configure(state="normal")
        self.btn_cancel.configure(state="disabled")

        if result.get("success"):
            self.progress_bar.set(1.0)
            self.lbl_status.configure(text="🎉 Download Completed Successfully!")
            self.lbl_stats.configure(text=f"Saved: {result.get('file_size')}")

            self.history_mgr.add_entry(
                url=result.get("url", ""),
                title=result.get("title", "YouTube Video"),
                file_path=result.get("file_path", ""),
                file_size=result.get("file_size", "0 B"),
                format_info=result.get("format", ""),
                source="YouTube",
                thumbnail_url=result.get("thumbnail", "")
            )

            ans = messagebox.askyesno(
                "Download Complete",
                f"Video successfully downloaded:\n\n{result.get('title')}\n\nWould you like to play it now?"
            )
            if ans and result.get("file_path"):
                HistoryManager.open_file(result["file_path"])
        else:
            if result.get("error") != "Download cancelled by user.":
                self.lbl_status.configure(text="❌ Download Failed.")
                messagebox.showerror("Download Error", f"Download failed:\n{result.get('error')}")

    def cancel_download(self):
        if self.is_downloading:
            self.lbl_status.configure(text="Cancelling download...")
            self.downloader.cancel()
