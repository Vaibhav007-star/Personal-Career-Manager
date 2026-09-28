"""Personal Career Management System — local Streamlit entrypoint."""

from __future__ import annotations

from database.crud import dashboard_counts, get_profile
from database.session import session_scope
from utils.bootstrap import bootstrap
from utils.config import get_settings

import streamlit as st

from components.layout import page_setup
from components.ui import empty_state

bootstrap()
page_setup("Home", "🎯")

settings = get_settings()

st.markdown(
    """
    <div class="pcm-hero">
      <h1>Personal Career Management System</h1>
      <p>Phase 1 — local SQLite, dashboard, profile, and projects. Bound to 127.0.0.1. No cloud uploads.</p>
    </div>
    """,
    unsafe_allow_html=True,
)

with session_scope() as session:
    profile = get_profile(session)
    counts = dashboard_counts(session)

name = profile.full_name if profile else "Add your profile to get started"
st.subheader(name)
if profile and profile.is_sample:
    st.warning(
        "A fictional sample profile is loaded. It is not real. Remove it in Settings before treating data as yours."
    )
if profile and profile.headline:
    st.caption(profile.headline)

c1, c2, c3, c4 = st.columns(4)
c1.metric("Projects", counts["projects"])
c2.metric("Skills", counts["skills"])
c3.metric("Applications", counts["applications"])
c4.metric("Open tasks", counts["tasks_open"])

st.markdown("### What you can do now")
col_a, col_b, col_c = st.columns(3)
with col_a:
    st.page_link("pages/1_Dashboard.py", label="Open dashboard", icon="📊")
with col_b:
    st.page_link("pages/2_Profile.py", label="Edit profile", icon="👤")
with col_c:
    st.page_link("pages/3_Projects.py", label="Manage projects", icon="📁")

st.markdown("### Coming in later phases (not implemented yet)")
st.markdown(
    "- GitHub REST importer for `vaibhav007-star` (public first; private only with a read-only token you opt into)\n"
    "- Document import (PDF/DOCX/CSV/XLSX/Markdown) with a review screen\n"
    "- Internship tracker, skill-gap analysis, resume/PDF generator, encrypted backups"
)

st.info(
    f"Server bind: `{settings.bind_host}:{settings.port}`. "
    "Local files are not encrypted in Phase 1. Anyone with access to this Windows account can read `data/career.db`."
)

if counts["projects"] == 0 and not profile:
    empty_state(
        "Empty workspace",
        "Use Profile to add your name, then add projects. Optional fictional samples can be loaded from Settings.",
    )
