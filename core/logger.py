"""Application logging infrastructure with rotating file handlers and user-data storage."""
import logging
from logging.handlers import RotatingFileHandler
import os
import sys

# Standard App Data path for logs and config
APP_DATA_DIR = os.path.join(os.path.expanduser("~"), ".multimedia_downloader")
LOG_DIR = os.path.join(APP_DATA_DIR, "logs")
os.makedirs(LOG_DIR, exist_ok=True)
LOG_FILE = os.path.join(LOG_DIR, "app.log")

_logger = None

def get_logger() -> logging.Logger:
    """Returns the application singleton logger."""
    global _logger
    if _logger is not None:
        return _logger

    _logger = logging.getLogger("MediaPulsePro")
    _logger.setLevel(logging.DEBUG)

    # Avoid adding duplicate handlers if re-called
    if not _logger.handlers:
        # Rotating File Handler (Max 5MB, keep 3 backups)
        file_handler = RotatingFileHandler(
            LOG_FILE,
            maxBytes=5 * 1024 * 1024,
            backupCount=3,
            encoding="utf-8"
        )
        file_handler.setLevel(logging.DEBUG)
        file_formatter = logging.Formatter(
            "[%(asctime)s] [%(levelname)s] [%(threadName)s] %(name)s: %(message)s"
        )
        file_handler.setFormatter(file_formatter)
        _logger.addHandler(file_handler)

        # Console Handler
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.INFO)
        console_formatter = logging.Formatter(
            "[%(levelname)s] %(message)s"
        )
        console_handler.setFormatter(console_formatter)
        _logger.addHandler(console_handler)

    return _logger

def log_exception(msg: str, exc: Exception):
    """Logs an exception with full traceback to log file."""
    logger = get_logger()
    logger.exception(f"{msg}: {exc}")
