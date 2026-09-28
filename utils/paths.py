"""Project path helpers. All local data stays under the project root."""

from __future__ import annotations

from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_ROOT / "data"
LOG_DIR = PROJECT_ROOT / "logs"
UPLOAD_DIR = PROJECT_ROOT / "uploads"
BACKUP_DIR = PROJECT_ROOT / "backups"
BACKUPS_DIR = BACKUP_DIR
EXPORT_DIR = PROJECT_ROOT / "exports"
EXPORTS_DIR = EXPORT_DIR
ENV_FILE = PROJECT_ROOT / ".env"
ENV_EXAMPLE = PROJECT_ROOT / ".env.example"


def ensure_local_dirs() -> None:
    for path in (DATA_DIR, LOG_DIR, UPLOAD_DIR, BACKUP_DIR, EXPORT_DIR):
        path.mkdir(parents=True, exist_ok=True)
    gitkeep = DATA_DIR / ".gitkeep"
    if not gitkeep.exists():
        gitkeep.write_text("", encoding="utf-8")
