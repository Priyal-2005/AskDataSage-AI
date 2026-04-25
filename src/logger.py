"""
AskDataSage AI — Logging Module
Configures structured logging with file rotation for query tracking and error diagnostics.
"""

import logging
import os
from logging.handlers import RotatingFileHandler

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
LOG_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "logs")
LOG_FILE = os.path.join(LOG_DIR, "app.log")
MAX_LOG_SIZE = 5 * 1024 * 1024  # 5 MB
BACKUP_COUNT = 3

# ---------------------------------------------------------------------------
# Logger setup
# ---------------------------------------------------------------------------

def get_logger(name: str = "askdatasage") -> logging.Logger:
    """
    Return a configured logger instance.

    - Logs to both console (INFO) and rotating file (DEBUG).
    - File rotates at 5 MB, keeps 3 backups.
    """
    logger = logging.getLogger(name)

    # Avoid adding duplicate handlers on re-import
    if logger.handlers:
        return logger

    logger.setLevel(logging.DEBUG)

    # Ensure log directory exists
    os.makedirs(LOG_DIR, exist_ok=True)

    # --- File handler (DEBUG level) ---
    file_handler = RotatingFileHandler(
        LOG_FILE,
        maxBytes=MAX_LOG_SIZE,
        backupCount=BACKUP_COUNT,
        encoding="utf-8",
    )
    file_handler.setLevel(logging.DEBUG)
    file_fmt = logging.Formatter(
        "%(asctime)s | %(levelname)-8s | %(name)s.%(funcName)s:%(lineno)d | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    file_handler.setFormatter(file_fmt)

    # --- Console handler (INFO level) ---
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_fmt = logging.Formatter(
        "%(asctime)s | %(levelname)-8s | %(message)s",
        datefmt="%H:%M:%S",
    )
    console_handler.setFormatter(console_fmt)

    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

    return logger
