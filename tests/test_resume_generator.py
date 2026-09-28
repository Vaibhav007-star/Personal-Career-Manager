from __future__ import annotations

import io
from docx import Document
from pypdf import PdfReader

from database.models import Profile, Project, Skill
from services.resume_generator import ResumeGenerator


def test_resume_generation_docx_and_pdf():
    profile = Profile(
        full_name="Vaibhav",
        headline="Aspiring Data Scientist",
        email="vaibhav@example.com",
        phone="+91 9876543210",
        github_url="https://github.com/vaibhav007-star",
        summary="Passionate about building data science applications and machine learning models.",
    )
    skill1 = Skill(name="Python", category="technical", verified=True)
    skill2 = Skill(name="SQL", category="technical", verified=True)
    skill3 = Skill(name="Power BI", category="tool", verified=True)

    project = Project(
        title="Predictive Sales Analysis",
        description="Built predictive model achieving 88% precision.",
        outcomes="Identified top 3 revenue leakages.",
        github_url="https://github.com/vaibhav007-star/sales",
        is_public=True,
    )

    generator = ResumeGenerator(
        profile=profile,
        skills=[skill1, skill2, skill3],
        projects=[project],
        education=[],
        experience=[],
        certificates=[],
        role_type="Data Analyst",
    )

    docx_bytes = generator.generate_docx()
    assert len(docx_bytes) > 1000
    doc = Document(io.BytesIO(docx_bytes))
    full_doc_text = "\n".join(p.text for p in doc.paragraphs)
    assert "Vaibhav" in full_doc_text
    assert "Predictive Sales Analysis" in full_doc_text
    assert "Python" in full_doc_text

    pdf_bytes = generator.generate_pdf()
    assert len(pdf_bytes) > 1000
    reader = PdfReader(io.BytesIO(pdf_bytes))
    assert len(reader.pages) >= 1
    pdf_text = "".join(page.extract_text() for page in reader.pages)
    assert "Vaibhav" in pdf_text
    assert "Predictive Sales Analysis" in pdf_text


def test_public_portfolio_redaction():
    profile = Profile(
        full_name="Vaibhav",
        headline="Aspiring Data Scientist",
        email="private.email@example.com",
        phone="+91 9876543210",
        github_url="https://github.com/vaibhav007-star",
        include_email_in_public_export=False,
    )
    skill = Skill(name="Python", verified=True)
    project = Project(title="Public Portfolio Project", is_public=True)

    generator = ResumeGenerator(
        profile=profile,
        skills=[skill],
        projects=[project],
        education=[],
        experience=[],
        certificates=[],
    )

    md = generator.generate_public_portfolio_markdown()
    assert "+91 9876543210" not in md
    assert "private.email@example.com" not in md
    assert "vaibhav007-star" in md
    assert "Public Portfolio Project" in md
