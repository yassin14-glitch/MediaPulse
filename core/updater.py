"""yt-dlp background update checker and in-app updater."""
import json
import subprocess
import sys
import threading
from typing import Optional, Tuple
import requests

import yt_dlp
from core.logger import get_logger

logger = get_logger()

_update_status = {
    "checked": False,
    "has_update": False,
    "current_version": getattr(yt_dlp.version, "__version__", "unknown"),
    "latest_version": None,
    "error": None
}


def get_current_version() -> str:
    return getattr(yt_dlp.version, "__version__", "unknown")


def check_for_updates() -> Tuple[bool, str, Optional[str]]:
    """Checks PyPI for the latest release of yt-dlp."""
    global _update_status
    current_ver = get_current_version()
    try:
        resp = requests.get("https://pypi.org/pypi/yt-dlp/json", timeout=6)
        if resp.status_code == 200:
            data = resp.json()
            latest_ver = data.get("info", {}).get("version")
            has_update = bool(latest_ver and latest_ver != current_ver)

            _update_status = {
                "checked": True,
                "has_update": has_update,
                "current_version": current_ver,
                "latest_version": latest_ver,
                "error": None
            }
            logger.info(f"yt-dlp update check: Current={current_ver}, Latest={latest_ver}, Available={has_update}")
            return has_update, current_ver, latest_ver
    except Exception as e:
        logger.warning(f"Failed to check yt-dlp updates: {e}")
        _update_status["checked"] = True
        _update_status["error"] = str(e)

    return False, current_ver, None


def get_update_status() -> dict:
    return _update_status


def perform_update() -> Tuple[bool, str]:
    """Updates yt-dlp using pip or yt-dlp self-update."""
    logger.info("Starting yt-dlp update...")
    try:
        # 1. Try pip update first
        result = subprocess.run(
            [sys.executable, "-m", "pip", "install", "--upgrade", "yt-dlp"],
            capture_output=True,
            text=True,
            timeout=120,
            creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0
        )
        if result.returncode == 0:
            logger.info("yt-dlp updated successfully via pip.")
            return True, "yt-dlp successfully updated to the latest version!"
        else:
            err = result.stderr or result.stdout or "Update process exited with error."
            logger.warning(f"pip update failed: {err}")
            return False, f"Update failed: {err[:150]}"
    except Exception as e:
        logger.exception("yt-dlp update exception")
        return False, f"Error updating yt-dlp: {str(e)}"


def start_background_check():
    """Starts background thread checking for updates on startup."""
    thread = threading.Thread(target=check_for_updates, daemon=True, name="YtDlpUpdateCheck")
    thread.start()
