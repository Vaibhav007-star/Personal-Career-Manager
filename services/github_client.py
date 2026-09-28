"""GitHub REST API Client for Personal Career Management System.

Supports public profile and repository synchronization.
Supports optional authenticated access to private repositories with explicit consent.
Handles rate limits, pagination, and token isolation. Tokens are never logged or stored.
"""

from __future__ import annotations

import base64
from datetime import datetime
import json
from typing import Any

import requests
from sqlalchemy.orm import Session

from database.crud import log_activity, upsert_github_repository
from utils.config import get_settings
from utils.logging_config import get_logger

logger = get_logger("career_os.github")

PHASE = 2
FEATURE_READY = True

GITHUB_API_BASE = "https://api.github.com"
DEFAULT_USER_AGENT = "PersonalCareerManager/1.0 (local-career-app)"


class GitHubError(Exception):
    """Base exception for GitHub API interactions."""
    pass


class GitHubRateLimitError(GitHubError):
    """Raised when GitHub API rate limit is exceeded."""
    def __init__(self, reset_timestamp: int | None = None):
        if reset_timestamp:
            reset_dt = datetime.fromtimestamp(reset_timestamp).strftime("%Y-%m-%d %H:%M:%S")
            message = f"GitHub API rate limit exceeded. Reset time: {reset_dt}."
        else:
            message = "GitHub API rate limit exceeded. Please try again later."
        super().__init__(message)
        self.reset_timestamp = reset_timestamp


class GitHubAuthError(GitHubError):
    """Raised when GitHub token or authentication fails."""
    pass


class GitHubClient:
    def __init__(self, token: str | None = None):
        self.token = token or get_settings().github_token
        self.session = requests.Session()
        self.session.headers.update(
            {
                "User-Agent": DEFAULT_USER_AGENT,
                "Accept": "application/vnd.github.v3+json",
            }
        )
        if self.token:
            self.session.headers["Authorization"] = f"Bearer {self.token.strip()}"

    def _check_rate_limit(self, response: requests.Response) -> None:
        remaining = response.headers.get("X-RateLimit-Remaining")
        reset_time = response.headers.get("X-RateLimit-Reset")
        if response.status_code == 403 and remaining == "0":
            reset_ts = int(reset_time) if reset_time and reset_time.isdigit() else None
            raise GitHubRateLimitError(reset_ts)
        if response.status_code == 401:
            raise GitHubAuthError("GitHub authentication failed. Check your local GITHUB_TOKEN.")

    def get_public_profile(self, username: str) -> dict[str, Any]:
        """Fetch public profile metadata for a username."""
        clean_user = username.strip()
        url = f"{GITHUB_API_BASE}/users/{clean_user}"
        resp = self.session.get(url, timeout=10)
        self._check_rate_limit(resp)
        if resp.status_code == 404:
            raise GitHubError(f"GitHub user '{clean_user}' not found.")
        resp.raise_for_status()
        data = resp.json()
        return {
            "login": data.get("login"),
            "name": data.get("name"),
            "bio": data.get("bio"),
            "public_repos": data.get("public_repos", 0),
            "followers": data.get("followers", 0),
            "html_url": data.get("html_url"),
            "avatar_url": data.get("avatar_url"),
        }

    def fetch_repositories(
        self, username: str, include_private: bool = False
    ) -> list[dict[str, Any]]:
        """Fetch repositories with pagination.
        If include_private is True, requires authenticated token.
        """
        clean_user = username.strip()
        repos: list[dict[str, Any]] = []

        if include_private:
            if not self.token:
                raise GitHubAuthError(
                    "Cannot import private repositories without a configured GITHUB_TOKEN."
                )
            url = f"{GITHUB_API_BASE}/user/repos"
            params: dict[str, Any] = {"per_page": 100, "sort": "pushed", "visibility": "all"}
        else:
            url = f"{GITHUB_API_BASE}/users/{clean_user}/repos"
            params = {"per_page": 100, "sort": "pushed", "type": "owner"}

        page = 1
        while True:
            params["page"] = page
            resp = self.session.get(url, params=params, timeout=15)
            self._check_rate_limit(resp)
            if resp.status_code == 404:
                raise GitHubError(f"Repositories for '{clean_user}' not found.")
            resp.raise_for_status()

            page_data = resp.json()
            if not isinstance(page_data, list) or not page_data:
                break

            for item in page_data:
                repos.append(item)

            if "next" not in resp.links:
                break
            page += 1
            if page > 10:
                break

        return repos

    def fetch_readme(self, owner: str, repo_name: str) -> str | None:
        """Fetch README content in markdown for a repository."""
        url = f"{GITHUB_API_BASE}/repos/{owner}/{repo_name}/readme"
        resp = self.session.get(
            url,
            headers={"Accept": "application/vnd.github.raw+json"},
            timeout=10,
        )
        if resp.status_code == 200:
            return resp.text[:15000]
        return None

    def sync_to_database(
        self,
        session: Session,
        username: str,
        include_private: bool = False,
        fetch_readmes: bool = False,
    ) -> dict[str, int]:
        """Synchronize GitHub repositories to SQLite database."""
        raw_repos = self.fetch_repositories(username, include_private=include_private)
        synced_count = 0

        for r in raw_repos:
            pushed_dt = None
            if r.get("pushed_at"):
                try:
                    pushed_dt = datetime.fromisoformat(r["pushed_at"].replace("Z", "+00:00"))
                except ValueError:
                    pass

            readme_text = None
            if fetch_readmes:
                try:
                    readme_text = self.fetch_readme(r["owner"]["login"], r["name"])
                except Exception as exc:
                    logger.debug("Could not fetch README for %s: %s", r.get("name"), exc)

            repo_payload = {
                "github_id": r["id"],
                "name": r["name"],
                "full_name": r["full_name"],
                "description": r.get("description"),
                "html_url": r["html_url"],
                "homepage": r.get("homepage"),
                "language": r.get("language"),
                "topics_json": json.dumps(r.get("topics", [])),
                "stars": r.get("stargazers_count", 0),
                "forks": r.get("forks_count", 0),
                "is_private": r.get("private", False),
                "is_fork": r.get("fork", False),
                "readme_content": readme_text,
                "pushed_at": pushed_dt,
            }
            upsert_github_repository(session, repo_payload)
            synced_count += 1

        log_activity(
            session,
            "sync",
            "github_importer",
            None,
            f"Synced {synced_count} repositories for user {username}",
        )
        return {"total_found": len(raw_repos), "synced": synced_count}


def import_public_profile(username: str) -> dict[str, Any]:
    """Convenience helper to fetch profile details."""
    client = GitHubClient()
    return client.get_public_profile(username)
