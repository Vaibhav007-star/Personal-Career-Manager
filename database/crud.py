"""CRUD helpers for all models. All queries use bound parameters via SQLAlchemy ORM."""

from __future__ import annotations

from datetime import date, datetime
import json

from sqlalchemy import Select, delete, func, inspect as sa_inspect, or_, select
from sqlalchemy.orm import Session, selectinload

from database.models import (
    ActivityLog,
    Application,
    ApplicationRequiredSkill,
    Certificate,
    Education,
    Experience,
    GithubRepository,
    Interview,
    JobDescription,
    Profile,
    Project,
    ProjectAsset,
    ProjectCertificate,
    ProjectGithubLink,
    ProjectTechnology,
    SchemaMeta,
    Skill,
    Task,
)
from utils.validation import (
    ValidationError,
    assert_date_order,
    optional_email,
    optional_text,
    optional_url,
    parse_date,
    require_text,
)

SCHEMA_VERSION = "1.0.0"


def _alive(obj):
    if obj is None:
        return None
    state = sa_inspect(obj)
    if state.deleted or state.was_deleted:
        return None
    return obj


def log_activity(
    session: Session,
    action: str,
    entity_type: str,
    entity_id: int | None = None,
    details: str | None = None,
) -> None:
    session.add(
        ActivityLog(
            action=action,
            entity_type=entity_type,
            entity_id=entity_id,
            details=(details or "")[:500] or None,
        )
    )


def get_or_create_schema_meta(session: Session) -> SchemaMeta:
    row = session.scalar(select(SchemaMeta).limit(1))
    if row is None:
        row = SchemaMeta(schema_version=SCHEMA_VERSION)
        session.add(row)
        session.flush()
    return row


def dashboard_counts(session: Session) -> dict[str, int]:
    def count(model) -> int:
        return int(session.scalar(select(func.count()).select_from(model)) or 0)

    open_tasks = int(
        session.scalar(select(func.count()).select_from(Task).where(Task.status == "open")) or 0
    )
    upcoming_interviews = int(
        session.scalar(select(func.count()).select_from(Interview)) or 0
    )
    return {
        "projects": count(Project),
        "skills": count(Skill),
        "certificates": count(Certificate),
        "education": count(Education),
        "experience": count(Experience),
        "github_repos": count(GithubRepository),
        "applications": count(Application),
        "interviews": upcoming_interviews,
        "tasks_open": open_tasks,
        "activity": count(ActivityLog),
    }


# ==============================================================================
# PROFILE CRUD
# ==============================================================================

def get_profile(session: Session) -> Profile | None:
    return _alive(session.scalar(select(Profile).order_by(Profile.id.asc()).limit(1)))


def upsert_profile(session: Session, payload: dict) -> Profile:
    full_name = require_text(payload.get("full_name"), "Full name", max_len=200)
    profile = get_profile(session)
    created = profile is None
    if created:
        profile = Profile(full_name=full_name)
        session.add(profile)
    profile.full_name = full_name
    if "headline" in payload:
        profile.headline = optional_text(payload.get("headline"), "Headline", 300)
    if "email" in payload:
        profile.email = optional_email(payload.get("email"))
    if "phone" in payload:
        profile.phone = optional_text(payload.get("phone"), "Phone", 50)
    if "location" in payload:
        profile.location = optional_text(payload.get("location"), "Location", 200)
    if "linkedin_url" in payload:
        profile.linkedin_url = optional_url(payload.get("linkedin_url"), "LinkedIn URL")
    if "github_username" in payload:
        profile.github_username = optional_text(payload.get("github_username"), "GitHub username", 100)
    if "github_url" in payload:
        profile.github_url = optional_url(payload.get("github_url"), "GitHub URL")
    if "portfolio_url" in payload:
        profile.portfolio_url = optional_url(payload.get("portfolio_url"), "Portfolio URL")
    if "summary" in payload:
        profile.summary = optional_text(payload.get("summary"), "Summary", 5000)
    if "target_roles" in payload:
        profile.target_roles = optional_text(payload.get("target_roles"), "Target roles", 500)
    if "include_email_in_public_export" in payload:
        profile.include_email_in_public_export = bool(payload.get("include_email_in_public_export"))
    if "is_sample" in payload:
        profile.is_sample = bool(payload["is_sample"])
    session.flush()
    log_activity(session, "create" if created else "update", "profile", profile.id, "Profile saved")
    return profile


# ==============================================================================
# SKILLS CRUD
# ==============================================================================

def list_skills(
    session: Session,
    search: str | None = None,
    category: str | None = None,
    verified_only: bool = False,
) -> list[Skill]:
    stmt: Select[tuple[Skill]] = select(Skill).order_by(Skill.category.asc(), Skill.name.asc())
    if search:
        stmt = stmt.where(Skill.name.ilike(f"%{search.strip()}%"))
    if category and category != "all":
        stmt = stmt.where(Skill.category == category)
    if verified_only:
        stmt = stmt.where(Skill.verified.is_(True))
    return list(session.scalars(stmt))


def get_skill(session: Session, skill_id: int) -> Skill | None:
    return _alive(session.get(Skill, skill_id))


def get_or_create_skill(
    session: Session,
    name: str,
    category: str = "technical",
    proficiency: str = "intermediate",
    verified: bool = False,
    source: str = "manual",
    is_sample: bool = False,
) -> Skill:
    clean = require_text(name, "Skill name", max_len=120)
    existing = session.scalar(select(Skill).where(func.lower(Skill.name) == clean.lower()))
    if existing:
        return existing
    skill = Skill(
        name=clean,
        category=category,
        proficiency=proficiency,
        verified=verified,
        source=source,
        is_sample=is_sample,
    )
    session.add(skill)
    session.flush()
    log_activity(session, "create", "skill", skill.id, clean)
    return skill


def create_skill(session: Session, payload: dict) -> Skill:
    clean = require_text(payload.get("name"), "Skill name", max_len=120)
    existing = session.scalar(select(Skill).where(func.lower(Skill.name) == clean.lower()))
    if existing:
        raise ValidationError(f"A skill named '{clean}' already exists.")
    skill = Skill(
        name=clean,
        category=payload.get("category", "technical"),
        proficiency=payload.get("proficiency", "intermediate"),
        verified=bool(payload.get("verified", False)),
        source=payload.get("source", "manual"),
        notes=optional_text(payload.get("notes"), "Notes", 1000),
        is_sample=bool(payload.get("is_sample", False)),
    )
    session.add(skill)
    session.flush()
    log_activity(session, "create", "skill", skill.id, clean)
    return skill


def update_skill(session: Session, skill_id: int, payload: dict) -> Skill:
    skill = get_skill(session, skill_id)
    if not skill:
        raise ValidationError("Skill not found.")
    name = require_text(payload.get("name"), "Skill name", 120)
    existing = session.scalar(
        select(Skill).where(func.lower(Skill.name) == name.lower(), Skill.id != skill_id)
    )
    if existing:
        raise ValidationError(f"A skill named '{name}' already exists.")
    skill.name = name
    skill.category = payload.get("category", skill.category)
    skill.proficiency = payload.get("proficiency", skill.proficiency)
    if "verified" in payload:
        skill.verified = bool(payload["verified"])
    if "source" in payload:
        skill.source = payload["source"]
    if "notes" in payload:
        skill.notes = optional_text(payload.get("notes"), "Notes", 1000)
    session.flush()
    log_activity(session, "update", "skill", skill.id, skill.name)
    return skill


def delete_skill(session: Session, skill_id: int) -> None:
    skill = get_skill(session, skill_id)
    if not skill:
        raise ValidationError("Skill not found.")
    name = skill.name
    session.delete(skill)
    session.flush()
    log_activity(session, "delete", "skill", skill_id, name)


# ==============================================================================
# PROJECTS CRUD
# ==============================================================================

def find_duplicate_projects(
    session: Session, title: str, github_url: str | None, exclude_id: int | None = None
) -> list[Project]:
    title_clean = title.strip().lower()
    stmt = select(Project)
    filters = [func.lower(Project.title) == title_clean]
    if github_url:
        filters.append(Project.github_url == github_url.strip())
    stmt = stmt.where(or_(*filters))
    if exclude_id is not None:
        stmt = stmt.where(Project.id != exclude_id)
    return list(session.scalars(stmt))


def list_projects(
    session: Session,
    search: str | None = None,
    status: str | None = None,
    sort: str = "updated_desc",
) -> list[Project]:
    stmt = (
        select(Project)
        .options(selectinload(Project.technologies).selectinload(ProjectTechnology.skill))
        .options(selectinload(Project.assets))
        .options(selectinload(Project.certificate_links).selectinload(ProjectCertificate.certificate))
        .options(selectinload(Project.github_links).selectinload(ProjectGithubLink.repository))
    )
    if search:
        like = f"%{search.strip()}%"
        stmt = stmt.where(
            or_(
                Project.title.ilike(like),
                Project.description.ilike(like),
                Project.role.ilike(like),
            )
        )
    if status and status != "all":
        stmt = stmt.where(Project.status == status)
    if sort == "title":
        stmt = stmt.order_by(Project.title.asc())
    elif sort == "status":
        stmt = stmt.order_by(Project.status.asc(), Project.title.asc())
    else:
        stmt = stmt.order_by(Project.updated_at.desc())
    return list(session.scalars(stmt).unique())


def get_project(session: Session, project_id: int) -> Project | None:
    return _alive(
        session.scalar(
            select(Project)
            .options(selectinload(Project.technologies).selectinload(ProjectTechnology.skill))
            .options(selectinload(Project.assets))
            .options(selectinload(Project.certificate_links).selectinload(ProjectCertificate.certificate))
            .options(selectinload(Project.github_links).selectinload(ProjectGithubLink.repository))
            .where(Project.id == project_id)
        )
    )


def _apply_project_fields(project: Project, payload: dict) -> None:
    project.title = require_text(payload.get("title"), "Title", max_len=300)
    project.description = optional_text(payload.get("description"), "Description", 8000)
    project.role = optional_text(payload.get("role"), "Role", 200)
    project.start_date = parse_date(payload.get("start_date"), "Start date")
    project.end_date = parse_date(payload.get("end_date"), "End date")
    assert_date_order(project.start_date, project.end_date)
    status = (payload.get("status") or "in_progress").strip()
    if status not in {"planning", "in_progress", "completed", "archived"}:
        raise ValidationError("Status is not valid.")
    project.status = status
    project.github_url = optional_url(payload.get("github_url"), "GitHub URL")
    project.live_demo_url = optional_url(payload.get("live_demo_url"), "Live demo URL")
    project.dataset_url = optional_url(payload.get("dataset_url"), "Dataset URL")
    project.report_url = optional_url(payload.get("report_url"), "Report URL")
    project.outcomes = optional_text(payload.get("outcomes"), "Outcomes", 4000)
    project.is_public = bool(payload.get("is_public", True))
    if "is_sample" in payload:
        project.is_sample = bool(payload["is_sample"])


def set_project_technologies(session: Session, project: Project, skill_names: list[str]) -> None:
    names = [require_text(n, "Technology", max_len=120) for n in skill_names if (n or "").strip()]
    unique_names = list(dict.fromkeys(names))
    session.execute(delete(ProjectTechnology).where(ProjectTechnology.project_id == project.id))
    session.flush()
    for name in unique_names:
        skill = get_or_create_skill(session, name)
        session.add(ProjectTechnology(project_id=project.id, skill_id=skill.id))
    session.flush()
    session.refresh(project)


def create_project(session: Session, payload: dict, skill_names: list[str] | None = None) -> Project:
    project = Project(title="tmp")
    _apply_project_fields(project, payload)
    duplicates = find_duplicate_projects(session, project.title, project.github_url)
    if duplicates and not payload.get("allow_duplicate"):
        raise ValidationError(
            "A similar project already exists (same title or GitHub URL). "
            "Enable 'allow duplicate' if this is intentional."
        )
    session.add(project)
    session.flush()
    if skill_names:
        set_project_technologies(session, project, skill_names)
    log_activity(session, "create", "project", project.id, project.title)
    return project


def update_project(
    session: Session,
    project_id: int,
    payload: dict,
    skill_names: list[str] | None = None,
) -> Project:
    project = get_project(session, project_id)
    if project is None:
        raise ValidationError("Project not found.")
    _apply_project_fields(project, payload)
    duplicates = find_duplicate_projects(session, project.title, project.github_url, exclude_id=project.id)
    if duplicates and not payload.get("allow_duplicate"):
        raise ValidationError(
            "A similar project already exists (same title or GitHub URL). "
            "Enable 'allow duplicate' if this is intentional."
        )
    if skill_names is not None:
        set_project_technologies(session, project, skill_names)
    log_activity(session, "update", "project", project.id, project.title)
    return project


def delete_project(session: Session, project_id: int) -> None:
    project = get_project(session, project_id)
    if project is None:
        raise ValidationError("Project not found.")
    title = project.title
    session.delete(project)
    session.flush()
    log_activity(session, "delete", "project", project_id, title)


def add_project_asset(
    session: Session,
    project_id: int,
    asset_type: str,
    label: str,
    url: str | None = None,
    local_path: str | None = None,
) -> ProjectAsset:
    project = get_project(session, project_id)
    if project is None:
        raise ValidationError("Project not found.")
    allowed = {"screenshot", "demo", "dataset", "report", "other"}
    if asset_type not in allowed:
        raise ValidationError("Asset type is not valid.")
    asset = ProjectAsset(
        project_id=project.id,
        asset_type=asset_type,
        label=require_text(label, "Label", max_len=200),
        url=optional_url(url, "Asset URL"),
        local_path=local_path,
    )
    session.add(asset)
    session.flush()
    log_activity(session, "create", "project_asset", asset.id, asset.label)
    return asset


def delete_project_asset(session: Session, asset_id: int) -> None:
    asset = session.get(ProjectAsset, asset_id)
    if asset is None:
        raise ValidationError("Asset not found.")
    session.delete(asset)
    log_activity(session, "delete", "project_asset", asset_id, None)


def link_certificate_to_project(session: Session, project_id: int, certificate_id: int) -> None:
    existing = session.scalar(
        select(ProjectCertificate).where(
            ProjectCertificate.project_id == project_id,
            ProjectCertificate.certificate_id == certificate_id,
        )
    )
    if not existing:
        session.add(ProjectCertificate(project_id=project_id, certificate_id=certificate_id))
        session.flush()


def unlink_certificate_from_project(session: Session, project_id: int, certificate_id: int) -> None:
    session.execute(
        delete(ProjectCertificate).where(
            ProjectCertificate.project_id == project_id,
            ProjectCertificate.certificate_id == certificate_id,
        )
    )
    session.flush()


# ==============================================================================
# EDUCATION CRUD
# ==============================================================================

def list_education(session: Session) -> list[Education]:
    return list(session.scalars(select(Education).order_by(Education.start_date.desc().nullslast())))


def get_education(session: Session, edu_id: int) -> Education | None:
    return _alive(session.get(Education, edu_id))


def create_education(session: Session, payload: dict) -> Education:
    inst = require_text(payload.get("institution"), "Institution", max_len=300)
    edu = Education(
        institution=inst,
        degree=optional_text(payload.get("degree"), "Degree", 200),
        field_of_study=optional_text(payload.get("field_of_study"), "Field of study", 200),
        start_date=parse_date(payload.get("start_date"), "Start date"),
        end_date=parse_date(payload.get("end_date"), "End date"),
        currently_enrolled=bool(payload.get("currently_enrolled", False)),
        grade=optional_text(payload.get("grade"), "Grade", 50),
        description=optional_text(payload.get("description"), "Description", 3000),
        is_sample=bool(payload.get("is_sample", False)),
    )
    if not edu.currently_enrolled and edu.start_date and edu.end_date:
        assert_date_order(edu.start_date, edu.end_date)
    session.add(edu)
    session.flush()
    log_activity(session, "create", "education", edu.id, edu.institution)
    return edu


def update_education(session: Session, edu_id: int, payload: dict) -> Education:
    edu = get_education(session, edu_id)
    if not edu:
        raise ValidationError("Education record not found.")
    edu.institution = require_text(payload.get("institution"), "Institution", max_len=300)
    edu.degree = optional_text(payload.get("degree"), "Degree", 200)
    edu.field_of_study = optional_text(payload.get("field_of_study"), "Field of study", 200)
    edu.start_date = parse_date(payload.get("start_date"), "Start date")
    edu.end_date = parse_date(payload.get("end_date"), "End date")
    edu.currently_enrolled = bool(payload.get("currently_enrolled", False))
    edu.grade = optional_text(payload.get("grade"), "Grade", 50)
    edu.description = optional_text(payload.get("description"), "Description", 3000)
    if not edu.currently_enrolled and edu.start_date and edu.end_date:
        assert_date_order(edu.start_date, edu.end_date)
    session.flush()
    log_activity(session, "update", "education", edu.id, edu.institution)
    return edu


def delete_education(session: Session, edu_id: int) -> None:
    edu = get_education(session, edu_id)
    if not edu:
        raise ValidationError("Education record not found.")
    inst = edu.institution
    session.delete(edu)
    session.flush()
    log_activity(session, "delete", "education", edu_id, inst)


# ==============================================================================
# EXPERIENCE CRUD
# ==============================================================================

def list_experience(session: Session) -> list[Experience]:
    return list(session.scalars(select(Experience).order_by(Experience.start_date.desc().nullslast())))


def get_experience(session: Session, exp_id: int) -> Experience | None:
    return _alive(session.get(Experience, exp_id))


def create_experience(session: Session, payload: dict) -> Experience:
    org = require_text(payload.get("organization"), "Organization", max_len=300)
    title = require_text(payload.get("title"), "Title", max_len=200)
    exp = Experience(
        organization=org,
        title=title,
        location=optional_text(payload.get("location"), "Location", 200),
        start_date=parse_date(payload.get("start_date"), "Start date"),
        end_date=parse_date(payload.get("end_date"), "End date"),
        currently_working=bool(payload.get("currently_working", False)),
        experience_type=payload.get("experience_type", "internship"),
        description=optional_text(payload.get("description"), "Description", 4000),
        is_sample=bool(payload.get("is_sample", False)),
    )
    if not exp.currently_working and exp.start_date and exp.end_date:
        assert_date_order(exp.start_date, exp.end_date)
    session.add(exp)
    session.flush()
    log_activity(session, "create", "experience", exp.id, f"{exp.title} at {exp.organization}")
    return exp


def update_experience(session: Session, exp_id: int, payload: dict) -> Experience:
    exp = get_experience(session, exp_id)
    if not exp:
        raise ValidationError("Experience record not found.")
    exp.organization = require_text(payload.get("organization"), "Organization", max_len=300)
    exp.title = require_text(payload.get("title"), "Title", max_len=200)
    exp.location = optional_text(payload.get("location"), "Location", 200)
    exp.start_date = parse_date(payload.get("start_date"), "Start date")
    exp.end_date = parse_date(payload.get("end_date"), "End date")
    exp.currently_working = bool(payload.get("currently_working", False))
    exp.experience_type = payload.get("experience_type", "internship")
    exp.description = optional_text(payload.get("description"), "Description", 4000)
    if not exp.currently_working and exp.start_date and exp.end_date:
        assert_date_order(exp.start_date, exp.end_date)
    session.flush()
    log_activity(session, "update", "experience", exp.id, f"{exp.title} at {exp.organization}")
    return exp


def delete_experience(session: Session, exp_id: int) -> None:
    exp = get_experience(session, exp_id)
    if not exp:
        raise ValidationError("Experience record not found.")
    desc = f"{exp.title} at {exp.organization}"
    session.delete(exp)
    session.flush()
    log_activity(session, "delete", "experience", exp_id, desc)


# ==============================================================================
# CERTIFICATES CRUD
# ==============================================================================

def list_certificates(session: Session) -> list[Certificate]:
    return list(session.scalars(select(Certificate).order_by(Certificate.issue_date.desc().nullslast())))


def get_certificate(session: Session, cert_id: int) -> Certificate | None:
    return _alive(
        session.scalar(
            select(Certificate)
            .options(selectinload(Certificate.project_links).selectinload(ProjectCertificate.project))
            .where(Certificate.id == cert_id)
        )
    )


def create_certificate(session: Session, payload: dict) -> Certificate:
    name = require_text(payload.get("name"), "Certificate name", max_len=300)
    cert = Certificate(
        name=name,
        issuer=optional_text(payload.get("issuer"), "Issuer", 300),
        issue_date=parse_date(payload.get("issue_date"), "Issue date"),
        expiry_date=parse_date(payload.get("expiry_date"), "Expiry date"),
        credential_id=optional_text(payload.get("credential_id"), "Credential ID", 200),
        credential_url=optional_url(payload.get("credential_url"), "Credential URL"),
        verification_status=payload.get("verification_status", "unverified"),
        notes=optional_text(payload.get("notes"), "Notes", 2000),
        is_sample=bool(payload.get("is_sample", False)),
    )
    if cert.issue_date and cert.expiry_date:
        assert_date_order(cert.issue_date, cert.expiry_date)
    session.add(cert)
    session.flush()
    log_activity(session, "create", "certificate", cert.id, cert.name)
    return cert


def update_certificate(session: Session, cert_id: int, payload: dict) -> Certificate:
    cert = get_certificate(session, cert_id)
    if not cert:
        raise ValidationError("Certificate not found.")
    cert.name = require_text(payload.get("name"), "Certificate name", max_len=300)
    cert.issuer = optional_text(payload.get("issuer"), "Issuer", 300)
    cert.issue_date = parse_date(payload.get("issue_date"), "Issue date")
    cert.expiry_date = parse_date(payload.get("expiry_date"), "Expiry date")
    cert.credential_id = optional_text(payload.get("credential_id"), "Credential ID", 200)
    cert.credential_url = optional_url(payload.get("credential_url"), "Credential URL")
    cert.verification_status = payload.get("verification_status", cert.verification_status)
    cert.notes = optional_text(payload.get("notes"), "Notes", 2000)
    if cert.issue_date and cert.expiry_date:
        assert_date_order(cert.issue_date, cert.expiry_date)
    session.flush()
    log_activity(session, "update", "certificate", cert.id, cert.name)
    return cert


def delete_certificate(session: Session, cert_id: int) -> None:
    cert = get_certificate(session, cert_id)
    if not cert:
        raise ValidationError("Certificate not found.")
    name = cert.name
    session.delete(cert)
    session.flush()
    log_activity(session, "delete", "certificate", cert_id, name)


# ==============================================================================
# GITHUB REPOSITORIES CRUD
# ==============================================================================

def upsert_github_repository(session: Session, repo_dict: dict) -> GithubRepository:
    gid = int(repo_dict["github_id"])
    repo = session.scalar(select(GithubRepository).where(GithubRepository.github_id == gid))
    if not repo:
        repo = GithubRepository(github_id=gid)
        session.add(repo)
    repo.name = repo_dict["name"]
    repo.full_name = repo_dict["full_name"]
    repo.description = repo_dict.get("description")
    repo.html_url = repo_dict["html_url"]
    repo.homepage = repo_dict.get("homepage")
    repo.language = repo_dict.get("language")
    repo.topics_json = repo_dict.get("topics_json")
    repo.stars = int(repo_dict.get("stars", 0))
    repo.forks = int(repo_dict.get("forks", 0))
    repo.is_private = bool(repo_dict.get("is_private", False))
    repo.is_fork = bool(repo_dict.get("is_fork", False))
    repo.readme_content = repo_dict.get("readme_content")
    repo.pushed_at = repo_dict.get("pushed_at")
    repo.imported_at = datetime.utcnow()
    session.flush()
    log_activity(session, "sync", "github_repo", repo.id, repo.full_name)
    return repo


def list_github_repositories(session: Session) -> list[GithubRepository]:
    return list(session.scalars(select(GithubRepository).order_by(GithubRepository.pushed_at.desc().nullslast())))


def get_github_repository(session: Session, repo_id: int) -> GithubRepository | None:
    return _alive(session.get(GithubRepository, repo_id))


# ==============================================================================
# APPLICATIONS & PLACEMENT CRUD
# ==============================================================================

def list_applications(
    session: Session, status: str | None = None, search: str | None = None
) -> list[Application]:
    stmt = (
        select(Application)
        .options(
            selectinload(Application.job_description),
            selectinload(Application.interviews),
            selectinload(Application.required_skills).selectinload(ApplicationRequiredSkill.matched_skill),
        )
        .order_by(Application.created_at.desc())
    )
    if status and status != "all":
        stmt = stmt.where(Application.status == status)
    if search:
        like = f"%{search.strip()}%"
        stmt = stmt.where(or_(Application.company.ilike(like), Application.role.ilike(like)))
    return list(session.scalars(stmt).unique())


def get_application(session: Session, app_id: int) -> Application | None:
    return _alive(
        session.scalar(
            select(Application)
            .options(
                selectinload(Application.job_description),
                selectinload(Application.interviews),
                selectinload(Application.required_skills).selectinload(ApplicationRequiredSkill.matched_skill),
            )
            .where(Application.id == app_id)
        )
    )


def create_application(session: Session, payload: dict) -> Application:
    app = Application(
        company=require_text(payload.get("company"), "Company", max_len=200),
        role=require_text(payload.get("role"), "Role", max_len=200),
        source=optional_text(payload.get("source"), "Source", 120),
        application_url=optional_url(payload.get("application_url"), "Application URL"),
        deadline=parse_date(payload.get("deadline"), "Deadline"),
        applied_date=parse_date(payload.get("applied_date"), "Applied date"),
        status=payload.get("status", "wishlist"),
        follow_up_date=parse_date(payload.get("follow_up_date"), "Follow-up date"),
        notes=optional_text(payload.get("notes"), "Notes", 5000),
        is_sample=bool(payload.get("is_sample", False)),
    )
    session.add(app)
    session.flush()
    if payload.get("raw_job_description"):
        upsert_job_description(session, app.id, payload["raw_job_description"])
    log_activity(session, "create", "application", app.id, f"{app.company} - {app.role}")
    return app


def update_application(session: Session, app_id: int, payload: dict) -> Application:
    app = get_application(session, app_id)
    if not app:
        raise ValidationError("Application not found.")
    app.company = require_text(payload.get("company"), "Company", max_len=200)
    app.role = require_text(payload.get("role"), "Role", max_len=200)
    app.source = optional_text(payload.get("source"), "Source", 120)
    app.application_url = optional_url(payload.get("application_url"), "Application URL")
    app.deadline = parse_date(payload.get("deadline"), "Deadline")
    app.applied_date = parse_date(payload.get("applied_date"), "Applied date")
    app.status = payload.get("status", app.status)
    app.follow_up_date = parse_date(payload.get("follow_up_date"), "Follow-up date")
    app.notes = optional_text(payload.get("notes"), "Notes", 5000)
    if "raw_job_description" in payload:
        upsert_job_description(session, app.id, payload["raw_job_description"])
    session.flush()
    log_activity(session, "update", "application", app.id, f"{app.company} - {app.role}")
    return app


def delete_application(session: Session, app_id: int) -> None:
    app = get_application(session, app_id)
    if not app:
        raise ValidationError("Application not found.")
    name = f"{app.company} - {app.role}"
    session.delete(app)
    session.flush()
    log_activity(session, "delete", "application", app_id, name)


def upsert_job_description(session: Session, application_id: int, raw_text: str) -> JobDescription:
    jd = session.scalar(select(JobDescription).where(JobDescription.application_id == application_id))
    if not jd:
        jd = JobDescription(application_id=application_id, raw_text=raw_text or "")
        session.add(jd)
    else:
        jd.raw_text = raw_text or ""
    session.flush()
    return jd


def set_application_required_skills(
    session: Session, application_id: int, skill_names: list[str]
) -> list[ApplicationRequiredSkill]:
    session.execute(delete(ApplicationRequiredSkill).where(ApplicationRequiredSkill.application_id == application_id))
    session.flush()
    results = []
    all_user_skills = {s.name.lower(): s for s in session.scalars(select(Skill))}
    for name in skill_names:
        clean = name.strip()
        if not clean:
            continue
        matched = all_user_skills.get(clean.lower())
        req = ApplicationRequiredSkill(
            application_id=application_id,
            skill_name=clean,
            matched_skill_id=matched.id if matched else None,
            is_verified_match=bool(matched and matched.verified),
        )
        session.add(req)
        results.append(req)
    session.flush()
    return results


# ==============================================================================
# INTERVIEWS CRUD
# ==============================================================================

def create_interview(session: Session, application_id: int, payload: dict) -> Interview:
    app = get_application(session, application_id)
    if not app:
        raise ValidationError("Application not found.")
    iv = Interview(
        application_id=application_id,
        round_name=require_text(payload.get("round_name"), "Round name", max_len=120),
        scheduled_at=payload.get("scheduled_at"),
        outcome=payload.get("outcome", "scheduled"),
        notes=optional_text(payload.get("notes"), "Notes", 3000),
    )
    session.add(iv)
    session.flush()
    log_activity(session, "create", "interview", iv.id, iv.round_name)
    return iv


def update_interview(session: Session, interview_id: int, payload: dict) -> Interview:
    iv = session.get(Interview, interview_id)
    if not iv:
        raise ValidationError("Interview not found.")
    iv.round_name = require_text(payload.get("round_name"), "Round name", max_len=120)
    iv.scheduled_at = payload.get("scheduled_at", iv.scheduled_at)
    iv.outcome = payload.get("outcome", iv.outcome)
    iv.notes = optional_text(payload.get("notes"), "Notes", 3000)
    session.flush()
    log_activity(session, "update", "interview", iv.id, iv.round_name)
    return iv


def delete_interview(session: Session, interview_id: int) -> None:
    iv = session.get(Interview, interview_id)
    if not iv:
        raise ValidationError("Interview not found.")
    session.delete(iv)
    session.flush()
    log_activity(session, "delete", "interview", interview_id, None)


# ==============================================================================
# TASKS CRUD
# ==============================================================================

def list_tasks(session: Session, status: str | None = None) -> list[Task]:
    stmt = select(Task).order_by(Task.due_date.asc().nullslast(), Task.created_at.desc())
    if status and status != "all":
        stmt = stmt.where(Task.status == status)
    return list(session.scalars(stmt))


def get_task(session: Session, task_id: int) -> Task | None:
    return _alive(session.get(Task, task_id))


def create_task(session: Session, payload: dict) -> Task:
    task = Task(
        title=require_text(payload.get("title"), "Task title", max_len=300),
        description=optional_text(payload.get("description"), "Description", 3000),
        due_date=parse_date(payload.get("due_date"), "Due date"),
        status=payload.get("status", "open"),
        priority=payload.get("priority", "medium"),
        related_application_id=payload.get("related_application_id"),
        related_project_id=payload.get("related_project_id"),
        is_sample=bool(payload.get("is_sample", False)),
    )
    session.add(task)
    session.flush()
    log_activity(session, "create", "task", task.id, task.title)
    return task


def update_task(session: Session, task_id: int, payload: dict) -> Task:
    task = get_task(session, task_id)
    if not task:
        raise ValidationError("Task not found.")
    task.title = require_text(payload.get("title"), "Task title", max_len=300)
    task.description = optional_text(payload.get("description"), "Description", 3000)
    task.due_date = parse_date(payload.get("due_date"), "Due date")
    task.status = payload.get("status", task.status)
    task.priority = payload.get("priority", task.priority)
    task.related_application_id = payload.get("related_application_id", task.related_application_id)
    task.related_project_id = payload.get("related_project_id", task.related_project_id)
    session.flush()
    log_activity(session, "update", "task", task.id, task.title)
    return task


def delete_task(session: Session, task_id: int) -> None:
    task = get_task(session, task_id)
    if not task:
        raise ValidationError("Task not found.")
    session.delete(task)
    session.flush()
    log_activity(session, "delete", "task", task_id, None)


# ==============================================================================
# REPORTING & UTILITIES
# ==============================================================================

def recent_activity(session: Session, limit: int = 12) -> list[ActivityLog]:
    stmt = select(ActivityLog).order_by(ActivityLog.created_at.desc()).limit(limit)
    return list(session.scalars(stmt))


def projects_by_status(session: Session) -> dict[str, int]:
    rows = session.execute(select(Project.status, func.count()).group_by(Project.status)).all()
    return {status: int(n) for status, n in rows}


def applications_by_status(session: Session) -> dict[str, int]:
    rows = session.execute(select(Application.status, func.count()).group_by(Application.status)).all()
    return {status: int(n) for status, n in rows}


def delete_sample_records(session: Session) -> int:
    total = 0
    for model in (Project, Skill, Profile, Education, Experience, Certificate, Application, Task):
        rows = list(session.scalars(select(model).where(model.is_sample.is_(True))))
        total += len(rows)
        for row in rows:
            session.delete(row)
    session.flush()
    if total:
        log_activity(session, "delete", "sample_data", None, f"Removed {total} fictional sample records")
    return total
