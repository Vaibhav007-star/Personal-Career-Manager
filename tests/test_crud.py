from __future__ import annotations

import pytest

from database.crud import (
    create_project,
    delete_project,
    find_duplicate_projects,
    get_or_create_skill,
    get_profile,
    get_project,
    list_projects,
    update_project,
    upsert_profile,
)
from utils.validation import ValidationError


def test_profile_requires_name(db_session):
    with pytest.raises(ValidationError):
        upsert_profile(db_session, {"full_name": "  "})


def test_profile_upsert(db_session):
    first = upsert_profile(db_session, {"full_name": "Vaibhav", "email": "you@example.com"})
    second = upsert_profile(db_session, {"full_name": "Vaibhav K", "github_username": "vaibhav007-star"})
    assert first.id == second.id
    profile = get_profile(db_session)
    assert profile is not None
    assert profile.full_name == "Vaibhav K"
    assert profile.github_username == "vaibhav007-star"
    assert profile.email == "you@example.com"


def test_invalid_email(db_session):
    with pytest.raises(ValidationError):
        upsert_profile(db_session, {"full_name": "A", "email": "not-an-email"})


def test_project_crud_and_skills(db_session):
    project = create_project(
        db_session,
        {
            "title": "Churn analysis",
            "description": "Internal practice project",
            "status": "in_progress",
            "github_url": "https://github.com/vaibhav007-star/example",
        },
        skill_names=["Python", "SQL"],
    )
    loaded = get_project(db_session, project.id)
    assert loaded is not None
    names = sorted(t.skill.name for t in loaded.technologies)
    assert names == ["Python", "SQL"]
    update_project(db_session, project.id, {"title": "Churn analysis v2", "allow_duplicate": True}, skill_names=["Python"])
    loaded = get_project(db_session, project.id)
    assert loaded.title == "Churn analysis v2"
    assert [t.skill.name for t in loaded.technologies] == ["Python"]
    listed = list_projects(db_session, search="churn")
    assert len(listed) == 1
    delete_project(db_session, project.id)
    assert get_project(db_session, project.id) is None


def test_duplicate_project_blocked(db_session):
    payload = {"title": "Same Title", "status": "planning"}
    create_project(db_session, payload)
    with pytest.raises(ValidationError, match="similar project"):
        create_project(db_session, payload)
    create_project(db_session, {**payload, "allow_duplicate": True})
    dupes = find_duplicate_projects(db_session, "Same Title", None)
    assert len(dupes) == 2


def test_skill_unique(db_session):
    a = get_or_create_skill(db_session, "Pandas")
    b = get_or_create_skill(db_session, "Pandas")
    assert a.id == b.id


def test_end_before_start_rejected(db_session):
    with pytest.raises(ValidationError):
        create_project(
            db_session,
            {
                "title": "Bad dates",
                "start_date": "2026-06-01",
                "end_date": "2026-01-01",
            },
        )
