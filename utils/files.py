"""Safe local file helpers: size limits and path-traversal protection."""

from __future__ import annotations

from pathlib import Path

from utils.paths import PROJECT_ROOT, UPLOAD_DIR


class FileSafetyError(ValueError):
    pass


ALLOWED_UPLOAD_SUFFIXES = {".pdf", ".docx", ".csv", ".xlsx", ".md", ".markdown", ".txt"}


def sanitize_filename(name: str) -> str:
    base = Path(name).name
    cleaned = "".join(ch if ch.isalnum() or ch in "._- " else "_" for ch in base).strip()
    if not cleaned or cleaned in {".", ".."}:
        raise FileSafetyError("Invalid file name.")
    return cleaned[:180]


def resolve_under(base: Path, *parts: str) -> Path:
    candidate = (base.joinpath(*parts)).resolve()
    base_resolved = base.resolve()
    if not str(candidate).startswith(str(base_resolved)):
        raise FileSafetyError("Path traversal is not allowed.")
    if not str(candidate).startswith(str(PROJECT_ROOT.resolve())):
        raise FileSafetyError("Files must stay inside the project directory.")
    return candidate


def ensure_upload_allowed(filename: str, size_bytes: int, max_mb: int) -> str:
    safe = sanitize_filename(filename)
    suffix = Path(safe).suffix.lower()
    if suffix not in ALLOWED_UPLOAD_SUFFIXES:
        raise FileSafetyError(f"File type {suffix or '(none)'} is not allowed.")
    if size_bytes > max_mb * 1024 * 1024:
        raise FileSafetyError(f"File exceeds the {max_mb} MB upload limit.")
    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    return safe
