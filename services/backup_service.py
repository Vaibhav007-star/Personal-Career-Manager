"""Encrypted Backup and Restore Service.

Uses industry-standard cryptography library (PBKDF2 + SHA-256 + Fernet AES).
Requires user password to encrypt and restore.
Tests SQLite database integrity upon decryption before applying.
"""

from __future__ import annotations

import base64
from datetime import datetime
import os
from pathlib import Path
import sqlite3
import tempfile

from cryptography.fernet import Fernet, InvalidToken
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

from utils.logging_config import get_logger
from utils.paths import BACKUPS_DIR, DATA_DIR

logger = get_logger("career_os.backup")

PBKDF2_ITERATIONS = 480_000
SALT_SIZE = 16


class BackupError(Exception):
    pass


class InvalidPasswordError(BackupError):
    pass


def _derive_key(password: str, salt: bytes) -> bytes:
    """Derive 32-byte key for Fernet using PBKDF2HMAC with SHA-256."""
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=salt,
        iterations=PBKDF2_ITERATIONS,
    )
    return base64.urlsafe_b64encode(kdf.derive(password.encode("utf-8")))


def create_encrypted_backup(password: str, custom_db_path: Path | None = None) -> Path:
    """Encrypts local SQLite database using user password and saves to backups/ directory."""
    if not password or len(password) < 6:
        raise BackupError("Password must be at least 6 characters long.")

    db_file = custom_db_path or (DATA_DIR / "career.db")
    if not db_file.exists():
        raise BackupError(f"Database file not found at {db_file}")

    db_bytes = db_file.read_bytes()
    salt = os.urandom(SALT_SIZE)
    key = _derive_key(password, salt)
    fernet = Fernet(key)

    encrypted_payload = fernet.encrypt(db_bytes)
    output_bundle = salt + encrypted_payload

    BACKUPS_DIR.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_file = BACKUPS_DIR / f"career_backup_{timestamp}.enc"
    backup_file.write_bytes(output_bundle)

    logger.info("Created encrypted backup: %s (%d bytes)", backup_file.name, len(output_bundle))
    return backup_file


def restore_encrypted_backup(
    backup_bytes: bytes, password: str, target_db_path: Path | None = None
) -> None:
    """Decrypts backup bundle, verifies SQLite integrity, and restores database."""
    if not password:
        raise BackupError("Password is required to decrypt backup.")

    if len(backup_bytes) <= SALT_SIZE:
        raise BackupError("Backup file is corrupt or invalid (too small).")

    salt = backup_bytes[:SALT_SIZE]
    ciphertext = backup_bytes[SALT_SIZE:]

    key = _derive_key(password, salt)
    fernet = Fernet(key)

    try:
        decrypted_bytes = fernet.decrypt(ciphertext)
    except InvalidToken as exc:
        raise InvalidPasswordError("Incorrect backup password or corrupted backup file.") from exc

    # Validate decrypted payload is a healthy SQLite database
    if not decrypted_bytes.startswith(b"SQLite format 3\000"):
        raise BackupError("Decrypted data is not a valid SQLite database.")

    # Integrity check in a temp file
    with tempfile.NamedTemporaryFile(delete=False, suffix=".db") as tmp:
        tmp.write(decrypted_bytes)
        tmp_path = Path(tmp.name)

    try:
        conn = sqlite3.connect(tmp_path)
        cur = conn.cursor()
        cur.execute("PRAGMA integrity_check")
        status = cur.fetchone()[0]
        conn.close()
        if status != "ok":
            raise BackupError(f"SQLite integrity check failed: {status}")
    finally:
        if tmp_path.exists():
            tmp_path.unlink()

    # Safely write to target DB
    destination = target_db_path or (DATA_DIR / "career.db")
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_bytes(decrypted_bytes)
    logger.info("Restored database from encrypted backup to %s", destination)
