"""Resume & Portfolio Generator Page."""

from __future__ import annotations

import streamlit as st

from components.layout import page_setup
from components.ui import empty_state
from database.crud import (
    get_profile,
    list_certificates,
    list_education,
    list_experience,
    list_projects,
    list_skills,
)
from database.session import session_scope
from services.resume_generator import ResumeGenerator, ROLE_TARGETS
from utils.bootstrap import bootstrap

bootstrap()
page_setup("Resume & Portfolio", "📄")

st.title("Resume & Portfolio Generator")
st.caption(
    "Generate ATS-compliant DOCX and PDF resumes tailored for 6-month internships in Data Science, "
    "Data Analytics, and AI. All outputs come strictly from verified database records."
)

with session_scope() as session:
    profile = get_profile(session)
    all_projects = list_projects(session)
    all_skills = list_skills(session)
    education = list_education(session)
    experience = list_experience(session)
    certificates = list_certificates(session)

if not profile:
    empty_state("Profile missing", "Please fill in your name in the Profile page first.")
    st.stop()

# Configuration columns
c1, c2 = st.columns((2, 3))

with c1:
    st.subheader("1. Target Role & Profile")
    target_role = st.selectbox("Internship Target Track", list(ROLE_TARGETS.keys()))
    st.info(f"💡 Strategy: {ROLE_TARGETS[target_role]['summary_focus']}")

    st.subheader("2. Project Selection")
    if all_projects:
        proj_names = {p.id: p.title for p in all_projects}
        selected_proj_ids = st.multiselect(
            "Select Projects to include",
            options=list(proj_names.keys()),
            default=list(proj_names.keys())[:3],
            format_func=lambda i: proj_names[i],
        )
        selected_projects = [p for p in all_projects if p.id in selected_proj_ids]
    else:
        st.warning("No projects in database.")
        selected_projects = []

    st.subheader("3. Skill Selection")
    if all_skills:
        skill_opts = {s.id: s.name for s in all_skills}
        preferred_names = set(ROLE_TARGETS[target_role]["preferred_skills"])
        default_skill_ids = [s.id for s in all_skills if s.name in preferred_names or s.verified]
        if not default_skill_ids:
            default_skill_ids = [s.id for s in all_skills[:8]]

        selected_skill_ids = st.multiselect(
            "Select Skills to feature",
            options=list(skill_opts.keys()),
            default=default_skill_ids,
            format_func=lambda i: skill_opts[i],
        )
        selected_skills = [s for s in all_skills if s.id in selected_skill_ids]
    else:
        st.warning("No skills in database.")
        selected_skills = []

with c2:
    st.subheader("4. Resume Export")
    generator = ResumeGenerator(
        profile=profile,
        skills=selected_skills,
        projects=selected_projects,
        education=education,
        experience=experience,
        certificates=certificates,
        role_type=target_role,
    )

    tab_docx, tab_pdf, tab_port = st.tabs(["📝 Word (.docx)", "📑 PDF (.pdf)", "🌐 Public Portfolio"])

    with tab_docx:
        st.markdown("##### Download Editable ATS-Friendly DOCX")
        st.caption("Standard single-column, ATS-parsed structure without fragile tables or text boxes.")
        try:
            docx_bytes = generator.generate_docx()
            st.download_button(
                label=f"⬇️ Download {target_role.replace('/', '_')} Resume (DOCX)",
                data=docx_bytes,
                file_name=f"{profile.full_name.replace(' ', '_')}_{target_role.replace('/', '_')}_Resume.docx",
                mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                type="primary",
            )
        except Exception as e:
            st.error(f"Error generating DOCX: {e}")

    with tab_pdf:
        st.markdown("##### Download Clean ATS-Friendly PDF")
        st.caption("Directly formatted via ReportLab according to ATS layout rules.")
        try:
            pdf_bytes = generator.generate_pdf()
            st.download_button(
                label=f"⬇️ Download {target_role.replace('/', '_')} Resume (PDF)",
                data=pdf_bytes,
                file_name=f"{profile.full_name.replace(' ', '_')}_{target_role.replace('/', '_')}_Resume.pdf",
                mime="application/pdf",
                type="primary",
            )
        except Exception as e:
            st.error(f"Error generating PDF: {e}")

    with tab_port:
        st.markdown("##### Public Portfolio Export (Markdown)")
        st.caption("Excludes phone numbers, unapproved projects, and unverified credentials.")
        md_text = generator.generate_public_portfolio_markdown()
        st.download_button(
            label="⬇️ Download Public Portfolio (Markdown)",
            data=md_text.encode("utf-8"),
            file_name="public_portfolio.md",
            mime="text/markdown",
        )
        with st.expander("Preview Public Portfolio"):
            st.markdown(md_text)

st.divider()

# Live Resume Outline Preview
st.subheader("Live Document Outline Preview")
with st.container():
    st.markdown(f"**Name:** {profile.full_name} | **Email:** {profile.email or '—'} | **GitHub:** {profile.github_url or '—'}")
    st.markdown(f"**Target Role:** {target_role}")
    st.markdown(f"**Selected Projects ({len(selected_projects)}):** " + (", ".join(p.title for p in selected_projects) or "None"))
    st.markdown(f"**Selected Skills ({len(selected_skills)}):** " + (", ".join(s.name for s in selected_skills) or "None"))
