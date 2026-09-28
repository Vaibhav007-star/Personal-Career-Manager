"""Education, Experience, and Certificates CRUD."""

from __future__ import annotations

from datetime import date
import pandas as pd
import streamlit as st

from components.layout import page_setup
from components.ui import dataframe_download, empty_state
from database.crud import (
    create_certificate,
    create_education,
    create_experience,
    delete_certificate,
    delete_education,
    delete_experience,
    get_certificate,
    get_education,
    get_experience,
    list_certificates,
    list_education,
    list_experience,
    update_certificate,
    update_education,
    update_experience,
)
from database.session import session_scope
from utils.bootstrap import bootstrap
from utils.validation import ValidationError

bootstrap()
page_setup("Credentials & Experience", "🎓")

st.title("Education, Experience & Certificates")
st.caption("Keep your academic, professional, and certification history up to date.")

tab_edu, tab_exp, tab_cert = st.tabs(["🎓 Education", "💼 Experience", "📜 Certificates"])

# ==============================================================================
# 1. EDUCATION TAB
# ==============================================================================
with tab_edu:
    st.subheader("Academic Records")
    with session_scope() as session:
        edu_list = list_education(session)

    if edu_list:
        rows = [
            {
                "id": e.id,
                "institution": e.institution,
                "degree": e.degree or "—",
                "field_of_study": e.field_of_study or "—",
                "start": str(e.start_date) if e.start_date else "—",
                "end": "Present" if e.currently_enrolled else (str(e.end_date) if e.end_date else "—"),
                "grade": e.grade or "—",
            }
            for e in edu_list
        ]
        df_edu = pd.DataFrame(rows)
        st.dataframe(df_edu, use_container_width=True, hide_index=True)
        dataframe_download(df_edu, "education.csv", "Export Education CSV")
    else:
        empty_state("No education records", "Add your university or college education below.")

    st.markdown("---")
    st.subheader("Add or Edit Education")
    edu_mode = st.radio("Education Action", ["Add Education", "Edit Education"], horizontal=True, key="edu_mode")

    if edu_mode == "Add Education":
        with st.form("add_edu_form"):
            inst = st.text_input("Institution * (e.g. University / College name)")
            c1, c2 = st.columns(2)
            deg = c1.text_input("Degree (e.g. B.Tech, B.Sc, BCA)")
            fos = c2.text_input("Field of Study (e.g. Computer Science, Statistics)")
            
            c3, c4 = st.columns(2)
            start_d = c3.date_input("Start date", value=date(2022, 8, 1))
            current = c4.checkbox("Currently enrolled")
            end_d = c4.date_input("End date (or expected graduation)", value=date(2026, 6, 1), disabled=current)
            
            grade = st.text_input("Grade / CGPA / Percentage (optional)")
            desc = st.text_area("Key Coursework or Highlights (optional)")
            save_edu = st.form_submit_button("Save Education", type="primary")

            if save_edu:
                try:
                    with session_scope() as session:
                        create_education(
                            session,
                            {
                                "institution": inst,
                                "degree": deg,
                                "field_of_study": fos,
                                "start_date": start_d,
                                "end_date": None if current else end_d,
                                "currently_enrolled": current,
                                "grade": grade,
                                "description": desc,
                            },
                        )
                    st.success("Education record saved.")
                    st.rerun()
                except ValidationError as exc:
                    st.error(str(exc))

    else:
        if not edu_list:
            st.info("No education records to edit.")
        else:
            edu_map = {e.id: f"{e.institution} ({e.degree or 'Degree'})" for e in edu_list}
            sel_edu_id = st.selectbox("Select record to edit", list(edu_map.keys()), format_func=lambda i: edu_map[i])
            with session_scope() as session:
                curr_edu = get_education(session, sel_edu_id)

            if curr_edu:
                with st.form("edit_edu_form"):
                    e_inst = st.text_input("Institution *", value=curr_edu.institution)
                    ec1, ec2 = st.columns(2)
                    e_deg = ec1.text_input("Degree", value=curr_edu.degree or "")
                    e_fos = ec2.text_input("Field of Study", value=curr_edu.field_of_study or "")
                    ec3, ec4 = st.columns(2)
                    e_start = ec3.date_input("Start date", value=curr_edu.start_date or date.today())
                    e_curr = ec4.checkbox("Currently enrolled", value=curr_edu.currently_enrolled)
                    e_end = ec4.date_input("End date", value=curr_edu.end_date or date.today(), disabled=e_curr)
                    e_grade = st.text_input("Grade", value=curr_edu.grade or "")
                    e_desc = st.text_area("Description", value=curr_edu.description or "")
                    
                    update_btn = st.form_submit_button("Update Education", type="primary")
                    if update_btn:
                        try:
                            with session_scope() as session:
                                update_education(
                                    session,
                                    sel_edu_id,
                                    {
                                        "institution": e_inst,
                                        "degree": e_deg,
                                        "field_of_study": e_fos,
                                        "start_date": e_start,
                                        "end_date": None if e_curr else e_end,
                                        "currently_enrolled": e_curr,
                                        "grade": e_grade,
                                        "description": e_desc,
                                    },
                                )
                            st.success("Record updated.")
                            st.rerun()
                        except ValidationError as exc:
                            st.error(str(exc))

                if st.button("Delete this education record", type="secondary"):
                    with session_scope() as session:
                        delete_education(session, sel_edu_id)
                    st.success("Record deleted.")
                    st.rerun()

# ==============================================================================
# 2. EXPERIENCE TAB
# ==============================================================================
with tab_exp:
    st.subheader("Work & Internship Experience")
    with session_scope() as session:
        exp_list = list_experience(session)

    if exp_list:
        rows = [
            {
                "id": x.id,
                "title": x.title,
                "organization": x.organization,
                "type": x.experience_type,
                "location": x.location or "—",
                "start": str(x.start_date) if x.start_date else "—",
                "end": "Present" if x.currently_working else (str(x.end_date) if x.end_date else "—"),
            }
            for x in exp_list
        ]
        df_exp = pd.DataFrame(rows)
        st.dataframe(df_exp, use_container_width=True, hide_index=True)
        dataframe_download(df_exp, "experience.csv", "Export Experience CSV")
    else:
        empty_state("No experience records", "Add internships, volunteer work, or research assistantships below.")

    st.markdown("---")
    st.subheader("Add or Edit Experience")
    exp_mode = st.radio("Experience Action", ["Add Experience", "Edit Experience"], horizontal=True, key="exp_mode")

    if exp_mode == "Add Experience":
        with st.form("add_exp_form"):
            c1, c2 = st.columns(2)
            title = c1.text_input("Role / Job Title * (e.g. Data Analyst Intern)")
            org = c2.text_input("Organization / Company *")
            c3, c4 = st.columns(2)
            exp_type = c3.selectbox("Type", ["internship", "part_time", "full_time", "volunteer", "research"])
            loc = c4.text_input("Location (e.g. Remote, City)")
            c5, c6 = st.columns(2)
            start_x = c5.date_input("Start date", value=date.today())
            working = c6.checkbox("Currently working here")
            end_x = c6.date_input("End date", value=date.today(), disabled=working)
            desc_x = st.text_area("Responsibilities & Impact (factual, verified achievements only)", height=120)
            save_exp = st.form_submit_button("Save Experience", type="primary")

            if save_exp:
                try:
                    with session_scope() as session:
                        create_experience(
                            session,
                            {
                                "title": title,
                                "organization": org,
                                "experience_type": exp_type,
                                "location": loc,
                                "start_date": start_x,
                                "end_date": None if working else end_x,
                                "currently_working": working,
                                "description": desc_x,
                            },
                        )
                    st.success("Experience added.")
                    st.rerun()
                except ValidationError as exc:
                    st.error(str(exc))

    else:
        if not exp_list:
            st.info("No experience records to edit.")
        else:
            exp_map = {x.id: f"{x.title} at {x.organization}" for x in exp_list}
            sel_exp_id = st.selectbox("Select experience to edit", list(exp_map.keys()), format_func=lambda i: exp_map[i])
            with session_scope() as session:
                curr_exp = get_experience(session, sel_exp_id)

            if curr_exp:
                with st.form("edit_exp_form"):
                    ec1, ec2 = st.columns(2)
                    e_title = ec1.text_input("Role / Job Title *", value=curr_exp.title)
                    e_org = ec2.text_input("Organization *", value=curr_exp.organization)
                    ec3, ec4 = st.columns(2)
                    types = ["internship", "part_time", "full_time", "volunteer", "research"]
                    t_idx = types.index(curr_exp.experience_type) if curr_exp.experience_type in types else 0
                    e_type = ec3.selectbox("Type", types, index=t_idx)
                    e_loc = ec4.text_input("Location", value=curr_exp.location or "")
                    ec5, ec6 = st.columns(2)
                    e_start = ec5.date_input("Start date", value=curr_exp.start_date or date.today())
                    e_work = ec6.checkbox("Currently working here", value=curr_exp.currently_working)
                    e_end = ec6.date_input("End date", value=curr_exp.end_date or date.today(), disabled=e_work)
                    e_desc = st.text_area("Responsibilities & Impact", value=curr_exp.description or "", height=120)
                    
                    update_exp_btn = st.form_submit_button("Update Experience", type="primary")
                    if update_exp_btn:
                        try:
                            with session_scope() as session:
                                update_experience(
                                    session,
                                    sel_exp_id,
                                    {
                                        "title": e_title,
                                        "organization": e_org,
                                        "experience_type": e_type,
                                        "location": e_loc,
                                        "start_date": e_start,
                                        "end_date": None if e_work else e_end,
                                        "currently_working": e_work,
                                        "description": e_desc,
                                    },
                                )
                            st.success("Experience updated.")
                            st.rerun()
                        except ValidationError as exc:
                            st.error(str(exc))

                if st.button("Delete this experience record", type="secondary"):
                    with session_scope() as session:
                        delete_experience(session, sel_exp_id)
                    st.success("Experience record deleted.")
                    st.rerun()

# ==============================================================================
# 3. CERTIFICATES TAB
# ==============================================================================
with tab_cert:
    st.subheader("Certifications & Badges")
    with session_scope() as session:
        cert_list = list_certificates(session)

    if cert_list:
        rows = [
            {
                "id": c.id,
                "name": c.name,
                "issuer": c.issuer or "—",
                "issued": str(c.issue_date) if c.issue_date else "—",
                "status": c.verification_status,
                "credential_url": c.credential_url or "—",
            }
            for c in cert_list
        ]
        df_cert = pd.DataFrame(rows)
        st.dataframe(df_cert, use_container_width=True, hide_index=True)
        dataframe_download(df_cert, "certificates.csv", "Export Certificates CSV")
    else:
        empty_state("No certificates", "Add course certificates or professional credentials below.")

    st.markdown("---")
    st.subheader("Add or Edit Certificate")
    cert_mode = st.radio("Certificate Action", ["Add Certificate", "Edit Certificate"], horizontal=True, key="cert_mode")

    if cert_mode == "Add Certificate":
        with st.form("add_cert_form"):
            name = st.text_input("Certificate Name * (e.g. Google Data Analytics Professional Certificate)")
            c1, c2 = st.columns(2)
            issuer = c1.text_input("Issuer (e.g. Coursera, Google, DeepLearning.AI, AWS)")
            cred_id = c2.text_input("Credential ID (optional)")
            c3, c4 = st.columns(2)
            issue_d = c3.date_input("Issue date", value=date.today())
            has_exp = c4.checkbox("Has expiry date")
            exp_d = c4.date_input("Expiry date", value=date.today(), disabled=not has_exp)
            cred_url = st.text_input("Credential Verification URL")
            status = st.selectbox("Status", ["verified", "unverified", "in_progress"])
            notes = st.text_area("Notes")
            save_cert = st.form_submit_button("Save Certificate", type="primary")

            if save_cert:
                try:
                    with session_scope() as session:
                        create_certificate(
                            session,
                            {
                                "name": name,
                                "issuer": issuer,
                                "credential_id": cred_id,
                                "issue_date": issue_d,
                                "expiry_date": exp_d if has_exp else None,
                                "credential_url": cred_url,
                                "verification_status": status,
                                "notes": notes,
                            },
                        )
                    st.success("Certificate saved.")
                    st.rerun()
                except ValidationError as exc:
                    st.error(str(exc))

    else:
        if not cert_list:
            st.info("No certificates to edit.")
        else:
            cert_map = {c.id: f"{c.name} ({c.issuer or 'Issuer'})" for c in cert_list}
            sel_cert_id = st.selectbox("Select certificate to edit", list(cert_map.keys()), format_func=lambda i: cert_map[i])
            with session_scope() as session:
                curr_cert = get_certificate(session, sel_cert_id)

            if curr_cert:
                with st.form("edit_cert_form"):
                    c_name = st.text_input("Certificate Name *", value=curr_cert.name)
                    cc1, cc2 = st.columns(2)
                    c_issuer = cc1.text_input("Issuer", value=curr_cert.issuer or "")
                    c_cred_id = cc2.text_input("Credential ID", value=curr_cert.credential_id or "")
                    cc3, cc4 = st.columns(2)
                    c_issue_d = cc3.date_input("Issue date", value=curr_cert.issue_date or date.today())
                    c_has_exp = cc4.checkbox("Has expiry date", value=bool(curr_cert.expiry_date))
                    c_exp_d = cc4.date_input("Expiry date", value=curr_cert.expiry_date or date.today(), disabled=not c_has_exp)
                    c_cred_url = st.text_input("Credential URL", value=curr_cert.credential_url or "")
                    statuses = ["verified", "unverified", "in_progress"]
                    s_idx = statuses.index(curr_cert.verification_status) if curr_cert.verification_status in statuses else 1
                    c_status = st.selectbox("Status", statuses, index=s_idx)
                    c_notes = st.text_area("Notes", value=curr_cert.notes or "")
                    
                    update_cert_btn = st.form_submit_button("Update Certificate", type="primary")
                    if update_cert_btn:
                        try:
                            with session_scope() as session:
                                update_certificate(
                                    session,
                                    sel_cert_id,
                                    {
                                        "name": c_name,
                                        "issuer": c_issuer,
                                        "credential_id": c_cred_id,
                                        "issue_date": c_issue_d,
                                        "expiry_date": c_exp_d if c_has_exp else None,
                                        "credential_url": c_cred_url,
                                        "verification_status": c_status,
                                        "notes": c_notes,
                                    },
                                )
                            st.success("Certificate updated.")
                            st.rerun()
                        except ValidationError as exc:
                            st.error(str(exc))

                if st.button("Delete this certificate", type="secondary"):
                    with session_scope() as session:
                        delete_certificate(session, sel_cert_id)
                    st.success("Certificate deleted.")
                    st.rerun()
