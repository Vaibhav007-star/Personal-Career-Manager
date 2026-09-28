"""Fictional sample records covering every single page and feature.

Includes: Profile, Skills, Education, Experience, Certificates, Projects,
Project Assets, Project Technologies, GitHub Repos, Applications,
Job Descriptions, Required Skills, Interview Rounds, Tasks, and Activity Logs.

All records are marked is_sample=True and can be cleanly purged with one click in Settings.
"""

from __future__ import annotations

from datetime import date, datetime, timedelta
import json

from sqlalchemy import delete, select

from database.crud import (
    add_project_asset,
    create_application,
    create_certificate,
    create_education,
    create_experience,
    create_interview,
    create_project,
    create_task,
    get_or_create_skill,
    get_profile,
    log_activity,
    set_application_required_skills,
    set_project_technologies,
    upsert_github_repository,
    upsert_job_description,
    upsert_profile,
)
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
    Skill,
    Task,
)
from database.session import session_scope

SAMPLE_NOTICE = (
    "FICTIONAL DEMONSTRATION SAMPLE DATA. "
    "Designed to showcase all dashboard charts, skill-gap analysis, and resume generation. "
    "Can be purged with 1 click in Settings."
)


def seed_sample_data(force: bool = False) -> None:
    """Populates complete working sample data across all models."""
    with session_scope() as session:
        # Check if already seeded
        profile = get_profile(session)
        if profile and not profile.is_sample and not force:
            return

        # 1. Profile
        upsert_profile(
            session,
            {
                "full_name": "Alex Rivera (FICTIONAL DEMO)",
                "headline": "Aspiring Data Scientist & AI Enthusiast | Python, SQL, Machine Learning",
                "email": "alex.rivera.demo@example.com",
                "phone": "+1 (555) 019-2834",
                "location": "Seattle, WA",
                "github_username": "alexrivera-ds",
                "github_url": "https://github.com/demo-user",
                "linkedin_url": "https://linkedin.com/in/demo-user",
                "portfolio_url": "https://alexrivera-demo.dev",
                "summary": (
                    "Results-driven computer science student specializing in predictive modeling, "
                    "exploratory data analysis, and scalable machine learning workflows. Seeking a 6-month "
                    "internship in Data Science, Data Analytics, or AI/ML."
                ),
                "target_roles": "Data Scientist Intern, Data Analyst Intern, AI/ML Intern",
                "include_email_in_public_export": True,
                "is_sample": True,
            },
        )

        # 2. Comprehensive Skills Catalog (Technical, Tool, Analytical, Soft Skills)
        sample_skills_data = [
            ("Python", "technical", "advanced", True),
            ("SQL", "technical", "advanced", True),
            ("Pandas", "technical", "advanced", True),
            ("NumPy", "technical", "intermediate", True),
            ("Scikit-Learn", "technical", "advanced", True),
            ("PyTorch", "technical", "intermediate", True),
            ("Machine Learning", "technical", "advanced", True),
            ("Deep Learning", "technical", "intermediate", False),
            ("Natural Language Processing", "technical", "intermediate", False),
            ("Statistics", "technical", "advanced", True),
            ("PostgreSQL", "technical", "intermediate", True),
            ("Power BI", "tool", "advanced", True),
            ("Excel", "tool", "advanced", True),
            ("Tableau", "tool", "intermediate", False),
            ("Docker", "tool", "beginner", False),
            ("Git", "tool", "advanced", True),
            ("A/B Testing", "analytical", "intermediate", False),
            ("Exploratory Data Analysis", "analytical", "advanced", True),
            ("Data Visualization", "analytical", "advanced", True),
            ("Technical Communication", "soft_skill", "advanced", True),
        ]

        skills_dict: dict[str, Skill] = {}
        for name, cat, prof, ver in sample_skills_data:
            s = get_or_create_skill(
                session,
                name=name,
                category=cat,
                proficiency=prof,
                verified=ver,
                source="sample",
                is_sample=True,
            )
            skills_dict[name] = s

        # 3. Education
        if session.scalar(select(Education).where(Education.is_sample.is_(True))) is None:
            session.add(
                Education(
                    institution="State University of Technology (DEMO)",
                    degree="Bachelor of Science",
                    field_of_study="Computer Science & Data Analytics",
                    start_date=date(2022, 9, 1),
                    end_date=date(2026, 6, 15),
                    currently_enrolled=True,
                    grade="3.88 / 4.0",
                    description=(
                        "Relevant Coursework: Data Structures, Applied Statistics, Deep Learning, "
                        "Relational Database Systems, Machine Learning Systems."
                    ),
                    is_sample=True,
                )
            )

        # 4. Experience
        if session.scalar(select(Experience).where(Experience.is_sample.is_(True))) is None:
            session.add(
                Experience(
                    organization="Metro Health Analytics (DEMO)",
                    title="Data Analytics Intern",
                    location="Remote",
                    start_date=date(2025, 5, 1),
                    end_date=date(2025, 8, 30),
                    currently_working=False,
                    experience_type="internship",
                    description=(
                        "Developed automated clinical KPI dashboards using SQL and Power BI. "
                        "Optimized complex PostgreSQL queries, cutting report delivery latency by 42%. "
                        "Presented weekly cohort analysis to medical directors."
                    ),
                    is_sample=True,
                )
            )
            session.add(
                Experience(
                    organization="University AI Research Lab (DEMO)",
                    title="Undergraduate Research Assistant",
                    location="Seattle, WA",
                    start_date=date(2025, 9, 1),
                    currently_working=True,
                    experience_type="research",
                    description=(
                        "Investigating transformer-based NLP models for clinical notes classification. "
                        "Constructed data preprocessing pipelines using Pandas, NumPy, and PyTorch."
                    ),
                    is_sample=True,
                )
            )

        # 5. Certificates
        cert1 = session.scalar(select(Certificate).where(Certificate.name == "Google Data Analytics Professional Certificate"))
        if not cert1:
            cert1 = create_certificate(
                session,
                {
                    "name": "Google Data Analytics Professional Certificate",
                    "issuer": "Google / Coursera",
                    "issue_date": date(2024, 11, 10),
                    "credential_id": "GOOG-DA-98214",
                    "credential_url": "https://coursera.org/verify/demo-cert",
                    "verification_status": "verified",
                    "notes": "Verified completion of 8-course data analytics suite.",
                    "is_sample": True,
                },
            )

        cert2 = session.scalar(select(Certificate).where(Certificate.name == "AWS Certified Cloud Practitioner"))
        if not cert2:
            cert2 = create_certificate(
                session,
                {
                    "name": "AWS Certified Cloud Practitioner",
                    "issuer": "Amazon Web Services",
                    "issue_date": date(2025, 4, 15),
                    "expiry_date": date(2028, 4, 15),
                    "credential_id": "AWS-CCP-44219",
                    "credential_url": "https://aws.amazon.com/verification/demo",
                    "verification_status": "verified",
                    "is_sample": True,
                },
            )

        cert3 = session.scalar(select(Certificate).where(Certificate.name == "Deep Learning Specialization"))
        if not cert3:
            cert3 = create_certificate(
                session,
                {
                    "name": "Deep Learning Specialization",
                    "issuer": "DeepLearning.AI",
                    "issue_date": date(2025, 7, 20),
                    "verification_status": "verified",
                    "is_sample": True,
                },
            )

        # 6. Projects & Project Assets
        existing_proj = session.scalar(select(Project).where(Project.title.like("Customer Churn%")))
        if not existing_proj:
            p1 = create_project(
                session,
                {
                    "title": "Customer Churn Prediction & Retention Engine",
                    "description": (
                        "End-to-end machine learning system predicting subscriber churn with 89% ROC-AUC. "
                        "Features modular data ingestion, automated feature engineering, and a live Streamlit dashboard."
                    ),
                    "role": "Lead ML Developer",
                    "status": "completed",
                    "start_date": date(2025, 8, 1),
                    "end_date": date(2025, 10, 15),
                    "github_url": "https://github.com/demo-user/customer-churn-engine",
                    "live_demo_url": "https://churn-simulator.demo.app",
                    "dataset_url": "https://kaggle.com/datasets/demo/telco-churn",
                    "report_url": "https://demo-user.github.io/churn-report.html",
                    "outcomes": "Identified top 3 risk factors driving churn; model achieves 88% precision on high-value customers.",
                    "is_public": True,
                    "is_sample": True,
                    "allow_duplicate": True,
                },
                skill_names=["Python", "SQL", "Pandas", "Scikit-Learn", "Machine Learning"],
            )
            add_project_asset(session, p1.id, "demo", "Interactive Streamlit App", "https://churn-simulator.demo.app")
            add_project_asset(session, p1.id, "dataset", "Telco Customer Churn Dataset", "https://kaggle.com/datasets/demo/telco-churn")
            add_project_asset(session, p1.id, "report", "Executive Summary Presentation", "https://demo-user.github.io/churn-report.pdf")

        existing_proj2 = session.scalar(select(Project).where(Project.title.like("E-Commerce Executive Sales%")))
        if not existing_proj2:
            p2 = create_project(
                session,
                {
                    "title": "E-Commerce Executive Sales & KPI Dashboard",
                    "description": (
                        "Interactive Power BI and SQL dashboard tracking revenue, Customer Acquisition Cost (CAC), "
                        "and regional sales metrics across 250,000+ transaction rows."
                    ),
                    "role": "Data Analyst",
                    "status": "completed",
                    "start_date": date(2025, 11, 1),
                    "end_date": date(2026, 1, 10),
                    "github_url": "https://github.com/demo-user/retail-analytics-dashboard",
                    "outcomes": "Automated monthly reporting pipeline, saving 6 hours per month of manual reporting.",
                    "is_public": True,
                    "is_sample": True,
                    "allow_duplicate": True,
                },
                skill_names=["SQL", "Power BI", "Excel", "PostgreSQL", "Data Visualization"],
            )
            add_project_asset(session, p2.id, "screenshot", "Executive Dashboard Overview", "https://demo-user.github.io/dashboard-preview.png")

        existing_proj3 = session.scalar(select(Project).where(Project.title.like("Healthcare Clinical Trial Sentiment%")))
        if not existing_proj3:
            p3 = create_project(
                session,
                {
                    "title": "Healthcare Clinical Trial Sentiment & Adverse Event NLP",
                    "description": (
                        "Fine-tuned transformer architectures for sentiment classification and automated adverse event "
                        "detection from patient feedback surveys."
                    ),
                    "role": "NLP Researcher",
                    "status": "in_progress",
                    "start_date": date(2026, 1, 15),
                    "github_url": "https://github.com/demo-user/clinical-nlp-sentiment",
                    "outcomes": "Attained 91.5% micro-F1 score on multi-label adverse symptom classification benchmark.",
                    "is_public": True,
                    "is_sample": True,
                    "allow_duplicate": True,
                },
                skill_names=["Python", "PyTorch", "Natural Language Processing", "Deep Learning"],
            )

        # 7. GitHub Synced Repositories
        upsert_github_repository(
            session,
            {
                "github_id": 88001,
                "name": "customer-churn-engine",
                "full_name": "demo-user/customer-churn-engine",
                "description": "Customer churn predictor using Scikit-Learn and Streamlit",
                "html_url": "https://github.com/demo-user/customer-churn-engine",
                "language": "Python",
                "topics_json": json.dumps(["machine-learning", "scikit-learn", "churn", "streamlit"]),
                "stars": 24,
                "forks": 6,
                "is_private": False,
                "is_fork": False,
                "pushed_at": datetime.now() - timedelta(days=5),
            },
        )
        upsert_github_repository(
            session,
            {
                "github_id": 88002,
                "name": "retail-analytics-dashboard",
                "full_name": "demo-user/retail-analytics-dashboard",
                "description": "SQL and Power BI analytics dashboard for e-commerce transactions",
                "html_url": "https://github.com/demo-user/retail-analytics-dashboard",
                "language": "SQL",
                "topics_json": json.dumps(["powerbi", "sql", "dashboard", "analytics"]),
                "stars": 16,
                "forks": 3,
                "is_private": False,
                "is_fork": False,
                "pushed_at": datetime.now() - timedelta(days=12),
            },
        )
        upsert_github_repository(
            session,
            {
                "github_id": 88003,
                "name": "clinical-nlp-sentiment",
                "full_name": "demo-user/clinical-nlp-sentiment",
                "description": "Clinical text classification using PyTorch and HuggingFace transformers",
                "html_url": "https://github.com/demo-user/clinical-nlp-sentiment",
                "language": "Python",
                "topics_json": json.dumps(["pytorch", "nlp", "transformers", "healthcare"]),
                "stars": 38,
                "forks": 11,
                "is_private": False,
                "is_fork": False,
                "pushed_at": datetime.now() - timedelta(days=2),
            },
        )

        # 8. Internship Placement Applications & Skill-Gap Analysis
        app1 = session.scalar(select(Application).where(Application.company == "Stripe (DEMO)"))
        if not app1:
            app1 = create_application(
                session,
                {
                    "company": "Stripe (DEMO)",
                    "role": "Data Scientist Intern (6-Month)",
                    "status": "interview",
                    "source": "University Career Fair",
                    "application_url": "https://stripe.com/jobs/demo-intern",
                    "applied_date": date.today() - timedelta(days=20),
                    "deadline": date.today() + timedelta(days=15),
                    "follow_up_date": date.today() + timedelta(days=3),
                    "notes": "Spoke with hiring manager at university booth. Highlight customer churn modeling experience.",
                    "raw_job_description": (
                        "Requirements: Strong proficiency in Python, SQL, Statistics, and Scikit-Learn. "
                        "Experience with A/B Testing, Machine Learning, and Exploratory Data Analysis."
                    ),
                    "is_sample": True,
                },
            )
            set_application_required_skills(
                session,
                app1.id,
                ["Python", "SQL", "Statistics", "Scikit-Learn", "A/B Testing", "Machine Learning"],
            )

        app2 = session.scalar(select(Application).where(Application.company == "Spotify (DEMO)"))
        if not app2:
            app2 = create_application(
                session,
                {
                    "company": "Spotify (DEMO)",
                    "role": "Data Analyst Intern",
                    "status": "oa",
                    "source": "LinkedIn",
                    "application_url": "https://spotify.com/jobs/demo-intern",
                    "applied_date": date.today() - timedelta(days=10),
                    "deadline": date.today() + timedelta(days=7),
                    "follow_up_date": date.today() + timedelta(days=5),
                    "notes": "Online Assessment (OA) link received. 3 SQL queries and 1 data interpretation question.",
                    "raw_job_description": "Proficiency in SQL, Power BI, Excel, Tableau, and Data Visualization.",
                    "is_sample": True,
                },
            )
            set_application_required_skills(
                session,
                app2.id,
                ["SQL", "Power BI", "Excel", "Tableau", "Data Visualization"],
            )

        app3 = session.scalar(select(Application).where(Application.company == "Anthropic (DEMO)"))
        if not app3:
            app3 = create_application(
                session,
                {
                    "company": "Anthropic (DEMO)",
                    "role": "AI / ML Research Intern",
                    "status": "applied",
                    "source": "Direct Career Portal",
                    "application_url": "https://anthropic.com/careers/demo",
                    "applied_date": date.today() - timedelta(days=4),
                    "deadline": date.today() + timedelta(days=25),
                    "notes": "Submitted tailored AI/ML resume featuring Clinical NLP project.",
                    "raw_job_description": "Strong PyTorch, Deep Learning, Natural Language Processing, and Docker knowledge.",
                    "is_sample": True,
                },
            )
            set_application_required_skills(
                session,
                app3.id,
                ["PyTorch", "Deep Learning", "Natural Language Processing", "Docker", "Python"],
            )

        app4 = session.scalar(select(Application).where(Application.company == "Amazon (DEMO)"))
        if not app4:
            app4 = create_application(
                session,
                {
                    "company": "Amazon (DEMO)",
                    "role": "Business Intelligence Engineer Intern",
                    "status": "offer",
                    "source": "Referral",
                    "applied_date": date.today() - timedelta(days=45),
                    "notes": "Offer letter received for 6-month term! Reviewing compensation & term dates.",
                    "is_sample": True,
                },
            )

        # 9. Interview Rounds
        if app1 and not session.scalar(select(Interview).where(Interview.application_id == app1.id)):
            create_interview(
                session,
                app1.id,
                {
                    "round_name": "Technical Screen (SQL & Algorithmic Problem Solving)",
                    "scheduled_at": datetime.now() + timedelta(days=2, hours=4),
                    "outcome": "scheduled",
                    "notes": "Focus on complex SQL window functions, self-joins, and Python dictionary manipulations.",
                },
            )
            create_interview(
                session,
                app1.id,
                {
                    "round_name": "Machine Learning Deep Dive & System Design",
                    "scheduled_at": datetime.now() + timedelta(days=7, hours=2),
                    "outcome": "scheduled",
                    "notes": "Walk through customer churn architecture, feature selection rationale, and metric tradeoffs.",
                },
            )

        # 10. Placement Tasks & Reminders
        if not session.scalar(select(Task).where(Task.is_sample.is_(True))):
            create_task(
                session,
                {
                    "title": "Complete Spotify SQL Online Assessment",
                    "description": "Finish 3 SQL challenge problems and 1 statistical analysis scenario.",
                    "due_date": date.today() + timedelta(days=4),
                    "priority": "high",
                    "status": "open",
                    "related_application_id": app2.id if app2 else None,
                    "is_sample": True,
                },
            )
            create_task(
                session,
                {
                    "title": "Review SQL Window Functions & LeetCode Hard Patterns",
                    "description": "Practice ROW_NUMBER, DENSE_RANK, and LAG/LEAD for Stripe technical interview.",
                    "due_date": date.today() + timedelta(days=2),
                    "priority": "high",
                    "status": "open",
                    "related_application_id": app1.id if app1 else None,
                    "is_sample": True,
                },
            )
            create_task(
                session,
                {
                    "title": "Export Tailored Data Analyst DOCX Resume for Fall Career Fair",
                    "description": "Generate resume emphasizing Power BI, SQL, and Excel achievements.",
                    "due_date": date.today() + timedelta(days=6),
                    "priority": "medium",
                    "status": "open",
                    "is_sample": True,
                },
            )

        # 11. Activity Logs
        log_activity(session, "seed", "sample_data", None, "Loaded comprehensive multi-module demonstration dataset")


if __name__ == "__main__":
    seed_sample_data(force=True)
    print("[SUCCESS] Comprehensive demonstration sample data loaded across all modules!")
    print("Open http://127.0.0.1:8501 to explore all working features.")
