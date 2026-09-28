"""Ensure the local SQLite file exists before Streamlit pages query it."""

from __future__ import annotations

from database.init_db import init_database


def bootstrap() -> None:
    init_database()
