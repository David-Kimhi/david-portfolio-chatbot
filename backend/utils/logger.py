import logging
import os
from logging.handlers import TimedRotatingFileHandler

# Log directory: prefer LOG_DIR env var, fall back to repo-local ./logs
LOG_DIR = os.getenv("LOG_DIR", "./logs")
os.makedirs(LOG_DIR, exist_ok=True)

LOG_FILE = os.path.join(LOG_DIR, "api.log")

# Log format: timestamp | level | message
_FORMATTER = logging.Formatter(
    fmt="%(asctime)s | %(levelname)-8s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)


def _build_logger() -> logging.Logger:
    logger = logging.getLogger("portfoliochat")
    logger.setLevel(logging.INFO)

    if logger.handlers:
        # Avoid adding duplicate handlers on hot-reload
        return logger

    # File handler: rotates daily, keeps 14 days of history
    file_handler = TimedRotatingFileHandler(
        LOG_FILE,
        when="midnight",
        interval=1,
        backupCount=14,
        encoding="utf-8",
    )
    file_handler.setFormatter(_FORMATTER)
    file_handler.suffix = "%Y-%m-%d"

    # Console handler: also prints to stdout (visible in Docker logs)
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(_FORMATTER)

    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

    return logger


# Single shared logger instance — import this everywhere
log = _build_logger()
