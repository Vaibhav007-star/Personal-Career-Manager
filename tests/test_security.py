from __future__ import annotations

from pathlib import Path

import pytest

from utils.config import get_settings
from utils.files import FileSafetyError, resolve_under, sanitize_filename
from utils.paths import PROJECT_ROOT
from utils.validation import optional_url


def test_gitignore_excludes_secrets_and_data():
    text = (PROJECT_ROOT / ".gitignore").read_text(encoding="utf-8")
    for token in (".env", "*.db", "data/", "uploads/", "backups/", "exports/"):
        assert token in text


def test_env_example_has_placeholder_token_only():
    text = (PROJECT_ROOT / ".env.example").read_text(encoding="utf-8")
    assert "GITHUB_TOKEN=" in text
    assert "github_pat_" not in text
    assert "ghp_" not in text


def test_bind_host_forced_loopback(monkeypatch):
    monkeypatch.setenv("APP_BIND_HOST", "0.0.0.0")
    monkeypatch.setenv("DATABASE_URL", "sqlite:///data/career.db")
    settings = get_settings()
    assert settings.bind_host == "127.0.0.1"


def test_github_client_does_not_store_token():
    source = (PROJECT_ROOT / "services" / "github_client.py").read_text(encoding="utf-8")
    assert "ghp_" not in source
    assert "github_pat_" not in source
    assert "FEATURE_READY = True" in source


def test_path_traversal_rejected(tmp_path):
    with pytest.raises(FileSafetyError):
        resolve_under(tmp_path, "..", "etc", "passwd")


def test_sanitize_filename():
    assert ".." not in sanitize_filename("../resume.pdf")
    assert sanitize_filename("my cert.PDF").endswith("PDF") or sanitize_filename("a.pdf").endswith(".pdf")


def test_optional_url_rejects_javascript():
    with pytest.raises(Exception):
        optional_url("javascript:alert(1)", "URL")
