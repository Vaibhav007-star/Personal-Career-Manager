"""Application configuration. Secrets are never returned to the UI."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

from utils.paths import DATA_DIR, ENV_FILE, PROJECT_ROOT, ensure_local_dirs


def _load_env() -> None:
    if ENV_FILE.exists():
        load_dotenv(ENV_FILE, override=False)
    else:
        load_dotenv(PROJECT_ROOT / ".env.example", override=False)


_load_env()
ensure_local_dirs()


def _bool(value: str | None, default: bool = False) -> bool:
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


@dataclass(frozen=True)
class Settings:
    bind_host: str
    port: int
    database_url: str
    github_username: str
    log_level: str
    max_upload_mb: int
    has_github_token: bool
    sample_data_loaded: bool

    @property
    def github_token(self) -> str | None:
        """Return the token only for service-layer use. Never log or display it."""
        raw = os.environ.get("GITHUB_TOKEN", "").strip()
        return raw or None


def _resolve_database_url(raw: str) -> str:
    raw = (raw or "").strip()
    if not raw:
        db_path = DATA_DIR / "career.db"
        return f"sqlite:///{db_path.as_posix()}"
    if raw.startswith("sqlite:///"):
        path_part = raw[len("sqlite:///") :]
        path = Path(path_part)
        if not path.is_absolute():
            path = PROJECT_ROOT / path
        path.parent.mkdir(parents=True, exist_ok=True)
        return f"sqlite:///{path.as_posix()}"
    raise ValueError("Only local sqlite:/// database URLs are supported in this application.")


def get_settings() -> Settings:
    host = os.environ.get("APP_BIND_HOST", "127.0.0.1").strip() or "127.0.0.1"
    if host not in {"127.0.0.1", "localhost"}:
        host = "127.0.0.1"
    port = int(os.environ.get("APP_PORT", "8501"))
    return Settings(
        bind_host=host,
        port=port,
        database_url=_resolve_database_url(os.environ.get("DATABASE_URL", "")),
        github_username=os.environ.get("GITHUB_USERNAME", "vaibhav007-star").strip(),
        log_level=os.environ.get("LOG_LEVEL", "INFO").strip().upper(),
        max_upload_mb=int(os.environ.get("MAX_UPLOAD_MB", "10")),
        has_github_token=bool(os.environ.get("GITHUB_TOKEN", "").strip()),
        sample_data_loaded=_bool(os.environ.get("SAMPLE_DATA_LOADED"), False),
    )
