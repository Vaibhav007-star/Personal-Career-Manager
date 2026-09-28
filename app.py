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
      <p>Local-first career & placement platform tailored for 6-month internship and placement prep in <b>Data Science, Data Analytics, and AI</b>.</p>
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
    st.info(
        "🧪 Demonstration sample profile loaded. Explore the dashboard, skills, and resume generator, or clear it in Settings."
    )
if profile and profile.headline:
    st.caption(profile.headline)

c1, c2, c3, c4 = st.columns(4)
c1.metric("Projects", counts["projects"])
c2.metric("Skills", counts["skills"])
c3.metric("Applications", counts["applications"])
c4.metric("Open Tasks", counts["tasks_open"])

st.markdown("### Quick Navigation")
r1_c1, r1_c2, r1_c3 = st.columns(3)
with r1_c1:
    st.page_link("pages/1_Dashboard.py", label="Comprehensive Dashboard", icon="📊")
    st.page_link("pages/2_Profile.py", label="Profile Management", icon="👤")
    st.page_link("pages/3_Projects.py", label="Project Portfolio", icon="📁")

with r1_c2:
    st.page_link("pages/4_Skills.py", label="Skills Catalog & Verification", icon="💡")
    st.page_link("pages/5_Education_Experience.py", label="Education & Credentials", icon="🎓")
    st.page_link("pages/6_GitHub_Sync.py", label="GitHub Repository Sync", icon="🐙")

with r1_c3:
    st.page_link("pages/7_Document_Import.py", label="Document Import Center", icon="📥")
    st.page_link("pages/8_Placement_Tracker.py", label="Placement & Skill-Gap", icon="🎯")
    st.page_link("pages/9_Resume_Portfolio.py", label="ATS Resume & Portfolio", icon="📄")

st.markdown("---")
st.page_link("pages/10_Settings.py", label="Security, Sample Data & Encrypted Backups", icon="⚙️")

st.info(
    f"🔒 Bound strictly to `{settings.bind_host}:{settings.port}`. "
    "All records and backups remain local. Use encrypted backups in Settings to protect your data."
)

if counts["projects"] == 0 and not profile:
    empty_state(
        "Empty workspace",
        "Use Profile to set up your profile, or load fictional sample data in Settings to explore.",
    )
