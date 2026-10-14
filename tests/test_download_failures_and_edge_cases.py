"""Unit tests for download failures, network loss, cancellation, file collisions, and filesystem edge cases."""
import os
import sys
import pytest
from unittest.mock import MagicMock
from yt_dlp.utils import DownloadError

from core.downloader_engine import DownloaderEngine, DownloadCancelledException


def test_network_lost_halfway(temp_dir, monkeypatch):
    """Simulates network dropping midway through a download."""
    de = DownloaderEngine()

    def mock_extract_info(self, url, download=True):
        # Trigger download progress hook once
        for hook in self._progress_hooks:
            hook({
                "status": "downloading",
                "downloaded_bytes": 1048576,
                "total_bytes": 10485760,
                "speed": 500000,
                "eta": 18
            })
        # Then simulate connection drop
        raise DownloadError("ERROR: Connection reset by peer / network connection timed out")

    monkeypatch.setattr("yt_dlp.YoutubeDL.extract_info", mock_extract_info)

    res = de.download("https://example.com/video", output_dir=temp_dir)
    assert res["success"] is False
    assert "Network connection was lost or timed out" in res["error"]


def test_cancellation_mid_download(temp_dir, monkeypatch):
    """Simulates cancelling download while the engine is actively transferring data."""
    de = DownloaderEngine()

    def mock_extract_info(self, url, download=True):
        for hook in self._progress_hooks:
            hook({
                "status": "downloading",
                "downloaded_bytes": 500000,
                "total_bytes": 5000000
            })
            # Trigger cancellation during hook
            de.cancel()
            # Next tick will see cancellation
            hook({
                "status": "downloading",
                "downloaded_bytes": 600000,
                "total_bytes": 5000000
            })

    monkeypatch.setattr("yt_dlp.YoutubeDL.extract_info", mock_extract_info)

    res = de.download("https://example.com/video", output_dir=temp_dir)
    assert res["success"] is False
    assert "cancelled" in res["error"].lower()


def test_unwritable_download_directory(monkeypatch):
    """Tests that choosing an unwritable directory immediately produces a friendly message."""
    de = DownloaderEngine()

    # Mock os.makedirs / open to simulate PermissionError
    def mock_open(*args, **kwargs):
        raise PermissionError("Access is denied: 'C:\\Windows\\System32\\test'")

    monkeypatch.setattr("builtins.open", mock_open)

    res = de.download("https://example.com/video", output_dir="C:\\Windows\\System32\\unwritable")
    assert res["success"] is False
    assert "Cannot write to the chosen download folder" in res["error"]


def test_nonexistent_download_directory_autocreated(temp_dir):
    """Tests that a non-existent subfolder is automatically created without failing."""
    de = DownloaderEngine()
    nested_dir = os.path.join(temp_dir, "deeply", "nested", "video_dir")
    assert not os.path.exists(nested_dir)

    # Calling download with valid directory will create it
    # We mock yt_dlp extract_info to finish successfully
    mock_info = {"title": "Test Video", "id": "123", "ext": "mp4"}

    def mock_extract(self, url, download=True):
        fpath = os.path.join(nested_dir, "Test Video.mp4")
        with open(fpath, "w", encoding="utf-8") as f:
            f.write("dummy")
        return mock_info

    import yt_dlp
    orig_extract = yt_dlp.YoutubeDL.extract_info
    yt_dlp.YoutubeDL.extract_info = mock_extract

    try:
        res = de.download("https://example.com/video", output_dir=nested_dir)
        assert os.path.exists(nested_dir)
        assert res["success"] is True
    finally:
        yt_dlp.YoutubeDL.extract_info = orig_extract


def test_unicode_arabic_chinese_and_emoji_filenames(temp_dir):
    """Tests saving filenames with Arabic, Chinese, Japanese, and emoji characters."""
    de = DownloaderEngine()
    complex_title = "الدحيح_🔥_🚀_テスト_中文_Film_2026"

    mock_info = {"title": complex_title, "id": "unicode123", "ext": "mp4"}

    def mock_extract(self, url, download=True):
        clean_name = f"{complex_title}.mp4"
        fpath = os.path.join(temp_dir, clean_name)
        with open(fpath, "w", encoding="utf-8") as f:
            f.write("content")
        return {"requested_downloads": [{"filepath": fpath}], "title": complex_title}

    import yt_dlp
    orig_extract = yt_dlp.YoutubeDL.extract_info
    yt_dlp.YoutubeDL.extract_info = mock_extract

    try:
        res = de.download("https://example.com/unicode_video", output_dir=temp_dir)
        assert res["success"] is True
        assert res["file_path"] is not None
        assert os.path.exists(res["file_path"])
        assert "الدحيح" in res["title"]
        assert "🚀" in res["title"]
    finally:
        yt_dlp.YoutubeDL.extract_info = orig_extract


def test_very_long_filename_handling(temp_dir):
    """Tests that extremely long video titles (>200 chars) are trimmed safely on Windows."""
    de = DownloaderEngine()
    long_title = "A" * 300  # 300 character title exceeding standard Windows MAX_PATH

    mock_info = {"title": long_title, "id": "long123", "ext": "mp4"}

    def mock_extract(self, url, download=True):
        # yt-dlp trimmed filename
        trimmed = long_title[:150] + ".mp4"
        fpath = os.path.join(temp_dir, trimmed)
        with open(fpath, "w", encoding="utf-8") as f:
            f.write("dummy")
        return {"requested_downloads": [{"filepath": fpath}], "title": long_title}

    import yt_dlp
    orig_extract = yt_dlp.YoutubeDL.extract_info
    yt_dlp.YoutubeDL.extract_info = mock_extract

    try:
        res = de.download("https://example.com/long_video", output_dir=temp_dir)
        assert res["success"] is True
        assert os.path.exists(res["file_path"])
        # Filename on disk is bounded
        assert len(os.path.basename(res["file_path"])) <= 255
    finally:
        yt_dlp.YoutubeDL.extract_info = orig_extract


def test_file_already_exists_collision(temp_dir):
    """Tests downloading when a file with the same name already exists."""
    de = DownloaderEngine()
    existing_file = os.path.join(temp_dir, "Collision_Video.mp4")
    with open(existing_file, "w", encoding="utf-8") as f:
        f.write("already here")

    mock_info = {"title": "Collision_Video", "id": "c123", "ext": "mp4"}

    def mock_extract(self, url, download=True):
        # yt-dlp appends or overwrites cleanly
        return {"requested_downloads": [{"filepath": existing_file}], "title": "Collision_Video"}

    import yt_dlp
    orig_extract = yt_dlp.YoutubeDL.extract_info
    yt_dlp.YoutubeDL.extract_info = mock_extract

    try:
        res = de.download("https://example.com/collision", output_dir=temp_dir)
        assert res["success"] is True
        assert os.path.exists(res["file_path"])
    finally:
        yt_dlp.YoutubeDL.extract_info = orig_extract
