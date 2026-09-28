from __future__ import annotations

import pytest
import requests
from unittest.mock import MagicMock, patch

from database.models import GithubRepository
from services.github_client import (
    GitHubAuthError,
    GitHubClient,
    GitHubError,
    GitHubRateLimitError,
)


def test_github_client_init_headers():
    client = GitHubClient(token="test_fake_token_123")
    assert client.session.headers["Authorization"] == "Bearer test_fake_token_123"
    assert "PersonalCareerManager" in client.session.headers["User-Agent"]


def test_github_rate_limit_detection():
    client = GitHubClient()
    mock_resp = MagicMock()
    mock_resp.status_code = 403
    mock_resp.headers = {"X-RateLimit-Remaining": "0", "X-RateLimit-Reset": "1700000000"}

    with pytest.raises(GitHubRateLimitError) as exc_info:
        client._check_rate_limit(mock_resp)
    assert "rate limit exceeded" in str(exc_info.value).lower()
    assert exc_info.value.reset_timestamp == 1700000000


def test_github_auth_error_detection():
    client = GitHubClient()
    mock_resp = MagicMock()
    mock_resp.status_code = 401
    mock_resp.headers = {}

    with pytest.raises(GitHubAuthError):
        client._check_rate_limit(mock_resp)


@patch("requests.Session.get")
def test_get_public_profile(mock_get):
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.headers = {}
    mock_resp.json.return_value = {
        "login": "sample-dev",
        "name": "Sample Developer",
        "bio": "Aspiring Data Scientist",
        "public_repos": 15,
        "followers": 10,
        "html_url": "https://github.com/sample-dev",
        "avatar_url": "https://avatars.githubusercontent.com/u/12345",
    }
    mock_get.return_value = mock_resp

    client = GitHubClient()
    profile = client.get_public_profile("sample-dev")
    assert profile["login"] == "sample-dev"
    assert profile["public_repos"] == 15


@patch("requests.Session.get")
def test_sync_to_database(mock_get, db_session):
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.headers = {}
    mock_resp.links = {}
    mock_resp.json.return_value = [
        {
            "id": 99901,
            "name": "data-science-project",
            "full_name": "sample-dev/data-science-project",
            "description": "Customer churn predictor",
            "html_url": "https://github.com/sample-dev/data-science-project",
            "homepage": None,
            "language": "Python",
            "topics": ["pandas", "scikit-learn"],
            "stargazers_count": 5,
            "forks_count": 1,
            "private": False,
            "fork": False,
            "pushed_at": "2026-03-01T12:00:00Z",
            "owner": {"login": "sample-dev"},
        }
    ]
    mock_get.return_value = mock_resp

    client = GitHubClient()
    result = client.sync_to_database(db_session, "sample-dev", fetch_readmes=False)
    assert result["synced"] == 1

    repo = db_session.query(GithubRepository).filter_by(github_id=99901).first()
    assert repo is not None
    assert repo.name == "data-science-project"
    assert repo.language == "Python"
