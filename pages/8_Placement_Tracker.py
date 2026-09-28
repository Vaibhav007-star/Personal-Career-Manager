"""Internship & Placement Tracker with Skill-Gap Analysis Engine."""

from __future__ import annotations

from datetime import date, datetime
import pandas as pd
import plotly.express as px
import streamlit as st

from components.layout import page_setup
from components.ui import dataframe_download, empty_state
from database.crud import (
    create_application,
    create_interview,
    create_task,
    delete_application,
    delete_interview,
    delete_task,
    get_application,
    list_applications,
    list_skills,
    list_tasks,
    set_application_required_skills,
    update_application,
    update_interview,
    update_task,
)
from database.session import session_scope
from utils.bootstrap import bootstrap
from utils.validation import ValidationError

bootstrap()
page_setup("Placement Tracker", "🎯")

st.title("Internship & Placement Tracker")
st.caption(
    "Track 6-month internship applications for Data Science, Data Analytics, and AI. "
    "Features verified skill-gap analysis, interview schedule tracking, and follow-up deadlines."
)

tab_pipe, tab_gap, tab_interview, tab_tasks = st.tabs(
    ["📌 Applications Pipeline", "🔍 Skill-Gap Analysis", "🗓️ Interview Rounds", "⏰ Tasks & Reminders"]
)

with session_scope() as session:
    all_apps = list_applications(session)
    all_user_skills = list_skills(session)

# ==============================================================================
# 1. APPLICATIONS PIPELINE TAB
# ==============================================================================
with tab_pipe:
    m1, m2, m3, m4, m5, m6 = st.columns(6)
    c_wish = sum(1 for a in all_apps if a.status == "wishlist")
    c_appl = sum(1 for a in all_apps if a.status == "applied")
    c_oa = sum(1 for a in all_apps if a.status == "oa")
    c_int = sum(1 for a in all_apps if a.status == "interview")
    c_off = sum(1 for a in all_apps if a.status == "offer")
    c_rej = sum(1 for a in all_apps if a.status == "rejected")

    m1.metric("Wishlist", c_wish)
    m2.metric("Applied", c_appl)
    m3.metric("OA / Test", c_oa)
    m4.metric("Interview", c_int)
    m5.metric("Offers", c_off)
    m6.metric("Rejected", c_rej)

    st.divider()

    fc1, fc2 = st.columns((3, 2))
    search_app = fc1.text_input("Search company or role")
    filter_status = fc2.selectbox("Filter by Status", ["all", "wishlist", "applied", "oa", "interview", "offer", "rejected"])

    with session_scope() as session:
        filtered_apps = list_applications(
            session,
            status=filter_status if filter_status != "all" else None,
            search=search_app or None,
        )

    if filtered_apps:
        rows = [
            {
                "id": a.id,
                "company": a.company,
                "role": a.role,
                "status": a.status.upper(),
                "applied_date": str(a.applied_date) if a.applied_date else "—",
                "deadline": str(a.deadline) if a.deadline else "—",
                "follow_up": str(a.follow_up_date) if a.follow_up_date else "—",
                "rounds": len(a.interviews),
            }
            for a in filtered_apps
        ]
        df_apps = pd.DataFrame(rows)
        st.dataframe(df_apps, use_container_width=True, hide_index=True)
        dataframe_download(df_apps, "applications.csv", "Export Applications CSV")
    else:
        empty_state("No applications found", "Create an application record below.")

    st.markdown("---")
    st.subheader("Add or Edit Application")
    app_mode = st.radio("Mode", ["Create New Application", "Edit Application"], horizontal=True, key="app_mode")

    if app_mode == "Create New Application":
        with st.form("new_app_form"):
            c1, c2 = st.columns(2)
            comp = c1.text_input("Company * (e.g. Google, Microsoft, Startup)")
            role = c2.text_input("Role * (e.g. Data Science Intern, Data Analyst Intern)")
            c3, c4 = st.columns(2)
            app_url = c3.text_input("Job Posting URL")
            source = c4.text_input("Source (e.g. LinkedIn, Career Page, Referral)")
            c5, c6, c7 = st.columns(3)
            status = c5.selectbox("Status", ["wishlist", "applied", "oa", "interview", "offer", "rejected"])
            applied_d = c6.date_input("Applied Date", value=None)
            deadline_d = c7.date_input("Deadline", value=None)
            
            c8, c9 = st.columns(2)
            follow_up = c8.date_input("Follow-up Date", value=None)
            req_skills = c9.text_input("Required Skills (comma-separated, e.g. Python, SQL, Pandas, Tableau)")

            raw_jd = st.text_area("Job Description (for skill-gap analysis)", height=120)
            notes = st.text_area("Personal Notes / Referral Contact", height=80)
            save_app = st.form_submit_button("Save Application", type="primary")

            if save_app:
                try:
                    with session_scope() as session:
                        new_app = create_application(
                            session,
                            {
                                "company": comp,
                                "role": role,
                                "application_url": app_url,
                                "source": source,
                                "status": status,
                                "applied_date": applied_d,
                                "deadline": deadline_d,
                                "follow_up_date": follow_up,
                                "notes": notes,
                                "raw_job_description": raw_jd,
                            },
                        )
                        if req_skills:
                            skills_list = [s.strip() for s in req_skills.split(",") if s.strip()]
                            set_application_required_skills(session, new_app.id, skills_list)

                    st.success("Application created.")
                    st.rerun()
                except ValidationError as exc:
                    st.error(str(exc))

    else:
        if not all_apps:
            st.info("No applications to edit.")
        else:
            app_map = {a.id: f"{a.company} — {a.role}" for a in all_apps}
            sel_app_id = st.selectbox("Select application to edit", list(app_map.keys()), format_func=lambda i: app_map[i])
            with session_scope() as session:
                curr_app = get_application(session, sel_app_id)

            if curr_app:
                with st.form("edit_app_form"):
                    ec1, ec2 = st.columns(2)
                    e_comp = ec1.text_input("Company *", value=curr_app.company)
                    e_role = ec2.text_input("Role *", value=curr_app.role)
                    ec3, ec4 = st.columns(2)
                    e_url = ec3.text_input("Job Posting URL", value=curr_app.application_url or "")
                    e_source = ec4.text_input("Source", value=curr_app.source or "")
                    ec5, ec6, ec7 = st.columns(3)
                    statuses = ["wishlist", "applied", "oa", "interview", "offer", "rejected"]
                    s_idx = statuses.index(curr_app.status) if curr_app.status in statuses else 0
                    e_status = ec5.selectbox("Status", statuses, index=s_idx)
                    e_app_d = ec6.date_input("Applied Date", value=curr_app.applied_date)
                    e_dead_d = ec7.date_input("Deadline", value=curr_app.deadline)
                    
                    ec8, ec9 = st.columns(2)
                    e_foll = ec8.date_input("Follow-up Date", value=curr_app.follow_up_date)
                    current_reqs = ", ".join(r.skill_name for r in curr_app.required_skills)
                    e_skills = ec9.text_input("Required Skills (comma-separated)", value=current_reqs)

                    existing_jd = curr_app.job_description.raw_text if curr_app.job_description else ""
                    e_jd = st.text_area("Job Description", value=existing_jd, height=120)
                    e_notes = st.text_area("Personal Notes", value=curr_app.notes or "", height=80)
                    
                    update_app_btn = st.form_submit_button("Update Application", type="primary")

                    if update_app_btn:
                        try:
                            with session_scope() as session:
                                update_application(
                                    session,
                                    sel_app_id,
                                    {
                                        "company": e_comp,
                                        "role": e_role,
                                        "application_url": e_url,
                                        "source": e_source,
                                        "status": e_status,
                                        "applied_date": e_app_d,
                                        "deadline": e_dead_d,
                                        "follow_up_date": e_foll,
                                        "notes": e_notes,
                                        "raw_job_description": e_jd,
                                    },
                                )
                                if e_skills != current_reqs:
                                    s_list = [s.strip() for s in e_skills.split(",") if s.strip()]
                                    set_application_required_skills(session, sel_app_id, s_list)

                            st.success("Application updated.")
                            st.rerun()
                        except ValidationError as exc:
                            st.error(str(exc))

                if st.button("Delete this application", type="secondary"):
                    with session_scope() as session:
                        delete_application(session, sel_app_id)
                    st.success("Application deleted.")
                    st.rerun()

# ==============================================================================
# 2. SKILL-GAP ANALYSIS ENGINE TAB
# ==============================================================================
with tab_gap:
    st.subheader("Verified Skill-Gap Analysis")
    st.caption(
        "Compares required job skills with your database. "
        "Verified skills count toward your readiness score; unverified skills are flagged."
    )

    with session_scope() as session:
        user_skills_dict = {s.name.lower(): s for s in list_skills(session)}
        apps_with_reqs = [a for a in list_applications(session) if a.required_skills or (a.job_description and a.job_description.raw_text)]

    analysis_mode = st.radio("Analysis Target", ["Select from Tracked Applications", "Custom Job Description"], horizontal=True)

    required_skills_list = []
    target_title = ""

    if analysis_mode == "Select from Tracked Applications":
        if not apps_with_reqs:
            st.info("No applications currently have required skills or job descriptions. Add some in the Applications tab.")
        else:
            app_choices = {a.id: f"{a.company} — {a.role}" for a in apps_with_reqs}
            sel_target_id = st.selectbox("Choose Application", list(app_choices.keys()), format_func=lambda i: app_choices[i])
            with session_scope() as session:
                target_app = get_application(session, sel_target_id)
            if target_app:
                target_title = f"{target_app.company} ({target_app.role})"
                required_skills_list = [r.skill_name for r in target_app.required_skills]
                if not required_skills_list and target_app.job_description and target_app.job_description.raw_text:
                    from services.document_parser import KNOWN_SKILLS
                    raw = target_app.job_description.raw_text.lower()
                    required_skills_list = [k for k in KNOWN_SKILLS if k.lower() in raw]
    else:
        target_title = "Custom Job Description"
        custom_jd = st.text_area("Paste Job Description or Required Skills", height=150, placeholder="Required: Python, SQL, Pandas, Machine Learning, Power BI, Statistics...")
        if custom_jd:
            from services.document_parser import KNOWN_SKILLS
            raw_c = custom_jd.lower()
            required_skills_list = [k for k in KNOWN_SKILLS if k.lower() in raw_c]

    if required_skills_list:
        st.markdown(f"### Skill Match Report: **{target_title}**")
        verified_matches = []
        unverified_matches = []
        missing_skills = []

        for req in required_skills_list:
            matched = user_skills_dict.get(req.lower())
            if matched:
                if matched.verified:
                    verified_matches.append(matched.name)
                else:
                    unverified_matches.append(matched.name)
            else:
                missing_skills.append(req)

        total_req = len(required_skills_list)
        match_score = int(100 * len(verified_matches) / total_req) if total_req else 0

        sc1, sc2, sc3 = st.columns(3)
        sc1.metric("Readiness Score (Verified)", f"{match_score}%")
        sc2.metric("Verified Matches", len(verified_matches))
        sc3.metric("Skills to Acquire / Verify", len(missing_skills) + len(unverified_matches))

        st.progress(match_score / 100)

        col_m1, col_m2 = st.columns(2)
        with col_m1:
            st.markdown("#### ✅ Verified Matching Skills")
            if verified_matches:
                for s in verified_matches:
                    st.success(f"**{s}** (Verified)")
            else:
                st.caption("No verified skills matched yet.")

            if unverified_matches:
                st.markdown("#### ⏳ Skills in Catalog but Unverified")
                for s in unverified_matches:
                    st.warning(f"**{s}** (Needs project evidence or verification in Skills Catalog)")

        with col_m2:
            st.markdown("#### ❌ Missing Required Skills")
            if missing_skills:
                for s in missing_skills:
                    st.error(f"**{s}** (Recommended to learn / build a project for)")
            else:
                st.balloons()
                st.success("Great job! You have all required skills in your catalog.")

# ==============================================================================
# 3. INTERVIEWS TAB
# ==============================================================================
with tab_interview:
    st.subheader("Interview Rounds")
    if not all_apps:
        empty_state("No applications", "Add an application first before scheduling interview rounds.")
    else:
        app_opts = {a.id: f"{a.company} — {a.role}" for a in all_apps}
        sel_app_for_iv = st.selectbox("Select Application", list(app_opts.keys()), format_func=lambda i: app_opts[i], key="iv_app_sel")
        with session_scope() as session:
            active_app = get_application(session, sel_app_for_iv)

        if active_app:
            st.write(f"Rounds for **{active_app.company} - {active_app.role}**:")
            if active_app.interviews:
                for iv in active_app.interviews:
                    ic1, ic2, ic3, ic4 = st.columns((3, 2, 2, 1))
                    ic1.write(f"**{iv.round_name}** ({iv.outcome})")
                    ic2.write(f"Time: {iv.scheduled_at.strftime('%Y-%m-%d %H:%M') if iv.scheduled_at else 'TBD'}")
                    ic3.write(iv.notes or "No notes")
                    if ic4.button("Delete", key=f"del_iv_{iv.id}"):
                        with session_scope() as session:
                            delete_interview(session, iv.id)
                        st.success("Round removed.")
                        st.rerun()
            else:
                st.caption("No interview rounds scheduled yet.")

            st.markdown("---")
            st.markdown("##### Schedule New Round")
            with st.form(f"add_iv_form_{active_app.id}"):
                round_name = st.text_input("Round Name (e.g. Technical Screening, SQL Assessment, Machine Learning Round)")
                c_date, c_time = st.columns(2)
                r_date = c_date.date_input("Date", value=date.today())
                r_outcome = c_time.selectbox("Outcome / Status", ["scheduled", "passed", "failed", "pending_feedback"])
                r_notes = st.text_area("Questions asked / Preparation focus")
                if st.form_submit_button("Add Interview Round"):
                    try:
                        with session_scope() as session:
                            create_interview(
                                session,
                                active_app.id,
                                {
                                    "round_name": round_name,
                                    "scheduled_at": datetime.combine(r_date, datetime.min.time()),
                                    "outcome": r_outcome,
                                    "notes": r_notes,
                                },
                            )
                        st.success("Interview round scheduled.")
                        st.rerun()
                    except ValidationError as ve:
                        st.error(str(ve))

# ==============================================================================
# 4. TASKS & REMINDERS TAB
# ==============================================================================
with tab_tasks:
    st.subheader("Placement Preparation Tasks & Reminders")
    with session_scope() as session:
        tasks = list_tasks(session)

    if tasks:
        rows = [
            {
                "id": t.id,
                "title": t.title,
                "due_date": str(t.due_date) if t.due_date else "—",
                "priority": t.priority.upper(),
                "status": t.status.upper(),
            }
            for t in tasks
        ]
        df_tasks = pd.DataFrame(rows)
        st.dataframe(df_tasks, use_container_width=True, hide_index=True)
    else:
        empty_state("No open tasks", "Keep track of assignment submissions, cold outreach, and revision tasks below.")

    st.markdown("---")
    st.markdown("##### Create Task")
    with st.form("new_task_form"):
        t_title = st.text_input("Task Title * (e.g. Review SQL Window Functions, Submit OA for Acme Corp)")
        tc1, tc2, tc3 = st.columns(3)
        t_due = tc1.date_input("Due Date", value=date.today())
        t_pri = tc2.selectbox("Priority", ["high", "medium", "low"])
        t_stat = tc3.selectbox("Status", ["open", "in_progress", "completed"])
        t_desc = st.text_area("Details")
        if st.form_submit_button("Create Task", type="primary"):
            try:
                with session_scope() as session:
                    create_task(
                        session,
                        {
                            "title": t_title,
                            "due_date": t_due,
                            "priority": t_pri,
                            "status": t_stat,
                            "description": t_desc,
                        },
                    )
                st.success("Task created.")
                st.rerun()
            except ValidationError as ve:
                st.error(str(ve))
