"""SQLite engine bound to a local file. WAL mode, foreign keys on."""

from __future__ import annotations

from sqlalchemy import create_engine, event, text
from sqlalchemy.engine import Engine

from utils.config import get_settings

_engine: Engine | None = None


def _apply_sqlite_pragmas(dbapi_connection, _connection_record) -> None:
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.execute("PRAGMA journal_mode=WAL")
    cursor.execute("PRAGMA busy_timeout=5000")
    cursor.close()


def reset_engine() -> None:
    global _engine
    if _engine is not None:
        _engine.dispose()
        _engine = None
    from database import session as session_mod

    session_mod._session_factory = None


def get_engine(url: str | None = None) -> Engine:
    global _engine
    if url:
        reset_engine()
        _engine = create_engine(
            url,
            future=True,
            echo=False,
            connect_args={"check_same_thread": False},
        )
        event.listen(_engine, "connect", _apply_sqlite_pragmas)
        return _engine
    if _engine is None:
        settings = get_settings()
        _engine = create_engine(
            settings.database_url,
            future=True,
            echo=False,
            connect_args={"check_same_thread": False},
        )
        event.listen(_engine, "connect", _apply_sqlite_pragmas)
        with _engine.connect() as conn:
            conn.execute(text("SELECT 1"))
    return _engine
