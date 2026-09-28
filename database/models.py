"""SQLAlchemy 2.0 models for the Personal Career Management System."""

from __future__ import annotations

from datetime import date, datetime
from typing import Optional

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Date,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


class TimestampMixin:
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now(), nullable=False
    )


class Profile(Base, TimestampMixin):
    __tablename__ = "profile"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    full_name: Mapped[str] = mapped_column(String(200), nullable=False)
    headline: Mapped[Optional[str]] = mapped_column(String(300))
    email: Mapped[Optional[str]] = mapped_column(String(254))
    phone: Mapped[Optional[str]] = mapped_column(String(50))
    location: Mapped[Optional[str]] = mapped_column(String(200))
    linkedin_url: Mapped[Optional[str]] = mapped_column(String(500))
    github_username: Mapped[Optional[str]] = mapped_column(String(100))
    github_url: Mapped[Optional[str]] = mapped_column(String(500))
    portfolio_url: Mapped[Optional[str]] = mapped_column(String(500))
    summary: Mapped[Optional[str]] = mapped_column(Text)
    target_roles: Mapped[Optional[str]] = mapped_column(String(500))
    include_email_in_public_export: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_sample: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)


class Education(Base, TimestampMixin):
    __tablename__ = "education"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    institution: Mapped[str] = mapped_column(String(300), nullable=False)
    degree: Mapped[Optional[str]] = mapped_column(String(200))
    field_of_study: Mapped[Optional[str]] = mapped_column(String(200))
    start_date: Mapped[Optional[date]] = mapped_column(Date)
    end_date: Mapped[Optional[date]] = mapped_column(Date)
    currently_enrolled: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    grade: Mapped[Optional[str]] = mapped_column(String(50))
    description: Mapped[Optional[str]] = mapped_column(Text)
    is_sample: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)


class Skill(Base, TimestampMixin):
    __tablename__ = "skills"
    __table_args__ = (UniqueConstraint("name", name="uq_skills_name"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    category: Mapped[str] = mapped_column(String(50), default="technical", nullable=False)
    proficiency: Mapped[str] = mapped_column(String(30), default="intermediate", nullable=False)
    verified: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    source: Mapped[str] = mapped_column(String(30), default="manual", nullable=False)
    notes: Mapped[Optional[str]] = mapped_column(Text)
    is_sample: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)


class Project(Base, TimestampMixin):
    __tablename__ = "projects"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    title: Mapped[str] = mapped_column(String(300), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text)
    role: Mapped[Optional[str]] = mapped_column(String(200))
    start_date: Mapped[Optional[date]] = mapped_column(Date)
    end_date: Mapped[Optional[date]] = mapped_column(Date)
    status: Mapped[str] = mapped_column(String(30), default="in_progress", nullable=False)
    github_url: Mapped[Optional[str]] = mapped_column(String(500))
    live_demo_url: Mapped[Optional[str]] = mapped_column(String(500))
    dataset_url: Mapped[Optional[str]] = mapped_column(String(500))
    report_url: Mapped[Optional[str]] = mapped_column(String(500))
    outcomes: Mapped[Optional[str]] = mapped_column(Text)
    is_public: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    is_sample: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    technologies: Mapped[list[ProjectTechnology]] = relationship(
        back_populates="project", cascade="all, delete-orphan"
    )
    assets: Mapped[list[ProjectAsset]] = relationship(
        back_populates="project", cascade="all, delete-orphan"
    )
    github_links: Mapped[list[ProjectGithubLink]] = relationship(
        back_populates="project", cascade="all, delete-orphan"
    )
    certificate_links: Mapped[list[ProjectCertificate]] = relationship(
        back_populates="project", cascade="all, delete-orphan"
    )


class ProjectTechnology(Base):
    __tablename__ = "project_technologies"
    __table_args__ = (UniqueConstraint("project_id", "skill_id", name="uq_project_skill"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    project_id: Mapped[int] = mapped_column(ForeignKey("projects.id", ondelete="CASCADE"), nullable=False)
    skill_id: Mapped[int] = mapped_column(ForeignKey("skills.id", ondelete="CASCADE"), nullable=False)

    project: Mapped[Project] = relationship(back_populates="technologies")
    skill: Mapped[Skill] = relationship()


class ProjectAsset(Base, TimestampMixin):
    __tablename__ = "project_assets"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    project_id: Mapped[int] = mapped_column(ForeignKey("projects.id", ondelete="CASCADE"), nullable=False)
    asset_type: Mapped[str] = mapped_column(String(40), nullable=False)
    label: Mapped[str] = mapped_column(String(200), nullable=False)
    url: Mapped[Optional[str]] = mapped_column(String(1000))
    local_path: Mapped[Optional[str]] = mapped_column(String(1000))

    project: Mapped[Project] = relationship(back_populates="assets")


class Certificate(Base, TimestampMixin):
    __tablename__ = "certificates"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(300), nullable=False)
    issuer: Mapped[Optional[str]] = mapped_column(String(300))
    issue_date: Mapped[Optional[date]] = mapped_column(Date)
    expiry_date: Mapped[Optional[date]] = mapped_column(Date)
    credential_id: Mapped[Optional[str]] = mapped_column(String(200))
    credential_url: Mapped[Optional[str]] = mapped_column(String(500))
    verification_status: Mapped[str] = mapped_column(String(40), default="unverified", nullable=False)
    notes: Mapped[Optional[str]] = mapped_column(Text)
    is_sample: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    project_links: Mapped[list[ProjectCertificate]] = relationship(back_populates="certificate")


class ProjectCertificate(Base):
    __tablename__ = "project_certificates"
    __table_args__ = (UniqueConstraint("project_id", "certificate_id", name="uq_project_certificate"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    project_id: Mapped[int] = mapped_column(ForeignKey("projects.id", ondelete="CASCADE"), nullable=False)
    certificate_id: Mapped[int] = mapped_column(
        ForeignKey("certificates.id", ondelete="CASCADE"), nullable=False
    )

    project: Mapped[Project] = relationship(back_populates="certificate_links")
    certificate: Mapped[Certificate] = relationship(back_populates="project_links")


class Experience(Base, TimestampMixin):
    __tablename__ = "experience"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    organization: Mapped[str] = mapped_column(String(300), nullable=False)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    location: Mapped[Optional[str]] = mapped_column(String(200))
    start_date: Mapped[Optional[date]] = mapped_column(Date)
    end_date: Mapped[Optional[date]] = mapped_column(Date)
    currently_working: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    experience_type: Mapped[str] = mapped_column(String(40), default="internship", nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text)
    is_sample: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)


class GithubRepository(Base, TimestampMixin):
    __tablename__ = "github_repositories"
    __table_args__ = (UniqueConstraint("github_id", name="uq_github_id"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    github_id: Mapped[int] = mapped_column(Integer, nullable=False)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    full_name: Mapped[str] = mapped_column(String(300), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text)
    html_url: Mapped[str] = mapped_column(String(500), nullable=False)
    homepage: Mapped[Optional[str]] = mapped_column(String(500))
    language: Mapped[Optional[str]] = mapped_column(String(80))
    topics_json: Mapped[Optional[str]] = mapped_column(Text)
    stars: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    forks: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    is_private: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_fork: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    readme_content: Mapped[Optional[str]] = mapped_column(Text)
    pushed_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    imported_at: Mapped[Optional[datetime]] = mapped_column(DateTime)

    project_links: Mapped[list[ProjectGithubLink]] = relationship(back_populates="repository")


class ProjectGithubLink(Base):
    __tablename__ = "project_github_links"
    __table_args__ = (UniqueConstraint("project_id", "github_repo_id", name="uq_project_github"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    project_id: Mapped[int] = mapped_column(ForeignKey("projects.id", ondelete="CASCADE"), nullable=False)
    github_repo_id: Mapped[int] = mapped_column(
        ForeignKey("github_repositories.id", ondelete="CASCADE"), nullable=False
    )

    project: Mapped[Project] = relationship(back_populates="github_links")
    repository: Mapped[GithubRepository] = relationship(back_populates="project_links")


class Application(Base, TimestampMixin):
    __tablename__ = "applications"
    __table_args__ = (
        CheckConstraint(
            "status in ('wishlist','applied','oa','interview','offer','rejected','withdrawn')",
            name="ck_application_status",
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    company: Mapped[str] = mapped_column(String(200), nullable=False)
    role: Mapped[str] = mapped_column(String(200), nullable=False)
    source: Mapped[Optional[str]] = mapped_column(String(120))
    application_url: Mapped[Optional[str]] = mapped_column(String(500))
    deadline: Mapped[Optional[date]] = mapped_column(Date)
    applied_date: Mapped[Optional[date]] = mapped_column(Date)
    status: Mapped[str] = mapped_column(String(30), default="wishlist", nullable=False)
    follow_up_date: Mapped[Optional[date]] = mapped_column(Date)
    notes: Mapped[Optional[str]] = mapped_column(Text)
    is_sample: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    job_description: Mapped[Optional[JobDescription]] = relationship(
        back_populates="application", uselist=False, cascade="all, delete-orphan"
    )
    interviews: Mapped[list[Interview]] = relationship(
        back_populates="application", cascade="all, delete-orphan"
    )
    required_skills: Mapped[list[ApplicationRequiredSkill]] = relationship(
        back_populates="application", cascade="all, delete-orphan"
    )


class JobDescription(Base, TimestampMixin):
    __tablename__ = "job_descriptions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    application_id: Mapped[int] = mapped_column(
        ForeignKey("applications.id", ondelete="CASCADE"), unique=True, nullable=False
    )
    raw_text: Mapped[str] = mapped_column(Text, nullable=False)
    extracted_requirements: Mapped[Optional[str]] = mapped_column(Text)

    application: Mapped[Application] = relationship(back_populates="job_description")


class ApplicationRequiredSkill(Base):
    __tablename__ = "application_required_skills"
    __table_args__ = (UniqueConstraint("application_id", "skill_name", name="uq_app_skill_name"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    application_id: Mapped[int] = mapped_column(
        ForeignKey("applications.id", ondelete="CASCADE"), nullable=False
    )
    skill_name: Mapped[str] = mapped_column(String(120), nullable=False)
    matched_skill_id: Mapped[Optional[int]] = mapped_column(ForeignKey("skills.id", ondelete="SET NULL"))
    is_verified_match: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    application: Mapped[Application] = relationship(back_populates="required_skills")
    matched_skill: Mapped[Optional[Skill]] = relationship()


class Interview(Base, TimestampMixin):
    __tablename__ = "interviews"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    application_id: Mapped[int] = mapped_column(
        ForeignKey("applications.id", ondelete="CASCADE"), nullable=False
    )
    round_name: Mapped[str] = mapped_column(String(120), nullable=False)
    scheduled_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    outcome: Mapped[str] = mapped_column(String(40), default="scheduled", nullable=False)
    notes: Mapped[Optional[str]] = mapped_column(Text)

    application: Mapped[Application] = relationship(back_populates="interviews")


class Task(Base, TimestampMixin):
    __tablename__ = "tasks"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    title: Mapped[str] = mapped_column(String(300), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text)
    due_date: Mapped[Optional[date]] = mapped_column(Date)
    status: Mapped[str] = mapped_column(String(30), default="open", nullable=False)
    priority: Mapped[str] = mapped_column(String(20), default="medium", nullable=False)
    related_application_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("applications.id", ondelete="SET NULL")
    )
    related_project_id: Mapped[Optional[int]] = mapped_column(ForeignKey("projects.id", ondelete="SET NULL"))
    is_sample: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)


class ActivityLog(Base):
    __tablename__ = "activity_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    action: Mapped[str] = mapped_column(String(50), nullable=False)
    entity_type: Mapped[str] = mapped_column(String(50), nullable=False)
    entity_id: Mapped[Optional[int]] = mapped_column(Integer)
    details: Mapped[Optional[str]] = mapped_column(String(500))
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), nullable=False)


class SchemaMeta(Base):
    __tablename__ = "schema_meta"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    schema_version: Mapped[str] = mapped_column(String(20), nullable=False)
    applied_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), nullable=False)
