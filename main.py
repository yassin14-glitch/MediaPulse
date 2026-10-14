"""Master Entry Point for the Universal Media Downloader."""
import argparse
import sys
import webbrowser


def run_customtkinter_app():
    """Launches the CustomTkinter Native Desktop Application."""
    try:
        from ui.main_window import ModernMainWindow
        app = ModernMainWindow()
        app.mainloop()
    except Exception as e:
        print(f"Error launching CustomTkinter application: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


def run_modern_app():
    """Launches the Ultra-Modern Glassmorphism Desktop Application."""
    try:
        from desktop_app import run_modern_desktop
        run_modern_desktop()
    except Exception as e:
        print(f"Modern window renderer notice: {e}")
        print("Launching CustomTkinter sidebar desktop app...")
        run_customtkinter_app()


def run_web_app(host: str = "127.0.0.1", port: int = 8000, open_browser: bool = True):
    """Launches the local FastAPI Web Server with browser dashboard."""
    try:
        import uvicorn
        from web.server import app

        url = f"http://{host}:{port}/static/modern.html"
        print("=" * 60)
        print(f"🚀 Universal Media Downloader Web Dashboard starting at: {url}")
        print("Press Ctrl+C to stop the server.")
        print("=" * 60)

        if open_browser:
            import threading
            import time
            def launch_browser():
                time.sleep(1.2)
                webbrowser.open(url)
            threading.Thread(target=launch_browser, daemon=True).start()

        uvicorn.run(app, host=host, port=port, log_level="info")
    except Exception as e:
        print(f"Error launching web server: {e}")
        sys.exit(1)


def main():
    parser = argparse.ArgumentParser(
        description="Universal Media Downloader (YouTube & Any Website)"
    )
    parser.add_argument(
        "--web",
        action="store_true",
        help="Launch as a browser-based Web UI application"
    )
    parser.add_argument(
        "--native",
        action="store_true",
        help="Launch the CustomTkinter Native Desktop GUI"
    )
    parser.add_argument(
        "--modern",
        action="store_true",
        help="Launch the Ultra-Modern Glassmorphism Desktop App"
    )
    parser.add_argument(
        "--host",
        type=str,
        default="127.0.0.1",
        help="Host address for the Web UI (default: 127.0.0.1)"
    )
    parser.add_argument(
        "--port",
        type=int,
        default=8000,
        help="Port for the Web UI (default: 8000)"
    )
    parser.add_argument(
        "--no-browser",
        action="store_true",
        help="Do not auto-open default browser when starting web UI"
    )

    args = parser.parse_args()

    if args.web:
        run_web_app(host=args.host, port=args.port, open_browser=not args.no_browser)
    elif args.native:
        run_customtkinter_app()
    else:
        # Default: Modern Glassmorphism Desktop App with auto-fallback
        run_modern_app()


if __name__ == "__main__":
    main()
