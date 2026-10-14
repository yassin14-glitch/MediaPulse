"""Enhanced Universal Website Video Downloader Tab with modern card styling."""
import io
import os
import threading
import tkinter as tk
from tkinter import filedialog, messagebox
from typing import Any, Dict, List, Optional

import customtkinter as ctk
from PIL import Image
from core.downloader_engine import DownloaderEngine
from core.history_manager import HistoryManager
from core.web_extractor import WebVideoExtractor


class WebVideoTab(ctk.CTkFrame):
    """Tab to download videos from any website URL."""

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
        self.extractor = WebVideoExtractor()
        self.downloader = DownloaderEngine()
        self.discovered_videos: List[Dict[str, Any]] = []
        self.is_downloading = False
        self.active_download_title = ""

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
        top_row.pack(fill="x", padx=16, pady=(14, 4))

        lbl_header = ctk.CTkLabel(
            top_row,
            text="🌐  Universal Web Video Downloader",
            font=ctk.CTkFont(size=18, weight="bold"),
            text_color="#ffffff"
        )
        lbl_header.pack(side="left")

        ctk.CTkLabel(
            top_row,
            text="TikTok • Vimeo • Twitter/X • Reddit • Instagram • Facebook • HTML5 Videos",
            font=ctk.CTkFont(size=12),
            text_color="#94a3b8"
        ).pack(side="left", padx=(12, 0), pady=(3, 0))

        # URL Input Row
        input_row = ctk.CTkFrame(url_card, fg_color="transparent")
        input_row.pack(fill="x", padx=16, pady=(8, 14))

        self.url_entry = ctk.CTkEntry(
            input_row,
            placeholder_text="Enter any webpage URL (e.g. https://vimeo.com/... or TikTok, Reddit, blogs, direct video links)",
            height=44,
            corner_radius=8,
            border_width=1,
            border_color=self.COLOR_BORDER,
            fg_color="#0b1120",
            font=ctk.CTkFont(size=13)
        )
        self.url_entry.pack(side="left", fill="x", expand=True, padx=(0, 10))
        self.url_entry.bind("<Return>", lambda e: self.scan_url())

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

        self.btn_scan = ctk.CTkButton(
            input_row,
            text="🔍 Scan Videos",
            width=120,
            height=44,
            corner_radius=8,
            font=ctk.CTkFont(size=13, weight="bold"),
            fg_color=self.COLOR_ACCENT,
            hover_color="#2563eb",
            command=self.scan_url
        )
        self.btn_scan.pack(side="left")

        # 2. Results Header Bar
        results_bar = ctk.CTkFrame(
            self,
            corner_radius=8,
            fg_color=self.COLOR_CARD_SECONDARY,
            height=42
        )
        results_bar.pack(fill="x", padx=10, pady=(0, 6))

        self.lbl_results_info = ctk.CTkLabel(
            results_bar,
            text="Paste any website URL above and click 'Scan Videos' to extract video streams.",
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color="#cbd5e1"
        )
        self.lbl_results_info.pack(side="left", padx=16, pady=8)

        btn_folder = ctk.CTkButton(
            results_bar,
            text="📂 Downloads Folder",
            width=140,
            height=28,
            corner_radius=6,
            fg_color="#1e293b",
            hover_color="#334155",
            font=ctk.CTkFont(size=11),
            command=self.open_current_folder
        )
        btn_folder.pack(side="right", padx=12, pady=6)

        # 3. Discovered Streams Container
        self.results_scroll = ctk.CTkScrollableFrame(self, corner_radius=12, fg_color="transparent")
        self.results_scroll.pack(fill="both", expand=True, padx=4, pady=4)

        self._show_empty_state()

        # 4. Bottom Active Download & Progress Bar
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

        stat_row = ctk.CTkFrame(bottom_frame, fg_color="transparent")
        stat_row.pack(fill="x", padx=16, pady=(0, 8))

        self.lbl_status = ctk.CTkLabel(
            stat_row,
            text="Ready",
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

        action_row = ctk.CTkFrame(bottom_frame, fg_color="transparent")
        action_row.pack(fill="x", padx=16, pady=(0, 12))

        self.lbl_curr_downloading = ctk.CTkLabel(
            action_row,
            text="",
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color="#ffffff",
            anchor="w"
        )
        self.lbl_curr_downloading.pack(side="left", fill="x", expand=True)

        self.btn_cancel = ctk.CTkButton(
            action_row,
            text="⏹️ Cancel Download",
            height=38,
            corner_radius=8,
            font=ctk.CTkFont(size=12, weight="bold"),
            fg_color=self.COLOR_DANGER,
            hover_color="#b91c1c",
            width=150,
            state="disabled",
            command=self.cancel_download
        )
        self.btn_cancel.pack(side="right")

    def paste_url(self):
        try:
            clipboard = self.clipboard_get().strip()
            self.url_entry.delete(0, "end")
            self.url_entry.insert(0, clipboard)
            self.scan_url()
        except Exception:
            pass

    def open_current_folder(self):
        HistoryManager.open_folder(self.download_dir)

    def _show_empty_state(self):
        for widget in self.results_scroll.winfo_children():
            widget.destroy()

        empty_box = ctk.CTkFrame(
            self.results_scroll,
            corner_radius=12,
            fg_color=self.COLOR_CARD,
            border_width=1,
            border_color=self.COLOR_BORDER
        )
        empty_box.pack(fill="x", padx=16, pady=30)

        ctk.CTkLabel(
            empty_box,
            text="🌐",
            font=ctk.CTkFont(size=44)
        ).pack(pady=(24, 8))

        ctk.CTkLabel(
            empty_box,
            text="Universal Video Sniffer Ready",
            font=ctk.CTkFont(size=16, weight="bold"),
            text_color="#ffffff"
        ).pack(pady=(0, 6))

        info_p = (
            "Supports 1800+ websites and direct media players:\n"
            "• Social: TikTok, Vimeo, Twitter/X, Reddit, Instagram, Facebook, Dailymotion, Twitch\n"
            "• Deep Web Scraping: Extracts embedded <video> tags, OpenGraph cards, iframes\n"
            "• Streaming Streams: HLS (.m3u8), DASH (.mpd), and direct MP4/WebM files"
        )
        ctk.CTkLabel(
            empty_box,
            text=info_p,
            font=ctk.CTkFont(size=12),
            text_color="#94a3b8",
            justify="left"
        ).pack(padx=24, pady=(0, 24))

    def scan_url(self):
        url = self.url_entry.get().strip()
        if not url:
            messagebox.showwarning("URL Required", "Please enter a website URL.")
            return

        self.btn_scan.configure(state="disabled", text="Scanning...")
        self.lbl_results_info.configure(text=f"🔍 Scanning website for video streams: {url[:50]}...")
        self.lbl_status.configure(text="Inspecting webpage and media extractors...")

        threading.Thread(target=self._scan_worker, args=(url,), daemon=True).start()

    def _scan_worker(self, url: str):
        try:
            results = self.extractor.inspect_url(url)
            self.after(0, lambda: self._display_scan_results(results))
        except Exception as e:
            self.after(0, lambda: self._handle_scan_error(str(e)))

    def _handle_scan_error(self, err: str):
        self.btn_scan.configure(state="normal", text="🔍 Scan Videos")
        self.lbl_results_info.configure(text="Failed to scan website.")
        messagebox.showerror("Scan Error", f"Error scanning website:\n{err}")

    def _display_scan_results(self, results: Dict[str, Any]):
        self.btn_scan.configure(state="normal", text="🔍 Scan Videos")
        videos = results.get("videos", [])
        self.discovered_videos = videos
        count = len(videos)

        page_title = results.get("title", "")
        self.lbl_results_info.configure(
            text=f"Found {count} video stream{'s' if count != 1 else ''} on: {page_title[:55]}"
        )
        self.lbl_status.configure(text=f"Discovered {count} video sources. Ready to download.")

        # Clear scroll area
        for widget in self.results_scroll.winfo_children():
            widget.destroy()

        if not videos:
            no_box = ctk.CTkFrame(self.results_scroll, fg_color=self.COLOR_CARD, corner_radius=12)
            no_box.pack(fill="x", padx=16, pady=30)
            ctk.CTkLabel(
                no_box,
                text="⚠️ No direct video streams found on this webpage.",
                font=ctk.CTkFont(size=14, weight="bold"),
                text_color="#f87171"
            ).pack(pady=(20, 6))
            ctk.CTkLabel(
                no_box,
                text="The site may require login credentials or uses a DRM-encrypted player.",
                font=ctk.CTkFont(size=12),
                text_color="#94a3b8"
            ).pack(pady=(0, 20))
            return

        # Render cards for each discovered video
        for idx, vid in enumerate(videos):
            self._render_video_card(vid, idx)

    def _render_video_card(self, vid: Dict[str, Any], idx: int):
        card = ctk.CTkFrame(
            self.results_scroll,
            corner_radius=10,
            fg_color=self.COLOR_CARD,
            border_width=1,
            border_color=self.COLOR_BORDER
        )
        card.pack(fill="x", padx=6, pady=5)

        # Header with source badge
        header_row = ctk.CTkFrame(card, fg_color="transparent")
        header_row.pack(fill="x", padx=14, pady=(12, 4))

        type_badge = ctk.CTkLabel(
            header_row,
            text=f" {vid.get('type', 'Video')} ",
            font=ctk.CTkFont(size=10, weight="bold"),
            text_color="#93c5fd",
            fg_color="#1e3a8a",
            corner_radius=4,
            padx=6,
            pady=2
        )
        type_badge.pack(side="left", padx=(0, 10))

        title_lbl = ctk.CTkLabel(
            header_row,
            text=vid.get("title", f"Video Stream #{idx+1}"),
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color="#ffffff",
            anchor="w",
            wraplength=480,
            justify="left"
        )
        title_lbl.pack(side="left", fill="x", expand=True)

        # Details row
        details_row = ctk.CTkFrame(card, fg_color="transparent")
        details_row.pack(fill="x", padx=14, pady=(2, 12))

        url_snippet = vid.get("url", "")
        if len(url_snippet) > 75:
            url_snippet = url_snippet[:72] + "..."

        url_lbl = ctk.CTkLabel(
            details_row,
            text=f"Source: {url_snippet}",
            font=ctk.CTkFont(size=11),
            text_color="#94a3b8",
            anchor="w"
        )
        url_lbl.pack(side="left", fill="x", expand=True, padx=(0, 10))

        # Controls column on the right
        ctrl_frame = ctk.CTkFrame(details_row, fg_color="transparent")
        ctrl_frame.pack(side="right")

        format_menu = ctk.CTkOptionMenu(
            ctrl_frame,
            values=["Best Video (MP4)", "Audio Only (MP3)", "720p HD", "480p"],
            width=140,
            height=34,
            corner_radius=6,
            fg_color="#1e293b",
            button_color=self.COLOR_ACCENT
        )
        format_menu.set("Best Video (MP4)")
        format_menu.pack(side="left", padx=(0, 8))

        btn_download = ctk.CTkButton(
            ctrl_frame,
            text="⬇️ Download",
            width=115,
            height=34,
            corner_radius=6,
            font=ctk.CTkFont(size=12, weight="bold"),
            fg_color=self.COLOR_SUCCESS,
            hover_color=self.COLOR_SUCCESS_HOVER,
            command=lambda v=vid, fm=format_menu: self.start_web_download(v, fm.get())
        )
        btn_download.pack(side="left")

    def start_web_download(self, video_dict: Dict[str, Any], selected_format: str):
        if self.is_downloading:
            messagebox.showinfo("Download in Progress", "Please wait for current download to complete or cancel it.")
            return

        self.is_downloading = True
        self.btn_cancel.configure(state="normal")
        self.progress_bar.set(0)

        title = video_dict.get("title", "Web Video")
        self.active_download_title = title
        self.lbl_curr_downloading.configure(text=f"⬇️ Downloading: {title[:50]}")
        self.lbl_status.configure(text="Initializing download...")

        mode = "audio" if "Audio" in selected_format else "video"
        container = "mp3" if mode == "audio" else "mp4"
        quality = "best"
        if "720p" in selected_format:
            quality = "720p"
        elif "480p" in selected_format:
            quality = "480p"

        download_url = video_dict.get("url")

        threading.Thread(
            target=self._download_worker,
            args=(download_url, self.download_dir, mode, quality, container, title, video_dict.get("thumbnail", "")),
            daemon=True
        ).start()

    def _download_worker(self, url, out_dir, mode, quality, container, title, thumb):
        def progress_cb(data: Dict[str, Any]):
            self.after(0, lambda: self._on_progress_update(data))

        result = self.downloader.download(
            url=url,
            output_dir=out_dir,
            mode=mode,
            quality=quality,
            container=container,
            embed_subs=False,
            embed_thumbnail=False,
            progress_callback=progress_cb
        )

        self.after(0, lambda: self._on_download_complete(result, title, thumb))

    def _on_progress_update(self, data: Dict[str, Any]):
        status = data.get("status")
        percent = data.get("percent", 0.0) / 100.0
        self.progress_bar.set(percent)

        if status == "downloading":
            self.lbl_status.configure(text=f"Downloading ({data.get('percent', 0):.1f}%)")
            self.lbl_stats.configure(
                text=f"{data.get('downloaded_str', '')} / {data.get('total_str', '')}  |  ⚡ {data.get('speed_str', '')}  |  ⏳ {data.get('eta_str', '')}"
            )
        elif status == "processing":
            self.lbl_status.configure(text="⚙️ Merging & converting video stream...")
        elif status == "cancelled":
            self.lbl_status.configure(text="❌ Download Cancelled.")
            self.lbl_stats.configure(text="")

    def _on_download_complete(self, result: Dict[str, Any], fallback_title: str, thumb: str):
        self.is_downloading = False
        self.btn_cancel.configure(state="disabled")
        self.lbl_curr_downloading.configure(text="")

        if result.get("success"):
            self.progress_bar.set(1.0)
            self.lbl_status.configure(text="🎉 Download Completed Successfully!")
            self.lbl_stats.configure(text=f"Saved: {result.get('file_size')}")

            final_title = result.get("title") or fallback_title

            self.history_mgr.add_entry(
                url=result.get("url", ""),
                title=final_title,
                file_path=result.get("file_path", ""),
                file_size=result.get("file_size", "0 B"),
                format_info=result.get("format", "Web Video"),
                source="Web Extractor",
                thumbnail_url=thumb
            )

            ans = messagebox.askyesno(
                "Download Complete",
                f"Web video successfully downloaded:\n\n{final_title}\n\nWould you like to play it now?"
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
