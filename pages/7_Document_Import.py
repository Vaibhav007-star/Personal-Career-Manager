"""Document Import Center with Automated Extraction and Staged Review."""

from __future__ import annotations

import streamlit as st

from components.layout import page_setup
from components.ui import empty_state
from database.crud import (
    create_application,
    create_certificate,
    create_education,
    create_experience,
    create_project,
    get_or_create_skill,
    upsert_profile,
)
from database.session import session_scope
from services.document_parser import DocumentParser, DocumentParserError
from utils.bootstrap import bootstrap
from utils.validation import ValidationError

bootstrap()
page_setup("Document Import", "📥")

st.title("Automated Document Import Center")
st.caption(
    "Import your existing Resume, CV, or spreadsheets (PDF, DOCX, CSV, XLSX, MD). "
    "The system automatically extracts your profile, skills, education, experience, and projects. "
    "You can auto-import everything in 1 click or review and adjust each section."
)

uploaded_file = st.file_uploader(
    "Upload your Resume (PDF/DOCX/MD) or Data Sheet (CSV/XLSX)",
    type=["pdf", "docx", "csv", "xlsx", "md", "txt"],
    help="Processed locally in-memory. Zero cloud uploads.",
)

if uploaded_file is not None:
    st.info(f"📁 Selected file: **{uploaded_file.name}** ({uploaded_file.size / 1024:.1f} KB)")
    if st.button("⚡ Parse & Extract Data Automatically", type="primary"):
        with st.spinner("Analyzing document structure and extracting career entities..."):
            try:
                parser = DocumentParser(uploaded_file.name, uploaded_file.getvalue())
                parsed = parser.parse()
                st.session_state["staged_import"] = parsed
                st.success("Extraction complete! Check the summary and review options below.")
            except DocumentParserError as dpe:
                st.error(f"Parser error: {dpe}")
            except Exception as ex:
                st.error(f"Failed to parse document: {ex}")

st.divider()

if "staged_import" in st.session_state:
    staged = st.session_state["staged_import"]
    st.subheader(f"Extracted Findings: `{staged.get('source_file')}`")

    # 1. Tabular Data (CSV / XLSX)
    if "tabular_data" in staged:
        tab_data = staged["tabular_data"]
        data_type = tab_data.get("type")
        records = tab_data.get("records", [])
        st.write(f"Detected format: **{data_type.title()}** ({len(records)} records)")
        st.dataframe(records, use_container_width=True)

        if st.button(f"📥 Save All {len(records)} {data_type} to Database", type="primary"):
            saved_count = 0
            with session_scope() as session:
                for r in records:
                    try:
                        if data_type == "applications":
                            create_application(
                                session,
                                {
                                    "company": str(r.get("company", "Unknown")),
                                    "role": str(r.get("role", "Unknown")),
                                    "status": str(r.get("status", "wishlist")),
                                    "deadline": r.get("deadline"),
                                    "application_url": r.get("application_url"),
                                    "notes": r.get("notes"),
                                },
                            )
                            saved_count += 1
                        elif data_type == "skills":
                            get_or_create_skill(
                                session,
                                name=str(r.get("name") or r.get("skill")),
                                category=str(r.get("category", "technical")),
                                proficiency=str(r.get("proficiency", "intermediate")),
                                verified=bool(r.get("verified", False)),
                            )
                            saved_count += 1
                        elif data_type == "certificates":
                            create_certificate(
                                session,
                                {
                                    "name": str(r.get("name") or r.get("certificate")),
                                    "issuer": str(r.get("issuer", "Unknown")),
                                    "verification_status": "unverified",
                                },
                            )
                            saved_count += 1
                    except Exception as err:
                        st.warning(f"Could not import row: {err}")
            st.success(f"Successfully saved {saved_count} records to database!")
            del st.session_state["staged_import"]
            st.rerun()

    # 2. Text / Resume Data
    else:
        prof = staged.get("profile", {})
        skills = staged.get("skills", [])
        edu_items = staged.get("education", [])
        exp_items = staged.get("experience", [])
        proj_items = staged.get("projects", [])
        cert_items = staged.get("certificates", [])

        # 1-CLICK AUTO IMPORT ALL BUTTON
        st.markdown(
            """
            <div style="background-color: #EBF8FF; border-left: 4px solid #3182CE; padding: 12px; border-radius: 4px; margin-bottom: 16px;">
                <h4 style="margin: 0; color: #2B6CB0;">🚀 1-Click Fast Track</h4>
                <p style="margin: 4px 0 0 0; color: #4A5568;">Save all detected information (Profile, Skills, Education, Experience, Projects) directly into your database in one go.</p>
            </div>
            """,
            unsafe_allow_html=True,
        )

        col_fast1, col_fast2 = st.columns((2, 1))
        if col_fast1.button("⚡ Save ALL Extracted Data to Database Now", type="primary"):
            imported_summary = []
            with session_scope() as session:
                # 1. Profile
                if prof.get("full_name"):
                    try:
                        upsert_profile(
                            session,
                            {
                                "full_name": prof["full_name"],
                                "email": prof.get("email"),
                                "phone": prof.get("phone"),
                                "github_username": prof.get("github_username"),
                                "github_url": prof.get("github_url"),
                                "linkedin_url": prof.get("linkedin_url"),
                            },
                        )
                        imported_summary.append("Profile")
                    except Exception:
                        pass

                # 2. Skills
                s_count = 0
                for s in skills:
                    get_or_create_skill(
                        session,
                        name=s["name"],
                        category=s["category"],
                        proficiency="intermediate",
                        verified=False,
                        source="resume_import",
                    )
                    s_count += 1
                if s_count:
                    imported_summary.append(f"{s_count} Skills")

                # 3. Education
                e_count = 0
                for e in edu_items:
                    try:
                        create_education(
                            session,
                            {
                                "institution": e.get("institution") or "University",
                                "degree": e.get("degree") or "Degree",
                                "currently_enrolled": True,
                            },
                        )
                        e_count += 1
                    except Exception:
                        pass
                if e_count:
                    imported_summary.append(f"{e_count} Education")

                # 4. Experience
                x_count = 0
                for x in exp_items:
                    try:
                        create_experience(
                            session,
                            {
                                "title": x.get("title") or "Role",
                                "organization": x.get("organization") or "Organization",
                                "experience_type": x.get("experience_type", "internship"),
                                "currently_working": False,
                            },
                        )
                        x_count += 1
                    except Exception:
                        pass
                if x_count:
                    imported_summary.append(f"{x_count} Experience")

                # 5. Projects
                p_count = 0
                for p in proj_items:
                    try:
                        create_project(
                            session,
                            {
                                "title": p.get("title") or "Project",
                                "description": "Imported from resume extraction.",
                                "status": "completed",
                                "allow_duplicate": True,
                            },
                        )
                        p_count += 1
                    except Exception:
                        pass
                if p_count:
                    imported_summary.append(f"{p_count} Projects")

            st.success(f"🎉 Auto-Import complete! Imported: {', '.join(imported_summary)}.")
            del st.session_state["staged_import"]
            st.rerun()

        if col_fast2.button("Discard Staged Data"):
            del st.session_state["staged_import"]
            st.rerun()

        st.markdown("---")
        st.subheader("Fine-Grained Review (Optional)")

        # Section 1: Profile
        with st.expander("👤 Candidate Profile", expanded=True):
            p1, p2 = st.columns(2)
            p_name = p1.text_input("Full Name", value=prof.get("full_name") or "")
            p_email = p2.text_input("Email", value=prof.get("email") or "")
            p_phone = p1.text_input("Phone", value=prof.get("phone") or "")
            p_github = p2.text_input("GitHub Username", value=prof.get("github_username") or "")
            if st.button("Apply Only Profile"):
                try:
                    with session_scope() as session:
                        upsert_profile(
                            session,
                            {
                                "full_name": p_name or "User",
                                "email": p_email or None,
                                "phone": p_phone or None,
                                "github_username": p_github or None,
                            },
                        )
                    st.success("Profile saved.")
                except ValidationError as ve:
                    st.error(str(ve))

        # Section 2: Skills
        with st.expander(f"💡 Detected Skills ({len(skills)})", expanded=True):
            selected_skills = []
            s_cols = st.columns(3)
            for idx, s in enumerate(skills):
                col = s_cols[idx % 3]
                chk = col.checkbox(f"{s['name']} ({s['category']})", value=True, key=f"rev_s_{idx}")
                if chk:
                    selected_skills.append(s)

            if st.button(f"Save {len(selected_skills)} Selected Skills"):
                with session_scope() as session:
                    for s in selected_skills:
                        get_or_create_skill(
                            session,
                            name=s["name"],
                            category=s["category"],
                            proficiency="intermediate",
                            verified=False,
                            source="resume_import",
                        )
                st.success(f"Added {len(selected_skills)} skills to catalog.")

        # Section 3: Education
        if edu_items:
            with st.expander(f"🎓 Detected Education ({len(edu_items)})"):
                for e in edu_items:
                    st.markdown(f"- **{e.get('degree')}** — *{e.get('institution')}*")

        # Section 4: Experience
        if exp_items:
            with st.expander(f"💼 Detected Experience ({len(exp_items)})"):
                for x in exp_items:
                    st.markdown(f"- **{x.get('title')}**")

        # Section 5: Projects
        if proj_items:
            with st.expander(f"📁 Detected Projects ({len(proj_items)})"):
                for pr in proj_items:
                    st.markdown(f"- **{pr.get('title')}**")

else:
    empty_state(
        "No document currently uploaded",
        "Upload your resume or spreadsheet above and click 'Parse & Extract Data Automatically'.",
    )
