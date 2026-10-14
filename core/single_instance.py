"""Single instance application lock for Windows and cross-platform."""
import ctypes
import os
import socket
import sys
from core.logger import get_logger

logger = get_logger()

_lock_socket: socket.socket = None
_mutex_handle = None


def is_already_running(app_id: str = "MediaPulseProSingleInstance") -> bool:
    """Returns True if another instance of the application is already running."""
    global _lock_socket, _mutex_handle

    # Method 1: Windows Named Mutex
    if sys.platform == "win32":
        try:
            mutex_name = f"Local\\{app_id}Mutex"
            _mutex_handle = ctypes.windll.kernel32.CreateMutexW(None, False, mutex_name)
            last_error = ctypes.windll.kernel32.GetLastError()
            ERROR_ALREADY_EXISTS = 183
            if last_error == ERROR_ALREADY_EXISTS:
                logger.warning("Another instance detected via Windows Mutex.")
                return True
            return False
        except Exception as e:
            logger.debug(f"Mutex creation failed, falling back to socket lock: {e}")

    # Method 2: Localhost socket lock fallback
    try:
        _lock_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        # Port 49281 reserved for single instance lock
        _lock_socket.bind(("127.0.0.1", 49281))
        return False
    except OSError:
        logger.warning("Another instance detected via socket lock on port 49281.")
        return True
