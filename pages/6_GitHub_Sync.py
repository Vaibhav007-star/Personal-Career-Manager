"""GitHub Integration & Repository Sync."""

from __future__ import annotations

import json
import pandas as pd
import streamlit as st

from components.layout import page_setup
from components.ui import dataframe_download, empty_state
from database.crud import (
    create_project,
    get_profile,
    list_github_repositories,
    list_projects,
)
from database.session import session_scope
from services.github_client import (
    GitHubAuthError,
    GitHubClient,
    GitHubError,
    GitHubRateLimitError,
)
from utils.bootstrap import bootstrap
from utils.config import get_settings

bootstrap()
page_setup("GitHub Sync", "🐙")

st.title("GitHub Integration")
st.caption(
    "Import and synchronize public repository data from the official GitHub REST API. "
    "Tokens are never logged, shown in the UI, or committed."
)

settings = get_settings()

with session_scope() as session:
    profile = get_profile(session)

default_user = (profile.github_username if profile and profile.github_username else None) or (settings.github_username if settings.github_username != "your-github-username" else "")

col_sync1, col_sync2 = st.columns((2, 1))
with col_sync1:
    username = st.text_input("GitHub Username", value=default_user)
with col_sync2:
    st.write("Token status:")
    if settings.has_github_token:
        st.success("✅ GITHUB_TOKEN configured in local environment")
    else:
        st.info("ℹ️ No token (public API: up to 60 requests/hour)")

col_opt1, col_opt2 = st.columns(2)
fetch_readmes = col_opt1.checkbox("Fetch README contents for repositories", value=False)
allow_private = col_opt2.checkbox(
    "Sync private repositories (Requires configured token and explicit consent)",
    value=False,
    disabled=not settings.has_github_token,
)

if st.button("🚀 Sync Repositories Now", type="primary"):
    with st.spinner(f"Contacting GitHub REST API for '{username}'..."):
        try:
            client = GitHubClient()
            with session_scope() as session:
                res = client.sync_to_database(
                    session=session,
                    username=username,
                    include_private=allow_private,
                    fetch_readmes=fetch_readmes,
                )
            st.success(f"Successfully synced {res['synced']} repositories!")
            st.rerun()
        except GitHubRateLimitError as rle:
            st.error(str(rle))
        except GitHubAuthError as ae:
            st.error(str(ae))
        except GitHubError as ge:
            st.error(f"GitHub Error: {ge}")
        except Exception as ex:
            st.error(f"Sync failed: {ex}")

st.divider()

# Synced Repositories Display
with session_scope() as session:
    repos = list_github_repositories(session)

st.subheader(f"Synced Repositories ({len(repos)})")

if repos:
    rows = []
    for r in repos:
        topics = []
        if r.topics_json:
            try:
                topics = json.loads(r.topics_json)
            except Exception:
                topics = []
        rows.append(
            {
                "id": r.id,
                "name": r.name,
                "language": r.language or "—",
                "stars": r.stars,
                "forks": r.forks,
                "topics": ", ".join(topics),
                "is_private": "🔒 Private" if r.is_private else "🌐 Public",
                "pushed_at": r.pushed_at.strftime("%Y-%m-%d") if r.pushed_at else "—",
                "url": r.html_url,
            }
        )
    df_repos = pd.DataFrame(rows)
    st.dataframe(df_repos, use_container_width=True, hide_index=True)
    dataframe_download(df_repos, "github_repositories.csv", "Export Repositories CSV")

    # Convert repo to Project
    st.markdown("---")
    st.subheader("Import GitHub Repository as Portfolio Project")
    repo_map = {r.id: f"{r.name} ({r.language or 'No lang'})" for r in repos}
    selected_repo_id = st.selectbox(
        "Choose a repo to create a Project record:",
        list(repo_map.keys()),
        format_func=lambda i: repo_map[i],
    )
    selected_repo = next((r for r in repos if r.id == selected_repo_id), None)

    if selected_repo and st.button("Create Project from this Repo"):
        with session_scope() as session:
            existing_projects = list_projects(session, search=selected_repo.name)
            already_linked = any(p.github_url == selected_repo.html_url for p in existing_projects)

            if already_linked:
                st.warning("A project with this GitHub URL already exists in your portfolio.")
            else:
                topics = []
                if selected_repo.topics_json:
                    try:
                        topics = json.loads(selected_repo.topics_json)
                    except Exception:
                        pass
                skills = [selected_repo.language] if selected_repo.language else []
                skills.extend(topics)

                create_project(
                    session,
                    {
                        "title": selected_repo.name.replace("-", " ").replace("_", " ").title(),
                        "description": selected_repo.description or f"GitHub repository: {selected_repo.full_name}",
                        "github_url": selected_repo.html_url,
                        "status": "completed",
                        "is_public": not selected_repo.is_private,
                        "allow_duplicate": True,
                    },
                    skill_names=skills,
                )
                st.success(f"Created project '{selected_repo.name}' and linked technologies: {', '.join(skills)}.")
                st.rerun()

else:
    empty_state(
        "No repositories synced yet",
        "Click 'Sync Repositories Now' above to import your public repositories.",
    )
