from __future__ import annotations

import pytest

from database.engine import reset_engine
from database.init_db import init_database
from database.session import session_scope


@pytest.fixture
def initialized_db(tmp_path, monkeypatch):
    db_file = tmp_path / "career_test.db"
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{db_file.as_posix()}")
    reset_engine()
    init_database()
    yield db_file
    reset_engine()


@pytest.fixture
def db_session(initialized_db):
    with session_scope() as session:
        yield session
