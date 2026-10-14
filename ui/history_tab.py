"""Download History Tab for CustomTkinter GUI."""
import os
import tkinter as tk
from tkinter import messagebox
from typing import Dict, List

import customtkinter as ctk
from core.history_manager import HistoryManager


class HistoryTab(ctk.CTkFrame):
    """Tab to view and manage past downloads."""

    def __init__(self, master, history_mgr: HistoryManager, default_download_dir: str):
        super().__init__(master, fg_color="transparent")
        self.history_mgr = history_mgr
        self.download_dir = default_download_dir

        self._build_ui()

    def _build_ui(self):
        # 1. Header Row
        header_frame = ctk.CTkFrame(self, corner_radius=10)
        header_frame.pack(fill="x", padx=10, pady=(10, 5))

        lbl_title = ctk.CTkLabel(
            header_frame,
            text="📁 Download History",
            font=ctk.CTkFont(size=18, weight="bold")
        )
        lbl_title.pack(side="left", padx=15, pady=12)

        btn_open_folder = ctk.CTkButton(
            header_frame,
            text="📂 Open Downloads Folder",
            width=160,
            command=self.open_current_folder
        )
        btn_open_folder.pack(side="right", padx=(0, 15), pady=12)

        btn_clear = ctk.CTkButton(
            header_frame,
            text="🧹 Clear History",
            width=110,
            fg_color="#D32F2F",
            hover_color="#9A0007",
            command=self.clear_history
        )
        btn_clear.pack(side="right", padx=(0, 10), pady=12)

        btn_refresh = ctk.CTkButton(
            header_frame,
            text="🔄 Refresh",
            width=90,
            fg_color="gray30",
            hover_color="gray40",
            command=self.refresh_list
        )
        btn_refresh.pack(side="right", padx=(0, 10), pady=12)

        # 2. History Scrollable List
        self.history_scroll = ctk.CTkScrollableFrame(self, corner_radius=10)
        self.history_scroll.pack(fill="both", expand=True, padx=10, pady=5)

        self.refresh_list()

    def open_current_folder(self):
        HistoryManager.open_folder(self.download_dir)

    def clear_history(self):
        ans = messagebox.askyesno("Clear History", "Are you sure you want to clear your download history?\n(This will not delete the actual files on disk)")
        if ans:
            self.history_mgr.clear_history()
            self.refresh_list()

    def refresh_list(self):
        for widget in self.history_scroll.winfo_children():
            widget.destroy()

        history: List[Dict] = self.history_mgr.load_history()

        if not history:
            empty_box = ctk.CTkFrame(self.history_scroll, fg_color="transparent")
            empty_box.pack(pady=50)

            ctk.CTkLabel(
                empty_box,
                text="📂",
                font=ctk.CTkFont(size=44)
            ).pack(pady=(0, 10))

            ctk.CTkLabel(
                empty_box,
                text="No downloads yet",
                font=ctk.CTkFont(size=16, weight="bold")
            ).pack(pady=(0, 5))

            ctk.CTkLabel(
                empty_box,
                text="Downloaded videos from YouTube or other websites will show up here.",
                font=ctk.CTkFont(size=12),
                text_color="gray"
            ).pack()
            return

        for item in history:
            self._render_history_item(item)

    def _render_history_item(self, item: Dict):
        card = ctk.CTkFrame(self.history_scroll, corner_radius=8, fg_color=("gray85", "gray17"))
        card.pack(fill="x", padx=10, pady=5)

        # Main Info
        info_col = ctk.CTkFrame(card, fg_color="transparent")
        info_col.pack(side="left", fill="both", expand=True, padx=12, pady=10)

        top_row = ctk.CTkFrame(info_col, fg_color="transparent")
        top_row.pack(fill="x")

        source = item.get("source", "YouTube")
        badge_color = "#E53935" if source == "YouTube" else "#1E88E5"
        src_badge = ctk.CTkLabel(
            top_row,
            text=f" {source} ",
            font=ctk.CTkFont(size=10, weight="bold"),
            fg_color=badge_color,
            corner_radius=4
        )
        src_badge.pack(side="left", padx=(0, 8))

        title = item.get("title", "Downloaded Video")
        title_lbl = ctk.CTkLabel(
            top_row,
            text=title,
            font=ctk.CTkFont(size=13, weight="bold"),
            anchor="w",
            wraplength=480,
            justify="left"
        )
        title_lbl.pack(side="left", fill="x", expand=True)

        meta_row = ctk.CTkFrame(info_col, fg_color="transparent")
        meta_row.pack(fill="x", pady=(4, 0))

        file_path = item.get("file_path", "")
        exists = os.path.exists(file_path) if file_path else False
        exist_str = "✔️ Saved" if exists else "⚠️ File moved or deleted"
        exist_color = "gray" if exists else "#FFA000"

        details = f"{item.get('format', '')}  •  {item.get('file_size', '')}  •  {item.get('timestamp', '')}  •  {exist_str}"
        ctk.CTkLabel(
            meta_row,
            text=details,
            font=ctk.CTkFont(size=11),
            text_color=exist_color,
            anchor="w"
        ).pack(side="left")

        # Buttons on the right
        btn_frame = ctk.CTkFrame(card, fg_color="transparent")
        btn_frame.pack(side="right", padx=12, pady=10)

        if exists:
            btn_play = ctk.CTkButton(
                btn_frame,
                text="▶️ Play",
                width=75,
                height=30,
                fg_color="#2FA572",
                hover_color="#1E7A52",
                command=lambda p=file_path: HistoryManager.open_file(p)
            )
            btn_play.pack(side="left", padx=(0, 6))

            btn_show = ctk.CTkButton(
                btn_frame,
                text="📂 Show",
                width=75,
                height=30,
                fg_color="gray30",
                hover_color="gray40",
                command=lambda p=file_path: HistoryManager.open_folder(p)
            )
            btn_show.pack(side="left", padx=(0, 6))

        btn_del = ctk.CTkButton(
            btn_frame,
            text="❌",
            width=36,
            height=30,
            fg_color="transparent",
            hover_color="gray25",
            command=lambda eid=item.get("id"): self._delete_entry(eid)
        )
        btn_del.pack(side="left")

    def _delete_entry(self, entry_id: str):
        if entry_id:
            self.history_mgr.delete_entry(entry_id)
            self.refresh_list()
