"""Standalone Native Desktop Application powered by Edge WebView2 and Modern UI."""
import ctypes
import os
import socket
import sys
import threading
import time

from core.logger import get_logger
from core.single_instance import is_already_running

logger = get_logger()


def enable_windows_high_dpi_and_app_id():
    """Sets Windows High-DPI awareness and AppUserModelID for taskbar icon grouping."""
    if sys.platform == "win32":
        try:
            # Set AppUserModelID so Windows taskbar displays the custom app icon instead of Python's icon
            ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID("MediaPulsePro.UniversalDownloader.1.0")
        except Exception as e:
            logger.debug(f"Could not set AppUserModelID: {e}")

        try:
            # 2 = PROCESS_PER_MONITOR_DPI_AWARE
            ctypes.windll.shcore.SetProcessDpiAwareness(2)
        except Exception:
            try:
                ctypes.windll.user32.SetProcessDPIAware()
            except Exception:
                pass


def find_free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(('', 0))
        return s.getsockname()[1]


def is_webview2_available() -> bool:
    """Checks if Microsoft Edge WebView2 runtime is available on Windows."""
    if sys.platform != "win32":
        return True
    try:
        import winreg
        # Check both 64-bit and 32-bit registry keys for WebView2 Runtime
        keys = [
            (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\WOW6432Node\Microsoft\EdgeUpdate\Clients\{F3017226-FE2A-4295-8BDF-00C3A9A7E4C5}"),
            (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Microsoft\EdgeUpdate\Clients\{F3017226-FE2A-4295-8BDF-00C3A9A7E4C5}"),
            (winreg.HKEY_CURRENT_USER, r"Software\Microsoft\EdgeUpdate\Clients\{F3017226-FE2A-4295-8BDF-00C3A9A7E4C5}")
        ]
        for root_key, sub_key in keys:
            try:
                with winreg.OpenKey(root_key, sub_key):
                    return True
            except OSError:
                continue
        # Also test pywebview / pythonnet import
        import webview
        return True
    except Exception as e:
        logger.warning(f"WebView2 runtime check failed: {e}")
        return False


def run_modern_desktop():
    """Runs the modern Glassmorphism desktop app using pywebview and local backend."""
    enable_windows_high_dpi_and_app_id()

    # Single instance check
    if is_already_running():
        logger.warning("Another instance of MediaPulse Pro is already running.")
        if sys.platform == "win32":
            ctypes.windll.user32.MessageBoxW(
                0,
                "MediaPulse Pro is already running.\nPlease check your taskbar or system tray.",
                "MediaPulse Pro",
                0x40 | 0x0  # MB_ICONINFORMATION | MB_OK
            )
        sys.exit(0)

    # Check WebView2 runtime availability
    if not is_webview2_available():
        logger.error("Microsoft Edge WebView2 Runtime is required.")
        if sys.platform == "win32":
            res = ctypes.windll.user32.MessageBoxW(
                0,
                "MediaPulse Pro requires the Microsoft Edge WebView2 Runtime.\n\nWould you like to open the Microsoft download page to install it now?",
                "WebView2 Runtime Required",
                0x24 # MB_ICONQUESTION | MB_YESNO
            )
            if res == 6: # IDYES
                import webbrowser
                webbrowser.open("https://developer.microsoft.com/en-us/microsoft-edge/webview2/#download")
        sys.exit(1)

    import uvicorn
    import webview
    from web.server import app as fastapi_app, queue_mgr

    port = 8000
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.bind(('127.0.0.1', 8000))
    except OSError:
        port = find_free_port()

    # Start FastAPI server in background thread
    server_thread = threading.Thread(
        target=lambda: uvicorn.run(fastapi_app, host="127.0.0.1", port=port, log_level="warning"),
        daemon=True,
        name="UvicornServer"
    )
    server_thread.start()

    # Fast wait until FastAPI server is listening (replaces blocking 1.0s sleep)
    for _ in range(40):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(0.05)
            if s.connect_ex(('127.0.0.1', port)) == 0:
                break
        time.sleep(0.02)

    url = f"http://127.0.0.1:{port}/static/modern.html"

    # Locate application icon
    icon_candidates = []
    if getattr(sys, "frozen", False):
        meipass = getattr(sys, "_MEIPASS", "")
        if meipass:
            icon_candidates.append(os.path.join(meipass, "assets", "icon.ico"))
        exe_dir = os.path.dirname(sys.executable)
        icon_candidates.append(os.path.join(exe_dir, "_internal", "assets", "icon.ico"))
        icon_candidates.append(os.path.join(exe_dir, "assets", "icon.ico"))
    icon_candidates.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets", "icon.ico"))

    icon_path = None
    for c in icon_candidates:
        if os.path.exists(c):
            icon_path = c
            break


    # Launch native desktop window
    window = webview.create_window(
        title="MediaPulse Pro • Universal Video Downloader",
        url=url,
        width=1140,
        height=800,
        min_size=(920, 620),
        background_color="#090d16"
    )

    def on_closing():
        logger.info("Window closing event triggered. Shutting down queue and tasks gracefully.")
        try:
            queue_mgr.shutdown()
        except Exception as e:
            logger.error(f"Error during queue shutdown: {e}")

    window.events.closing += on_closing

    try:
        webview.start(private_mode=False, icon=icon_path)
    except Exception as e:
        logger.exception("Error starting webview window, falling back to CustomTkinter")
        from ui.main_window import ModernMainWindow
        fallback_app = ModernMainWindow()
        fallback_app.mainloop()


if __name__ == "__main__":
    run_modern_desktop()
