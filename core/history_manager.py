"""Download history manager storing records in JSON."""
import json
import os
import subprocess
import time
import uuid
from typing import Dict, List, Optional


class HistoryManager:
    """Manages persistent download history."""

    def __init__(self, history_file: Optional[str] = None):
        if not history_file:
            user_data_dir = os.path.join(os.path.expanduser("~"), ".multimedia_downloader")
            os.makedirs(user_data_dir, exist_ok=True)
            self.history_file = os.path.join(user_data_dir, "history.json")
        else:
            self.history_file = history_file

        self._ensure_file()

    def _ensure_file(self):
        if not os.path.exists(self.history_file):
            with open(self.history_file, "w", encoding="utf-8") as f:
                json.dump([], f)

    def load_history(self) -> List[Dict]:
        try:
            with open(self.history_file, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return []

    def save_history(self, history: List[Dict]):
        try:
            with open(self.history_file, "w", encoding="utf-8") as f:
                json.dump(history, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"Error saving history: {e}")

    def add_entry(
        self,
        url: str,
        title: str,
        file_path: str,
        file_size: str,
        format_info: str,
        source: str = "YouTube",
        thumbnail_url: str = ""
    ) -> Dict:
        history = self.load_history()
        entry = {
            "id": str(uuid.uuid4()),
            "url": url,
            "title": title,
            "file_path": file_path,
            "file_size": file_size,
            "format": format_info,
            "source": source,
            "thumbnail_url": thumbnail_url,
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "exists": os.path.exists(file_path) if file_path else False
        }
        # Prepend so newest is first
        history.insert(0, entry)
        # Keep maximum 200 records
        if len(history) > 200:
            history = history[:200]
        self.save_history(history)
        return entry

    def delete_entry(self, entry_id: str):
        history = self.load_history()
        history = [e for e in history if e.get("id") != entry_id]
        self.save_history(history)

    def clear_history(self):
        self.save_history([])

    @staticmethod
    def open_file(file_path: str) -> bool:
        """Opens file in system default player."""
        if not file_path or not os.path.exists(file_path):
            return False
        try:
            if os.name == "nt":
                os.startfile(file_path)
            else:
                subprocess.Popen(["xdg-open", file_path])
            return True
        except Exception as e:
            print(f"Failed to open file: {e}")
            return False

    @staticmethod
    def open_folder(file_path: str) -> bool:
        """Opens explorer window with the file selected or folder open."""
        if not file_path:
            return False
        try:
            if os.name == "nt":
                if os.path.exists(file_path):
                    # Select the file
                    subprocess.Popen(f'explorer /select,"{os.path.normpath(file_path)}"')
                else:
                    parent = os.path.dirname(file_path)
                    if os.path.exists(parent):
                        subprocess.Popen(f'explorer "{os.path.normpath(parent)}"')
                    else:
                        return False
            else:
                parent = os.path.dirname(file_path) if os.path.isfile(file_path) else file_path
                subprocess.Popen(["xdg-open", parent])
            return True
        except Exception as e:
            print(f"Failed to open folder: {e}")
            return False
