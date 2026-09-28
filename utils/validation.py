"""Input validation and sanitization used across forms and imports."""

from __future__ import annotations

import re
from datetime import date, datetime
from urllib.parse import urlparse

EMAIL_RE = re.compile(r"^[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}$")
SAFE_NAME_RE = re.compile(r"^[\w\s.&+\-/'()]{1,200}$", re.UNICODE)


class ValidationError(ValueError):
    pass


def require_text(value: str | None, field: str, min_len: int = 1, max_len: int = 200) -> str:
    text = (value or "").strip()
    if len(text) < min_len:
        raise ValidationError(f"{field} is required.")
    if len(text) > max_len:
        raise ValidationError(f"{field} must be at most {max_len} characters.")
    return text


def optional_text(value: str | None, field: str, max_len: int = 5000) -> str | None:
    text = (value or "").strip()
    if not text:
        return None
    if len(text) > max_len:
        raise ValidationError(f"{field} must be at most {max_len} characters.")
    return text


def optional_email(value: str | None) -> str | None:
    text = optional_text(value, "Email", 254)
    if text is None:
        return None
    if not EMAIL_RE.match(text):
        raise ValidationError("Email address is not valid.")
    return text.lower()


def optional_url(value: str | None, field: str = "URL") -> str | None:
    text = optional_text(value, field, 2000)
    if text is None:
        return None
    parsed = urlparse(text)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        raise ValidationError(f"{field} must be an http(s) URL.")
    return text


def parse_date(value: date | datetime | str | None, field: str = "Date") -> date | None:
    if value is None or value == "":
        return None
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    text = str(value).strip()
    for fmt in ("%Y-%m-%d", "%d-%m-%Y", "%d/%m/%Y"):
        try:
            return datetime.strptime(text, fmt).date()
        except ValueError:
            continue
    raise ValidationError(f"{field} must be a valid date (YYYY-MM-DD).")


def assert_date_order(start: date | None, end: date | None) -> None:
    if start and end and end < start:
        raise ValidationError("End date cannot be earlier than start date.")
