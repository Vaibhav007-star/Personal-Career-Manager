from __future__ import annotations

from io import StringIO

from utils.logging_config import RedactingFormatter
import logging


def test_logger_redacts_github_tokens():
    record = logging.LogRecord(
        name="t",
        level=logging.INFO,
        pathname=__file__,
        lineno=1,
        msg="Authorization: Bearer ghp_abcdefghijklmnopqrstuvwxyz0123456789",
        args=(),
        exc_info=None,
    )
    formatted = RedactingFormatter("%(message)s").format(record)
    assert "ghp_" not in formatted
    assert "[REDACTED]" in formatted
    stream = StringIO()
    assert "ghp_" not in stream.getvalue()
