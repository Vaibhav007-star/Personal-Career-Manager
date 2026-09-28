from __future__ import annotations

from datetime import date
import pytest

from database.crud import (
    create_application,
    create_interview,
    create_task,
    get_application,
    get_or_create_skill,
    list_applications,
    list_tasks,
    set_application_required_skills,
    update_application,
)
from utils.validation import ValidationError


def test_application_crud(db_session):
    app = create_application(
        db_session,
        {
            "company": "DeepMind Partner Lab",
            "role": "Data Scientist Intern",
            "status": "applied",
            "deadline": "2026-11-01",
            "raw_job_description": "We need someone with strong Python, SQL, and Machine Learning experience.",
        },
    )
    assert app.id is not None
    assert app.company == "DeepMind Partner Lab"
    assert app.job_description is not None
    assert "Python" in app.job_description.raw_text

    updated = update_application(db_session, app.id, {"company": "DeepMind Partner Lab", "role": "Data Scientist Intern", "status": "interview"})
    assert updated.status == "interview"


def test_interview_rounds_and_tasks(db_session):
    app = create_application(
        db_session,
        {"company": "Tech Corp", "role": "Analytics Intern", "status": "interview"},
    )
    iv = create_interview(
        db_session,
        app.id,
        {"round_name": "Technical Assessment", "outcome": "scheduled"},
    )
    assert iv.id is not None
    assert iv.application_id == app.id

    task = create_task(
        db_session,
        {
            "title": "Prepare SQL window functions for Tech Corp",
            "due_date": "2026-10-15",
            "priority": "high",
            "related_application_id": app.id,
        },
    )
    assert task.id is not None
    tasks = list_tasks(db_session)
    assert any(t.title == task.title for t in tasks)


def test_skill_gap_analysis(db_session):
    get_or_create_skill(db_session, "Python", verified=True)
    get_or_create_skill(db_session, "SQL", verified=True)
    get_or_create_skill(db_session, "Tableau", verified=False)

    app = create_application(
        db_session,
        {"company": "Analytics Firm", "role": "Data Analyst Intern"},
    )
    reqs = set_application_required_skills(
        db_session, app.id, ["Python", "SQL", "Tableau", "Docker"]
    )
    assert len(reqs) == 4

    verified_matches = [r.skill_name for r in reqs if r.is_verified_match]
    assert "Python" in verified_matches
    assert "SQL" in verified_matches
    assert "Tableau" not in verified_matches
    assert "Docker" not in verified_matches
