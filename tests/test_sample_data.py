from __future__ import annotations

from database.crud import delete_sample_records, get_profile, list_projects
from database.seed import SAMPLE_NOTICE, seed_sample_data
from database.session import session_scope


def test_sample_data_is_labeled_and_removable(initialized_db):
    seed_sample_data()
    with session_scope() as session:
        profile = get_profile(session)
        assert profile is not None
        assert profile.is_sample is True
        assert "FICTIONAL" in profile.full_name
        projects = list_projects(session)
        assert projects
        assert all(p.is_sample for p in projects)
        assert SAMPLE_NOTICE.split()[0] == "FICTIONAL"
        removed = delete_sample_records(session)
        assert removed >= 1
        assert get_profile(session) is None
