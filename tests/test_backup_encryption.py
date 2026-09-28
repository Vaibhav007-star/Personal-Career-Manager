from __future__ import annotations

import sqlite3
import pytest

from services.backup_service import (
    BackupError,
    InvalidPasswordError,
    create_encrypted_backup,
    restore_encrypted_backup,
)


def test_backup_and_restore_roundtrip(tmp_path):
    db_file = tmp_path / "test_career.db"
    conn = sqlite3.connect(db_file)
    cur = conn.cursor()
    cur.execute("CREATE TABLE test_data (id INTEGER PRIMARY KEY, note TEXT);")
    cur.execute("INSERT INTO test_data (note) VALUES ('secret placement note');")
    conn.commit()
    conn.close()

    password = "SuperSecretPassword123"

    backup_file = create_encrypted_backup(password, custom_db_path=db_file)
    assert backup_file.exists()
    assert backup_file.suffix == ".enc"

    raw_enc = backup_file.read_bytes()
    assert b"secret placement note" not in raw_enc

    with pytest.raises(InvalidPasswordError):
        restore_encrypted_backup(raw_enc, "WrongPassword999", target_db_path=tmp_path / "restored.db")

    restored_db = tmp_path / "restored.db"
    restore_encrypted_backup(raw_enc, password, target_db_path=restored_db)
    assert restored_db.exists()

    conn2 = sqlite3.connect(restored_db)
    cur2 = conn2.cursor()
    cur2.execute("SELECT note FROM test_data;")
    row = cur2.fetchone()
    conn2.close()
    assert row is not None
    assert row[0] == "secret placement note"


def test_short_password_rejected(tmp_path):
    db_file = tmp_path / "test.db"
    db_file.write_bytes(b"SQLite format 3\000fake")
    with pytest.raises(BackupError, match="at least 6 characters"):
        create_encrypted_backup("123", custom_db_path=db_file)
