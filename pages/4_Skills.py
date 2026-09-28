"""Skills Catalog CRUD: manage, verify, categorize, and export skills."""

from __future__ import annotations

import pandas as pd
import streamlit as st

from components.layout import page_setup
from components.ui import dataframe_download, empty_state
from database.crud import (
    create_skill,
    delete_skill,
    get_skill,
    list_skills,
    update_skill,
)
from database.session import session_scope
from utils.bootstrap import bootstrap
from utils.validation import ValidationError

bootstrap()
page_setup("Skills", "💡")

st.title("Skills Catalog")
st.caption(
    "Manage your verified and emerging skills. Verified skills are used in skill-gap analysis and resume targeting."
)

with session_scope() as session:
    all_skills = list_skills(session)

# Top metrics
c1, c2, c3, c4 = st.columns(4)
total_count = len(all_skills)
verified_count = sum(1 for s in all_skills if s.verified)
tech_count = sum(1 for s in all_skills if s.category == "technical")
tools_count = sum(1 for s in all_skills if s.category == "tool")

c1.metric("Total Skills", total_count)
c2.metric("Verified Skills", verified_count)
c3.metric("Technical Skills", tech_count)
c4.metric("Tools & Platforms", tools_count)

st.divider()

# Filter and Search
f1, f2, f3 = st.columns((3, 2, 2))
search = f1.text_input("Search skill name")
category_filter = f2.selectbox(
    "Category",
    ["all", "technical", "analytical", "tool", "soft_skill", "other"],
)
verified_filter = f3.selectbox("Verification", ["all", "verified_only", "unverified_only"])

with session_scope() as session:
    skills = list_skills(
        session,
        search=search or None,
        category=category_filter if category_filter != "all" else None,
        verified_only=(verified_filter == "verified_only"),
    )
    if verified_filter == "unverified_only":
        skills = [s for s in skills if not s.verified]

# Display table
if skills:
    rows = [
        {
            "id": s.id,
            "name": s.name,
            "category": s.category,
            "proficiency": s.proficiency,
            "verified": "✅ Verified" if s.verified else "⏳ Unverified",
            "source": s.source,
            "notes": s.notes or "",
        }
        for s in skills
    ]
    df = pd.DataFrame(rows)
    st.dataframe(df, use_container_width=True, hide_index=True)
    dataframe_download(df, "skills_export.csv", "Export Skills CSV")
else:
    empty_state("No skills found", "Add a skill below or adjust search filters.")

st.divider()

# Create or Edit Section
st.subheader("Add or Edit Skill")
mode = st.radio("Action", ["Add new skill", "Edit existing skill"], horizontal=True)

if mode == "Add new skill":
    with st.form("add_skill_form"):
        col_a, col_b = st.columns(2)
        name = col_a.text_input("Skill name * (e.g. Pandas, SQL, PyTorch)")
        category = col_b.selectbox("Category", ["technical", "analytical", "tool", "soft_skill", "other"])
        col_c, col_d = st.columns(2)
        proficiency = col_c.selectbox("Proficiency", ["beginner", "intermediate", "advanced", "expert"])
        verified = col_d.checkbox("Verified (I have built projects or passed tests using this)")
        notes = st.text_area("Notes / Proof / Context (optional)")
        submitted = st.form_submit_button("Save Skill", type="primary")

        if submitted:
            try:
                with session_scope() as session:
                    create_skill(
                        session,
                        {
                            "name": name,
                            "category": category,
                            "proficiency": proficiency,
                            "verified": verified,
                            "source": "manual",
                            "notes": notes,
                        },
                    )
                st.success(f"Skill '{name}' added.")
                st.rerun()
            except ValidationError as exc:
                st.error(str(exc))

else:
    if not skills:
        st.info("No skills available to edit.")
    else:
        skill_options = {s.id: f"{s.name} ({s.category})" for s in skills}
        selected_id = st.selectbox("Select skill to edit", list(skill_options.keys()), format_func=lambda i: skill_options[i])
        with session_scope() as session:
            current_skill = get_skill(session, selected_id)

        if current_skill:
            with st.form("edit_skill_form"):
                col_a, col_b = st.columns(2)
                edit_name = col_a.text_input("Skill name *", value=current_skill.name)
                cats = ["technical", "analytical", "tool", "soft_skill", "other"]
                cat_idx = cats.index(current_skill.category) if current_skill.category in cats else 0
                edit_category = col_b.selectbox("Category", cats, index=cat_idx)
                
                col_c, col_d = st.columns(2)
                profs = ["beginner", "intermediate", "advanced", "expert"]
                prof_idx = profs.index(current_skill.proficiency) if current_skill.proficiency in profs else 1
                edit_proficiency = col_c.selectbox("Proficiency", profs, index=prof_idx)
                edit_verified = col_d.checkbox("Verified", value=current_skill.verified)
                edit_notes = st.text_area("Notes", value=current_skill.notes or "")
                
                col_btn1, col_btn2 = st.columns((3, 1))
                save_edit = col_btn1.form_submit_button("Update Skill", type="primary")

                if save_edit:
                    try:
                        with session_scope() as session:
                            update_skill(
                                session,
                                selected_id,
                                {
                                    "name": edit_name,
                                    "category": edit_category,
                                    "proficiency": edit_proficiency,
                                    "verified": edit_verified,
                                    "notes": edit_notes,
                                },
                            )
                        st.success(f"Skill '{edit_name}' updated.")
                        st.rerun()
                    except ValidationError as exc:
                        st.error(str(exc))

            if st.button("Delete this skill", type="secondary"):
                with session_scope() as session:
                    delete_skill(session, selected_id)
                st.success("Skill deleted.")
                st.rerun()
