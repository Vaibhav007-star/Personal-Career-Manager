"""Project portfolio CRUD with search, filters, duplicate checks, and export."""

from __future__ import annotations

from datetime import date

import pandas as pd
import streamlit as st

from components.layout import page_setup
from components.ui import dataframe_download, empty_state, sample_badge, status_badge
from database.crud import (
    add_project_asset,
    create_project,
    delete_project,
    delete_project_asset,
    get_project,
    list_projects,
    list_skills,
    update_project,
)
from database.session import session_scope
from utils.bootstrap import bootstrap
from utils.validation import ValidationError

bootstrap()
page_setup("Projects", "📁")

st.title("Projects")
st.caption("Store only work you actually did. Outcomes stay blank unless you type them yourself.")

with session_scope() as session:
    all_skills = [s.name for s in list_skills(session)]

filters = st.columns((3, 2, 2, 1))
search = filters[0].text_input("Search title, role, or description")
status_filter = filters[1].selectbox(
    "Status",
    ["all", "planning", "in_progress", "completed", "archived"],
)
sort = filters[2].selectbox("Sort", ["updated_desc", "title", "status"], format_func=lambda x: {
    "updated_desc": "Recently updated",
    "title": "Title",
    "status": "Status",
}[x])

with session_scope() as session:
    projects = list_projects(session, search=search or None, status=status_filter, sort=sort)

if filters[3].button("Refresh"):
    st.rerun()

if projects:
    rows = []
    for p in projects:
        techs = ", ".join(t.skill.name for t in p.technologies if t.skill)
        rows.append(
            {
                "id": p.id,
                "title": p.title,
                "status": p.status,
                "role": p.role or "",
                "technologies": techs,
                "github_url": p.github_url or "",
                "live_demo_url": p.live_demo_url or "",
                "is_sample": p.is_sample,
                "updated_at": p.updated_at,
            }
        )
    df = pd.DataFrame(rows)
    st.dataframe(df.drop(columns=["is_sample"]), use_container_width=True, hide_index=True)
    export_cols = st.columns(2)
    with export_cols[0]:
        dataframe_download(df.drop(columns=["is_sample"]), "projects.csv", "Export projects CSV")
else:
    empty_state("No projects match", "Create one below, or clear search filters.")

st.divider()
st.subheader("Create or edit")

ids = [p.id for p in projects]
labels = {p.id: f"{p.id} — {p.title}" for p in projects}
mode = st.radio("Mode", ["Create new", "Edit existing"], horizontal=True)
editing_id = None
current = None
if mode == "Edit existing":
    if not ids:
        st.warning("Nothing to edit yet.")
    else:
        editing_id = st.selectbox("Select project", ids, format_func=lambda i: labels[i])
        with session_scope() as session:
            current = get_project(session, editing_id)

def _val(attr: str, default: str = "") -> str:
    if current is None:
        return default
    value = getattr(current, attr)
    return value or default

with st.form("project_form"):
    title = st.text_input("Title *", value=_val("title"))
    description = st.text_area("Description", value=_val("description"), height=120)
    c1, c2, c3 = st.columns(3)
    role = c1.text_input("Your role", value=_val("role"))
    status = c2.selectbox(
        "Status",
        ["planning", "in_progress", "completed", "archived"],
        index=["planning", "in_progress", "completed", "archived"].index(
            current.status if current else "in_progress"
        ),
    )
    is_public = c3.checkbox("Include in future public portfolio", value=current.is_public if current else True)
    d1, d2 = st.columns(2)
    start_date = d1.date_input("Start date", value=current.start_date if current and current.start_date else date.today())
    use_end = d2.checkbox("Has end date", value=bool(current and current.end_date))
    end_date = d2.date_input("End date", value=current.end_date if current and current.end_date else date.today())
    u1, u2 = st.columns(2)
    github_url = u1.text_input("GitHub repository URL", value=_val("github_url"))
    live_demo_url = u2.text_input("Live demo URL", value=_val("live_demo_url"))
    u3, u4 = st.columns(2)
    dataset_url = u3.text_input("Dataset URL", value=_val("dataset_url"))
    report_url = u4.text_input("Report URL", value=_val("report_url"))
    selected_tech = []
    if current:
        selected_tech = [t.skill.name for t in current.technologies if t.skill]
    technologies = st.multiselect("Technologies (from skills)", options=all_skills, default=selected_tech)
    extra_tech = st.text_input("Add technologies (comma-separated)", value="")
    outcomes = st.text_area(
        "Outcomes (optional — only facts you can stand behind)",
        value=_val("outcomes"),
        height=80,
    )
    allow_duplicate = st.checkbox("Allow save even if title or GitHub URL already exists")
    save = st.form_submit_button("Save project", type="primary")

if save:
    extra = [part.strip() for part in extra_tech.split(",") if part.strip()]
    skill_names = list(dict.fromkeys(list(technologies) + extra))
    payload = {
        "title": title,
        "description": description,
        "role": role,
        "status": status,
        "is_public": is_public,
        "start_date": start_date,
        "end_date": end_date if use_end else None,
        "github_url": github_url,
        "live_demo_url": live_demo_url,
        "dataset_url": dataset_url,
        "report_url": report_url,
        "outcomes": outcomes,
        "allow_duplicate": allow_duplicate,
        "is_sample": False,
    }
    try:
        with session_scope() as session:
            if mode == "Edit existing" and editing_id:
                update_project(session, editing_id, payload, skill_names=skill_names)
                st.success("Project updated.")
            else:
                create_project(session, payload, skill_names=skill_names)
                st.success("Project created.")
        st.rerun()
    except ValidationError as exc:
        st.error(str(exc))

if mode == "Edit existing" and current:
    sample_badge(current.is_sample)
    st.markdown(status_badge(current.status), unsafe_allow_html=True)
    st.markdown("#### Linked assets")
    with session_scope() as session:
        fresh = get_project(session, current.id)
        assets = list(fresh.assets) if fresh else []
    if assets:
        for asset in assets:
            cols = st.columns((4, 2, 1))
            cols[0].write(f"{asset.asset_type}: **{asset.label}**")
            cols[1].write(asset.url or "—")
            if cols[2].button("Delete", key=f"del_asset_{asset.id}"):
                try:
                    with session_scope() as session:
                        delete_project_asset(session, asset.id)
                    st.rerun()
                except ValidationError as exc:
                    st.error(str(exc))
    with st.form(f"asset_form_{current.id}"):
        a1, a2, a3 = st.columns(3)
        asset_type = a1.selectbox("Type", ["screenshot", "demo", "dataset", "report", "other"])
        label = a2.text_input("Label")
        url = a3.text_input("https URL")
        if st.form_submit_button("Add asset"):
            try:
                with session_scope() as session:
                    add_project_asset(session, current.id, asset_type, label, url or None)
                st.success("Asset saved.")
                st.rerun()
            except ValidationError as exc:
                st.error(str(exc))
    st.markdown("#### Delete project")
    confirm = st.text_input("Type DELETE to confirm")
    if st.button("Delete project", type="secondary"):
        if confirm != "DELETE":
            st.error("Type DELETE to confirm.")
        else:
            try:
                with session_scope() as session:
                    delete_project(session, current.id)
                st.success("Project deleted.")
                st.rerun()
            except ValidationError as exc:
                st.error(str(exc))
