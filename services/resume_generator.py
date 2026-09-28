"""ATS-Friendly Resume and Public Portfolio Generator.

Generates:
1. Editable ATS-compliant DOCX resumes.
2. Clean ATS-compliant PDF resumes via ReportLab.
3. Tailored versions for Data Analyst, Data Scientist, and AI/ML internships.
4. Privacy-respecting Public Portfolio exports (redacts phone, unshared email, private notes).

Never invents achievements or exaggerates experience.
"""

from __future__ import annotations

import io
import json
from pathlib import Path
from typing import Any

from docx import Document
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, HRFlowable

from database.models import Certificate, Education, Experience, Profile, Project, Skill
from utils.paths import EXPORTS_DIR


ROLE_TARGETS = {
    "Data Analyst": {
        "summary_focus": "Aspiring Data Analyst with proven foundation in SQL, Excel, Power BI, and exploratory data analysis.",
        "preferred_skills": ["SQL", "Excel", "Power BI", "Pandas", "Tableau", "Data Analysis", "Data Visualization"],
    },
    "Data Scientist": {
        "summary_focus": "Data Science candidate focused on machine learning pipelines, predictive modeling, statistical analysis, and Python.",
        "preferred_skills": ["Python", "Pandas", "NumPy", "Scikit-Learn", "Machine Learning", "Statistics", "SQL"],
    },
    "AI/ML Intern": {
        "summary_focus": "AI/ML engineering candidate specializing in deep learning architectures, neural networks, PyTorch, and NLP.",
        "preferred_skills": ["Python", "PyTorch", "TensorFlow", "Deep Learning", "Artificial Intelligence", "NLP", "Git"],
    },
}


class ResumeGenerator:
    def __init__(
        self,
        profile: Profile | None,
        skills: list[Skill],
        projects: list[Project],
        education: list[Education],
        experience: list[Experience],
        certificates: list[Certificate],
        role_type: str = "Data Analyst",
    ):
        self.profile = profile
        self.skills = skills
        self.projects = projects
        self.education = education
        self.experience = experience
        self.certificates = certificates
        self.role_type = role_type
        self.role_config = ROLE_TARGETS.get(role_type, ROLE_TARGETS["Data Analyst"])

    def generate_docx(self) -> bytes:
        """Generate single-column, ATS-friendly Word document."""
        doc = Document()
        
        # Set normal 0.75-inch margins
        for section in doc.sections:
            section.top_margin = Inches(0.75)
            section.bottom_margin = Inches(0.75)
            section.left_margin = Inches(0.75)
            section.right_margin = Inches(0.75)

        # Header: Name & Contact
        name = self.profile.full_name if self.profile else "Candidate Name"
        title_p = doc.add_paragraph()
        title_p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        title_run = title_p.add_run(name)
        title_run.font.name = "Arial"
        title_run.font.size = Pt(18)
        title_run.font.bold = True

        # Contact line
        contact_parts = []
        if self.profile:
            if self.profile.email:
                contact_parts.append(self.profile.email)
            if self.profile.phone:
                contact_parts.append(self.profile.phone)
            if self.profile.location:
                contact_parts.append(self.profile.location)
            if self.profile.github_url:
                contact_parts.append(self.profile.github_url)
            if self.profile.linkedin_url:
                contact_parts.append(self.profile.linkedin_url)

        contact_p = doc.add_paragraph(" | ".join(contact_parts))
        contact_p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        contact_p.style.font.size = Pt(9.5)
        contact_p.style.font.name = "Arial"

        def add_heading(text: str):
            p = doc.add_paragraph()
            p.paragraph_format.space_before = Pt(12)
            p.paragraph_format.space_after = Pt(4)
            run = p.add_run(text.upper())
            run.font.name = "Arial"
            run.font.size = Pt(12)
            run.font.bold = True
            run.font.color.rgb = RGBColor(30, 30, 30)

        # Summary
        add_heading("Professional Summary")
        summary_text = (
            self.profile.summary
            if (self.profile and self.profile.summary and not self.profile.is_sample)
            else self.role_config["summary_focus"]
        )
        p_sum = doc.add_paragraph(summary_text)
        p_sum.style.font.name = "Arial"
        p_sum.style.font.size = Pt(10)

        # Skills
        add_heading("Technical Skills")
        sorted_skills = sorted(
            self.skills,
            key=lambda s: (s.name not in self.role_config["preferred_skills"], not s.verified, s.name),
        )
        tech_skills = [s.name for s in sorted_skills if s.category == "technical"]
        tool_skills = [s.name for s in sorted_skills if s.category == "tool"]
        other_skills = [s.name for s in sorted_skills if s.category not in {"technical", "tool"}]

        if tech_skills:
            p = doc.add_paragraph()
            p.add_run("Programming & Frameworks: ").bold = True
            p.add_run(", ".join(tech_skills))
            p.style.font.name = "Arial"
            p.style.font.size = Pt(10)

        if tool_skills:
            p = doc.add_paragraph()
            p.add_run("Tools & Platforms: ").bold = True
            p.add_run(", ".join(tool_skills))
            p.style.font.name = "Arial"
            p.style.font.size = Pt(10)

        if other_skills:
            p = doc.add_paragraph()
            p.add_run("Core Competencies: ").bold = True
            p.add_run(", ".join(other_skills))
            p.style.font.name = "Arial"
            p.style.font.size = Pt(10)

        # Projects
        if self.projects:
            add_heading("Key Projects")
            for proj in self.projects:
                proj_p = doc.add_paragraph()
                proj_run = proj_p.add_run(proj.title)
                proj_run.bold = True
                
                tech_names = [t.skill.name for t in proj.technologies if t.skill]
                if tech_names:
                    proj_p.add_run(f" | Tools: {', '.join(tech_names)}").italic = True
                
                if proj.github_url:
                    proj_p.add_run(f" | Link: {proj.github_url}")

                if proj.description:
                    desc_p = doc.add_paragraph(proj.description, style="List Bullet")
                    desc_p.style.font.name = "Arial"
                    desc_p.style.font.size = Pt(9.5)
                if proj.outcomes:
                    out_p = doc.add_paragraph(f"Outcomes: {proj.outcomes}", style="List Bullet")
                    out_p.style.font.name = "Arial"
                    out_p.style.font.size = Pt(9.5)

        # Experience
        if self.experience:
            add_heading("Experience")
            for exp in self.experience:
                exp_p = doc.add_paragraph()
                exp_p.add_run(f"{exp.title} — {exp.organization}").bold = True
                date_str = f"{exp.start_date or 'Start'} to {'Present' if exp.currently_working else (exp.end_date or 'End')}"
                exp_p.add_run(f" ({date_str})").italic = True
                if exp.description:
                    d_p = doc.add_paragraph(exp.description, style="List Bullet")
                    d_p.style.font.name = "Arial"
                    d_p.style.font.size = Pt(9.5)

        # Education
        if self.education:
            add_heading("Education")
            for edu in self.education:
                edu_p = doc.add_paragraph()
                edu_p.add_run(f"{edu.institution}").bold = True
                if edu.degree or edu.field_of_study:
                    deg = f" — {edu.degree or ''} in {edu.field_of_study or ''}".strip()
                    edu_p.add_run(deg)
                if edu.grade:
                    edu_p.add_run(f" (CGPA/Grade: {edu.grade})")

        # Certifications
        if self.certificates:
            add_heading("Certifications")
            for cert in self.certificates:
                cert_p = doc.add_paragraph(style="List Bullet")
                cert_p.add_run(cert.name).bold = True
                if cert.issuer:
                    cert_p.add_run(f" — {cert.issuer}")
                if cert.credential_url:
                    cert_p.add_run(f" ({cert.credential_url})")

        bio = io.BytesIO()
        doc.save(bio)
        return bio.getvalue()

    def generate_pdf(self) -> bytes:
        """Generate single-column, clean ATS-compliant PDF using ReportLab."""
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(
            buffer,
            pagesize=letter,
            leftMargin=40,
            rightMargin=40,
            topMargin=40,
            bottomMargin=40,
        )
        styles = getSampleStyleSheet()

        title_style = ParagraphStyle(
            "DocTitle",
            parent=styles["Normal"],
            fontName="Helvetica-Bold",
            fontSize=16,
            leading=20,
            alignment=1,  # Center
            textColor=colors.HexColor("#1A1A1A"),
        )
        contact_style = ParagraphStyle(
            "ContactStyle",
            parent=styles["Normal"],
            fontName="Helvetica",
            fontSize=9,
            leading=12,
            alignment=1,  # Center
            textColor=colors.HexColor("#4A4A4A"),
        )
        h1_style = ParagraphStyle(
            "Heading1Style",
            parent=styles["Normal"],
            fontName="Helvetica-Bold",
            fontSize=11,
            leading=15,
            spaceBefore=8,
            spaceAfter=3,
            textColor=colors.HexColor("#1A365D"),
        )
        body_style = ParagraphStyle(
            "BodyTextStyle",
            parent=styles["Normal"],
            fontName="Helvetica",
            fontSize=9.5,
            leading=13,
            textColor=colors.HexColor("#222222"),
        )
        bullet_style = ParagraphStyle(
            "BulletStyle",
            parent=body_style,
            leftIndent=15,
            firstLineIndent=-10,
        )

        elements = []

        # Name
        name = self.profile.full_name if self.profile else "Candidate Name"
        elements.append(Paragraph(name, title_style))

        # Contact Info
        contact_parts = []
        if self.profile:
            if self.profile.email:
                contact_parts.append(self.profile.email)
            if self.profile.phone:
                contact_parts.append(self.profile.phone)
            if self.profile.location:
                contact_parts.append(self.profile.location)
            if self.profile.github_url:
                contact_parts.append(self.profile.github_url)

        elements.append(Paragraph(" | ".join(contact_parts), contact_style))
        elements.append(Spacer(1, 10))
        elements.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor("#CCCCCC"), spaceBefore=2, spaceAfter=8))

        # Summary
        elements.append(Paragraph("PROFESSIONAL SUMMARY", h1_style))
        summary_text = (
            self.profile.summary
            if (self.profile and self.profile.summary and not self.profile.is_sample)
            else self.role_config["summary_focus"]
        )
        elements.append(Paragraph(summary_text, body_style))
        elements.append(Spacer(1, 6))

        # Skills
        elements.append(Paragraph("TECHNICAL SKILLS", h1_style))
        sorted_skills = sorted(
            self.skills,
            key=lambda s: (s.name not in self.role_config["preferred_skills"], not s.verified, s.name),
        )
        tech_skills = [s.name for s in sorted_skills if s.category == "technical"]
        tool_skills = [s.name for s in sorted_skills if s.category == "tool"]

        if tech_skills:
            elements.append(Paragraph(f"<b>Technical Skills:</b> {', '.join(tech_skills)}", body_style))
        if tool_skills:
            elements.append(Paragraph(f"<b>Tools & Platforms:</b> {', '.join(tool_skills)}", body_style))
        elements.append(Spacer(1, 6))

        # Projects
        if self.projects:
            elements.append(Paragraph("KEY PROJECTS", h1_style))
            for proj in self.projects:
                tech_names = [t.skill.name for t in proj.technologies if t.skill]
                tools_str = f" | <i>Tools: {', '.join(tech_names)}</i>" if tech_names else ""
                elements.append(Paragraph(f"<b>{proj.title}</b>{tools_str}", body_style))
                if proj.description:
                    elements.append(Paragraph(f"&bull; {proj.description}", bullet_style))
                if proj.outcomes:
                    elements.append(Paragraph(f"&bull; <b>Outcome:</b> {proj.outcomes}", bullet_style))
                elements.append(Spacer(1, 4))

        # Experience
        if self.experience:
            elements.append(Paragraph("EXPERIENCE", h1_style))
            for exp in self.experience:
                date_str = f"{exp.start_date or ''} – {'Present' if exp.currently_working else (exp.end_date or '')}"
                elements.append(Paragraph(f"<b>{exp.title}</b> — {exp.organization} (<i>{date_str}</i>)", body_style))
                if exp.description:
                    elements.append(Paragraph(f"&bull; {exp.description}", bullet_style))
                elements.append(Spacer(1, 4))

        # Education
        if self.education:
            elements.append(Paragraph("EDUCATION", h1_style))
            for edu in self.education:
                deg = f" — {edu.degree or ''} in {edu.field_of_study or ''}".strip()
                gr = f" (Grade: {edu.grade})" if edu.grade else ""
                elements.append(Paragraph(f"<b>{edu.institution}</b>{deg}{gr}", body_style))
                elements.append(Spacer(1, 3))

        # Certificates
        if self.certificates:
            elements.append(Paragraph("CERTIFICATIONS", h1_style))
            for cert in self.certificates:
                issuer = f" — {cert.issuer}" if cert.issuer else ""
                elements.append(Paragraph(f"&bull; <b>{cert.name}</b>{issuer}", bullet_style))

        doc.build(elements)
        return buffer.getvalue()

    def generate_public_portfolio_markdown(self) -> str:
        """Export clean Markdown public portfolio redacting private information."""
        lines = []
        name = self.profile.full_name if self.profile else "Portfolio"
        lines.append(f"# {name}")
        if self.profile and self.profile.headline:
            lines.append(f"*{self.profile.headline}*\n")

        # Contact info — REDACT PHONE ALWAYS, REDACT EMAIL UNLESS OPTED IN
        links = []
        if self.profile:
            if self.profile.include_email_in_public_export and self.profile.email:
                links.append(f"Email: {self.profile.email}")
            if self.profile.github_url:
                links.append(f"[GitHub]({self.profile.github_url})")
            if self.profile.linkedin_url:
                links.append(f"[LinkedIn]({self.profile.linkedin_url})")
            if self.profile.portfolio_url:
                links.append(f"[Website]({self.profile.portfolio_url})")
        if links:
            lines.append(" | ".join(links) + "\n")

        lines.append("## Verified Skills")
        verified_skills = [s.name for s in self.skills if s.verified]
        if verified_skills:
            lines.append(", ".join(f"`{s}`" for s in verified_skills) + "\n")
        else:
            lines.append("*(Skills catalog in progress)*\n")

        lines.append("## Featured Projects")
        public_projects = [p for p in self.projects if p.is_public]
        for p in public_projects:
            lines.append(f"### {p.title}")
            if p.description:
                lines.append(p.description)
            techs = [t.skill.name for t in p.technologies if t.skill]
            if techs:
                lines.append(f"\n**Technologies:** {', '.join(techs)}")
            if p.github_url:
                lines.append(f"**Repository:** [{p.github_url}]({p.github_url})")
            if p.live_demo_url:
                lines.append(f"**Live Demo:** [{p.live_demo_url}]({p.live_demo_url})")
            if p.outcomes:
                lines.append(f"**Outcomes:** {p.outcomes}")
            lines.append("\n---")

        return "\n".join(lines)
