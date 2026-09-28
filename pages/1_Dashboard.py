"""Overview cards, counts, and simple progress charts."""

from __future__ import annotations

import pandas as pd
import plotly.express as px
import streamlit as st

from components.layout import page_setup
from components.ui import empty_state
from database.crud import dashboard_counts, get_profile, projects_by_status, recent_activity
from database.session import session_scope
from utils.bootstrap import bootstrap

bootstrap()
page_setup("Dashboard", "📊")

st.title("Dashboard")
st.caption("Counts come only from your local database. Empty sections stay empty — nothing is invented.")

with session_scope() as session:
    profile = get_profile(session)
    counts = dashboard_counts(session)
    status_map = projects_by_status(session)
    activity = recent_activity(session, limit=10)
    skills_rows = []
    from database.crud import list_skills

    for skill in list_skills(session):
        skills_rows.append({"name": skill.name, "category": skill.category, "verified": skill.verified})

if profile is None:
    empty_state("No profile yet", "Open the Profile page and save your name. That is the only required field.")
else:
    if profile.is_sample:
        st.warning("Showing fictional sample data. Remove samples in Settings.")
    completeness_bits = [
        bool(profile.full_name),
        bool(profile.headline),
        bool(profile.email),
        bool(profile.summary),
        bool(profile.github_username),
        bool(profile.target_roles),
    ]
    pct = int(100 * sum(completeness_bits) / len(completeness_bits))
    st.progress(pct / 100, text=f"Profile completeness {pct}% (fields you filled, not a career score)")

m1, m2, m3, m4, m5, m6 = st.columns(6)
m1.metric("Projects", counts["projects"])
m2.metric("Skills", counts["skills"])
m3.metric("Certificates", counts["certificates"])
m4.metric("Education", counts["education"])
m5.metric("Experience", counts["experience"])
m6.metric("GitHub repos", counts["github_repos"])

m7, m8, m9, m10 = st.columns(4)
m7.metric("Applications", counts["applications"])
m8.metric("Interviews", counts["interviews"])
m9.metric("Open tasks", counts["tasks_open"])
m10.metric("Activity events", counts["activity"])

left, right = st.columns(2)
with left:
    st.subheader("Projects by status")
    if status_map:
        df = pd.DataFrame({"status": list(status_map.keys()), "count": list(status_map.values())})
        fig = px.bar(df, x="status", y="count", color="status")
        fig.update_layout(showlegend=False, margin=dict(l=10, r=10, t=10, b=10), height=280)
        st.plotly_chart(fig, use_container_width=True)
    else:
        empty_state("No projects", "Add a project to see this chart.")

with right:
    st.subheader("Skills by category")
    if skills_rows:
        sdf = pd.DataFrame(skills_rows)
        counts_df = sdf.groupby("category", as_index=False).size()
        fig = px.pie(counts_df, names="category", values="size", hole=0.45)
        fig.update_layout(margin=dict(l=10, r=10, t=10, b=10), height=280)
        st.plotly_chart(fig, use_container_width=True)
        verified = int(sdf["verified"].sum())
        st.caption(f"Verified skills: {verified} of {len(sdf)}. Unverified skills are never treated as confirmed.")
    else:
        empty_state("No skills", "Skills are created when you tag technologies on a project.")

st.subheader("Recent activity")
if not activity:
    st.caption("No activity yet.")
else:
    for item in activity:
        when = item.created_at.strftime("%Y-%m-%d %H:%M") if item.created_at else ""
        st.markdown(f"- `{when}` **{item.action}** `{item.entity_type}` — {item.details or '—'}")

st.info(
    "Internship tracker, GitHub statistics, certificates, and interviews will appear here in later phases. "
    "Zeros mean those tables are empty, not that data was imported."
)
