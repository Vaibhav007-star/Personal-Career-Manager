"""Logging without secrets or personal payloads."""

from __future__ import annotations

import logging
import re
from logging.handlers import RotatingFileHandler

from utils.paths import LOG_DIR, ensure_local_dirs

_SECRET_PATTERNS = (
    re.compile(r"(github_pat_[A-Za-z0-9_]+)", re.I),
    re.compile(r"(ghp_[A-Za-z0-9_]+)", re.I),
    re.compile(r"(token['\"]?\s*[:=]\s*['\"]?)([^'\"\s]+)", re.I),
    re.compile(r"(authorization:\s*bearer\s+)(\S+)", re.I),
)


class RedactingFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        message = super().format(record)
        for pattern in _SECRET_PATTERNS:
            message = pattern.sub("[REDACTED]", message)
        return message


def get_logger(name: str = "career_os") -> logging.Logger:
    ensure_local_dirs()
    logger = logging.getLogger(name)
    if logger.handlers:
        return logger
    logger.setLevel(logging.INFO)
    formatter = RedactingFormatter("%(asctime)s %(levelname)s %(name)s - %(message)s")
    file_handler = RotatingFileHandler(
        LOG_DIR / "app.log",
        maxBytes=1_000_000,
        backupCount=3,
        encoding="utf-8",
    )
    file_handler.setFormatter(formatter)
    stream_handler = logging.StreamHandler()
    stream_handler.setFormatter(formatter)
    logger.addHandler(file_handler)
    logger.addHandler(stream_handler)
    logger.propagate = False
    return logger
