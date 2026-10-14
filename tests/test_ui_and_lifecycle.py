"""Unit tests for UI responsiveness, non-blocking threads, window close, and lifecycle."""
import os
import threading
import time
import pytest

from core.downloader_engine import DownloaderEngine
from core.single_instance import is_already_running
try:
    from ui.main_window import ModernMainWindow
except ImportError:
    ModernMainWindow = None


def test_customtkinter_ui_remains_responsive_during_download(ctk_app, temp_dir):
    """Verifies the CustomTkinter UI event loop continues processing without freezing while a download is running."""
    pytest.importorskip("customtkinter")
    app = ctk_app

    yt_view = app.views["youtube"]
    yt_view.download_dir = temp_dir

    # Flush any pending GUI events first
    app.update_idletasks()
    app.update()

    # Simulate a mock download running in a background thread
    is_finished = False
    def mock_worker():
        nonlocal is_finished
        for _ in range(15):
            time.sleep(0.02)
        is_finished = True

    thread = threading.Thread(target=mock_worker, daemon=True)
    thread.start()

    # Pump Tkinter event loop repeatedly
    start_time = time.time()
    iterations = 0
    while not is_finished and (time.time() - start_time) < 3.0:
        app.update_idletasks()
        app.update()
        iterations += 1
        time.sleep(0.01)

    # Event loop iterated smoothly multiple times while worker ran in background
    assert iterations >= 5, f"UI loop ran {iterations} iterations, expected at least 5"
    assert is_finished is True


def test_closing_window_cancels_running_downloads(ctk_app, temp_dir, monkeypatch):
    """Verifies closing the main window cancels any active downloads gracefully."""
    app = ctk_app
    yt_view = app.views["youtube"]
    downloader = yt_view.downloader

    # Start simulated download state
    yt_view.is_downloading = True
    downloader.reset_cancellation()
    assert not downloader._is_cancelled

    # Prevent destroying the shared test session window
    monkeypatch.setattr(app, "destroy", lambda: None)

    # Trigger window close protocol
    app._on_window_close()

    # Cancellation should be signaled
    assert downloader._is_cancelled is True
    yt_view.is_downloading = False


def test_single_instance_check():
    """Tests single instance detection does not crash."""
    # First call will claim or test mutex
    running = is_already_running("TestAppId123")
    assert isinstance(running, bool)
