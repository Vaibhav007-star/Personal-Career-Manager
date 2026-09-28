"""Create and update the single personal profile row."""

from __future__ import annotations

import streamlit as st

from components.layout import page_setup
from database.crud import get_profile, upsert_profile
from database.session import session_scope
from utils.bootstrap import bootstrap
from utils.validation import ValidationError

bootstrap()
page_setup("Profile", "👤")

st.title("Profile")
st.caption("One profile record. Email and phone stay local. Public portfolio export (later) excludes them unless you opt in.")

with session_scope() as session:
    profile = get_profile(session)
    initial = {
        "full_name": profile.full_name if profile else "",
        "headline": profile.headline or "" if profile else "",
        "email": profile.email or "" if profile else "",
        "phone": profile.phone or "" if profile else "",
        "location": profile.location or "" if profile else "",
        "linkedin_url": profile.linkedin_url or "" if profile else "",
        "github_username": profile.github_username or "" if profile else "vaibhav007-star",
        "github_url": profile.github_url or "" if profile else "https://github.com/vaibhav007-star",
        "portfolio_url": profile.portfolio_url or "" if profile else "",
        "summary": profile.summary or "" if profile else "",
        "target_roles": profile.target_roles or "" if profile else "Data Analyst intern, Data Scientist intern, AI/ML intern",
        "include_email_in_public_export": profile.include_email_in_public_export if profile else False,
        "is_sample": profile.is_sample if profile else False,
    }

if initial["is_sample"]:
    st.warning("This profile is marked as fictional sample data.")

with st.form("profile_form"):
    full_name = st.text_input("Full name *", value=initial["full_name"])
    headline = st.text_input("Headline", value=initial["headline"])
    c1, c2 = st.columns(2)
    with c1:
        email = st.text_input("Email (kept private by default)", value=initial["email"])
        location = st.text_input("Location", value=initial["location"])
        github_username = st.text_input("GitHub username", value=initial["github_username"])
        linkedin_url = st.text_input("LinkedIn URL", value=initial["linkedin_url"])
    with c2:
        phone = st.text_input("Phone (kept private)", value=initial["phone"])
        github_url = st.text_input("GitHub profile URL", value=initial["github_url"])
        portfolio_url = st.text_input("Portfolio URL", value=initial["portfolio_url"])
        include_email = st.checkbox(
            "Allow email on future public portfolio export",
            value=initial["include_email_in_public_export"],
        )
    target_roles = st.text_input("Target roles", value=initial["target_roles"])
    summary = st.text_area("Summary (write only what is true)", value=initial["summary"], height=140)
    st.caption("Do not invent achievements. Leave fields blank if you are unsure.")
    submitted = st.form_submit_button("Save profile", type="primary")

if submitted:
    try:
        with session_scope() as session:
            upsert_profile(
                session,
                {
                    "full_name": full_name,
                    "headline": headline,
                    "email": email,
                    "phone": phone,
                    "location": location,
                    "linkedin_url": linkedin_url,
                    "github_username": github_username,
                    "github_url": github_url,
                    "portfolio_url": portfolio_url,
                    "summary": summary,
                    "target_roles": target_roles,
                    "include_email_in_public_export": include_email,
                    "is_sample": False,
                },
            )
        st.success("Profile saved locally.")
        st.rerun()
    except ValidationError as exc:
        st.error(str(exc))

st.markdown("### Education and experience")
st.info("Education, skills catalog, certificates, and work history screens are Phase 2+. Tables already exist in SQLite.")
