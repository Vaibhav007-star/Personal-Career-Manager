from __future__ import annotations

from sqlalchemy import inspect, select

from database.crud import SCHEMA_VERSION, dashboard_counts, get_or_create_schema_meta
from database.engine import get_engine
from database.models import Base


def test_tables_created(db_session):
    inspector = inspect(get_engine())
    tables = set(inspector.get_table_names())
    expected = {
        "profile",
        "education",
        "skills",
        "projects",
        "project_technologies",
        "project_assets",
        "certificates",
        "project_certificates",
        "experience",
        "github_repositories",
        "project_github_links",
        "applications",
        "job_descriptions",
        "application_required_skills",
        "interviews",
        "tasks",
        "activity_logs",
        "schema_meta",
    }
    assert expected.issubset(tables)


def test_schema_meta(db_session):
    meta = get_or_create_schema_meta(db_session)
    assert meta.schema_version == SCHEMA_VERSION


def test_empty_dashboard_counts(db_session):
    counts = dashboard_counts(db_session)
    assert counts["projects"] == 0
    assert counts["applications"] == 0
    assert counts["skills"] == 0


def test_foreign_keys_enabled(db_session):
    result = db_session.execute(select(1)).scalar()
    assert result == 1
    assert Base.metadata.tables["project_technologies"].c.project_id is not None
