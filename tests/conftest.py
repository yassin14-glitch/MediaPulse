"""Pytest configuration and shared fixtures."""
import os
import shutil
import sys
import tempfile
import pytest

# Ensure project root is in sys.path
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

# Reconfigure console output for Windows UTF-8
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass


def pytest_configure(config):
    config.addinivalue_line(
        "markers", "slow: marks tests as slow (deselect with '-m \"not slow\"')"
    )


@pytest.fixture
def temp_dir():
    """Provides a fresh temporary directory that is cleaned up after test."""
    d = tempfile.mkdtemp(prefix="mp_test_")
    yield d
    shutil.rmtree(d, ignore_errors=True)


@pytest.fixture
def mock_ffmpeg(monkeypatch):
    """Mocks FFmpegManager to return a dummy path for fast isolated testing."""
    from core.ffmpeg_manager import FFmpegManager
    monkeypatch.setattr(FFmpegManager, "get_ffmpeg_path", lambda: "mock_ffmpeg.exe")
    monkeypatch.setattr(FFmpegManager, "get_status", lambda: (True, "FFmpeg 7.1 Mock", "mock_ffmpeg.exe"))


@pytest.fixture(scope="session")
def ctk_app():
    """Provides a shared CustomTkinter root window across the test session."""
    try:
        from ui.main_window import ModernMainWindow
        app = ModernMainWindow()
        app.withdraw()
        app.update_idletasks()
        app.update()
        yield app
        try:
            app.destroy()
        except Exception:
            pass
    except Exception as e:
        pytest.skip(f"Tkinter display not available: {e}")

