"""Fictional sample records, clearly labeled and removable from Settings."""

from __future__ import annotations

from datetime import date

from sqlalchemy import select

from database.crud import create_project, get_profile, get_or_create_skill, upsert_profile
from database.models import Education, Experience, Project
from database.session import session_scope

SAMPLE_NOTICE = (
    "FICTIONAL SAMPLE DATA for UI demonstration only. "
    "These records are not real credentials, grades, or employment. Remove them in Settings."
)


def seed_sample_data() -> None:
    with session_scope() as session:
        profile = get_profile(session)
        if profile and not profile.is_sample:
            return
        upsert_profile(
            session,
            {
                "full_name": "Alex Rivera (FICTIONAL SAMPLE)",
                "headline": "Aspiring Data Analyst — SAMPLE PROFILE, not a real person",
                "email": "sample.not.real@example.com",
                "phone": None,
                "location": "Sample City",
                "linkedin_url": None,
                "github_username": "vaibhav007-star",
                "github_url": "https://github.com/vaibhav007-star",
                "portfolio_url": None,
                "summary": SAMPLE_NOTICE,
                "target_roles": "Data Analyst intern, Data Science intern",
                "include_email_in_public_export": False,
                "is_sample": True,
            },
        )
        for name, category in (
            ("Python", "technical"),
            ("SQL", "technical"),
            ("Pandas", "technical"),
            ("Power BI", "tool"),
            ("Excel", "tool"),
        ):
            get_or_create_skill(
                session,
                name,
                category=category,
                proficiency="intermediate",
                verified=False,
                source="sample",
                is_sample=True,
            )
        if session.scalar(select(Education).where(Education.is_sample.is_(True))) is None:
            session.add(
                Education(
                    institution="Sample State University (FICTIONAL)",
                    degree="B.Sc. (sample)",
                    field_of_study="Statistics — fictional",
                    start_date=date(2022, 8, 1),
                    currently_enrolled=True,
                    grade=None,
                    description=SAMPLE_NOTICE,
                    is_sample=True,
                )
            )
        if session.scalar(select(Experience).where(Experience.is_sample.is_(True))) is None:
            session.add(
                Experience(
                    organization="Sample Analytics Lab (FICTIONAL)",
                    title="Student volunteer — not real employment",
                    location="Remote",
                    start_date=date(2025, 1, 1),
                    currently_working=True,
                    experience_type="volunteer",
                    description=SAMPLE_NOTICE,
                    is_sample=True,
                )
            )
        existing = session.scalar(select(Project).where(Project.is_sample.is_(True)))
        if not existing:
            create_project(
                session,
                {
                    "title": "Retail Sales Dashboard (FICTIONAL SAMPLE)",
                    "description": SAMPLE_NOTICE + " No real business outcomes are claimed.",
                    "role": "Analyst (sample)",
                    "start_date": date(2026, 1, 1),
                    "end_date": date(2026, 3, 1),
                    "status": "completed",
                    "github_url": None,
                    "live_demo_url": None,
                    "dataset_url": None,
                    "report_url": None,
                    "outcomes": None,
                    "is_public": True,
                    "is_sample": True,
                    "allow_duplicate": True,
                },
                skill_names=["Python", "Power BI", "Excel"],
            )


if __name__ == "__main__":
    seed_sample_data()
    print("Fictional sample data loaded. Remove it from Settings when you add real records.")
