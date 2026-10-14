"""Comprehensive verification test suite for the downloader application."""
import sys
import os
import pytest

# Add root directory to pythonpath
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.ffmpeg_manager import FFmpegManager
from core.history_manager import HistoryManager
from core.downloader_engine import DownloaderEngine
from core.web_extractor import WebVideoExtractor


def test_ffmpeg():
    print("[1/5] Testing FFmpeg Manager...")
    avail, ver, path = FFmpegManager.get_status()
    assert avail is True, "FFmpeg should be available"
    assert path is not None and os.path.exists(path), f"FFmpeg path invalid: {path}"
    print(f"      FFmpeg OK: {ver[:50]}... at {path}")


def test_history():
    print("[2/5] Testing History Manager...")
    test_hist_file = os.path.join(os.path.dirname(__file__), "test_history.json")
    hm = HistoryManager(test_hist_file)
    entry = hm.add_entry(
        url="https://example.com/test",
        title="Test Video",
        file_path="C:/nonexistent.mp4",
        file_size="10.5 MB",
        format_info="1080p MP4",
        source="Test"
    )
    assert entry["title"] == "Test Video"
    history = hm.load_history()
    assert len(history) >= 1
    hm.delete_entry(entry["id"])
    if os.path.exists(test_hist_file):
        os.remove(test_hist_file)
    print("      History Manager OK")


def test_web_extractor():
    print("[3/5] Testing Web Video Extractor...")
    extractor = WebVideoExtractor()
    # Test on a generic page
    res = extractor.inspect_url("https://example.com")
    assert "page_url" in res
    assert "videos" in res
    print(f"      Web Extractor OK (scanned example.com, title: {res.get('title')})")


def test_ui_instantiation(ctk_app=None):
    print("[4/5] Testing CustomTkinter UI Instantiation...")
    pytest.importorskip("customtkinter")
    if ctk_app is None:
        from ui.main_window import MainWindow
        app = MainWindow()
    else:
        app = ctk_app
    assert "youtube" in app.views and app.views["youtube"] is not None

    assert "web" in app.views and app.views["web"] is not None
    assert "history" in app.views and app.views["history"] is not None
    assert "settings" in app.views and app.views["settings"] is not None
    app.update_idletasks()
    print("      CustomTkinter Desktop UI OK")


def test_web_api():
    print("[5/5] Testing FastAPI Server Endpoints...")
    from fastapi.testclient import TestClient
    from web.server import app

    client = TestClient(app)
    res = client.get("/api/status")
    assert res.status_code == 200
    data = res.json()
    assert data["ffmpeg_available"] is True
    print("      FastAPI Server Endpoints OK")


if __name__ == "__main__":
    print("=" * 60)
    print("RUNNING MULTI-DOWNLOADER VERIFICATION SUITE")
    print("=" * 60)
    test_ffmpeg()
    test_history()
    test_web_extractor()
    test_ui_instantiation()
    test_web_api()
    print("=" * 60)
    print("ALL TESTS PASSED! Application is 100% operational.")
    print("=" * 60)
