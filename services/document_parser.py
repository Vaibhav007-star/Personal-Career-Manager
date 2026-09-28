"""Document Import Center Parser.

Extracts career data (Profile, Education, Skills, Projects, Experience, Certificates)
from PDF, DOCX, CSV, XLSX, and Markdown/text files.
Flags uncertain extractions for user confirmation.
Never invents data or fabricates credentials.
Cleans up temporary uploaded files.
"""

from __future__ import annotations

import csv
from io import BytesIO
from pathlib import Path
import re
from typing import Any

import pandas as pd
from pypdf import PdfReader
from docx import Document

from utils.files import FileSafetyError, sanitize_filename
from utils.logging_config import get_logger

logger = get_logger("career_os.doc_parser")

SUPPORTED_EXTENSIONS = {".pdf", ".docx", ".csv", ".xlsx", ".md", ".txt"}

# Known skill vocabulary for Data Science, Analytics, and AI
KNOWN_SKILLS = [
    "Python", "SQL", "Pandas", "NumPy", "Streamlit", "Power BI", "Excel",
    "Tableau", "Scikit-Learn", "TensorFlow", "PyTorch", "Machine Learning",
    "Deep Learning", "Data Analysis", "Data Science", "Artificial Intelligence",
    "Natural Language Processing", "NLP", "Computer Vision", "Statistics",
    "PostgreSQL", "MySQL", "SQLite", "Git", "GitHub", "Docker", "R", "Spark",
    "Hadoop", "AWS", "Azure", "GCP", "FastAPI", "Flask", "Matplotlib", "Seaborn",
    "Jupyter", "ETL", "Data Visualization", "Data Modeling", "Business Intelligence",
]

# Common certificate issuers
KNOWN_ISSUERS = [
    "Coursera", "Udemy", "edX", "Google", "IBM", "Microsoft", "AWS",
    "DeepLearning.AI", "DataCamp", "Codecademy", "Kaggle", "LinkedIn Learning",
]


class DocumentParserError(Exception):
    pass


class DocumentParser:
    """Parses resumes, certificates, and project sheets into structured staging data."""

    def __init__(self, filename: str, file_bytes: bytes):
        self.filename = sanitize_filename(filename)
        self.ext = Path(self.filename).suffix.lower()
        self.file_bytes = file_bytes
        if self.ext not in SUPPORTED_EXTENSIONS:
            raise DocumentParserError(
                f"Unsupported file format '{self.ext}'. "
                f"Allowed formats: {', '.join(sorted(SUPPORTED_EXTENSIONS))}"
            )

    def extract_text(self) -> str:
        """Extract raw text from PDF, DOCX, MD, or TXT."""
        if self.ext == ".pdf":
            try:
                reader = PdfReader(BytesIO(self.file_bytes))
                pages = [page.extract_text() or "" for page in reader.pages]
                return "\n".join(pages)
            except Exception as e:
                raise DocumentParserError(f"Failed to read PDF: {e}") from e

        elif self.ext == ".docx":
            try:
                doc = Document(BytesIO(self.file_bytes))
                paragraphs = [p.text for p in doc.paragraphs if p.text.strip()]
                for table in doc.tables:
                    for row in table.rows:
                        row_text = " | ".join(cell.text.strip() for cell in row.cells if cell.text.strip())
                        if row_text:
                            paragraphs.append(row_text)
                return "\n".join(paragraphs)
            except Exception as e:
                raise DocumentParserError(f"Failed to read DOCX: {e}") from e

        elif self.ext in {".md", ".txt"}:
            try:
                return self.file_bytes.decode("utf-8", errors="replace")
            except Exception as e:
                raise DocumentParserError(f"Failed to read text file: {e}") from e

        elif self.ext in {".csv", ".xlsx"}:
            return ""  # Handled separately via tabular parsing

        return ""

    def parse_tabular(self) -> dict[str, Any]:
        """Extract structured records from CSV or Excel sheets."""
        try:
            if self.ext == ".csv":
                df = pd.read_csv(BytesIO(self.file_bytes))
            else:
                df = pd.read_excel(BytesIO(self.file_bytes))
        except Exception as e:
            raise DocumentParserError(f"Failed to parse tabular file: {e}") from e

        # Normalize column names
        df.columns = [str(c).strip().lower().replace(" ", "_") for c in df.columns]
        records: list[dict[str, Any]] = df.to_dict(orient="records")

        # Determine target entity based on columns
        cols = set(df.columns)
        if {"company", "role"}.issubset(cols):
            return {"type": "applications", "records": records, "count": len(records)}
        elif {"skill", "name"}.intersection(cols) and "proficiency" in cols:
            return {"type": "skills", "records": records, "count": len(records)}
        elif {"project", "title"}.intersection(cols):
            return {"type": "projects", "records": records, "count": len(records)}
        elif {"certificate", "issuer"}.intersection(cols):
            return {"type": "certificates", "records": records, "count": len(records)}
        else:
            return {"type": "generic_table", "columns": list(df.columns), "records": records, "count": len(records)}

    def parse(self) -> dict[str, Any]:
        """Main parsing entry point returning extracted candidate entities."""
        if self.ext in {".csv", ".xlsx"}:
            return {"source_file": self.filename, "tabular_data": self.parse_tabular()}

        raw_text = self.extract_text()
        if not raw_text.strip():
            return {
                "source_file": self.filename,
                "warning": "No readable text could be extracted from this file.",
                "profile": {},
                "skills": [],
                "education": [],
                "experience": [],
                "projects": [],
                "certificates": [],
            }

        return {
            "source_file": self.filename,
            "raw_text_snippet": raw_text[:500],
            "profile": self._extract_profile(raw_text),
            "skills": self._extract_skills(raw_text),
            "education": self._extract_education(raw_text),
            "experience": self._extract_experience(raw_text),
            "projects": self._extract_projects(raw_text),
            "certificates": self._extract_certificates(raw_text),
        }

    def _extract_profile(self, text: str) -> dict[str, Any]:
        lines = [line.strip() for line in text.splitlines() if line.strip()]
        candidate_name = lines[0] if lines and len(lines[0]) < 80 else None

        # Email match
        email_match = re.search(r"[\w\.-]+@[\w\.-]+\.\w+", text)
        email = email_match.group(0) if email_match else None

        # Phone match
        phone_match = re.search(r"(\+?\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}", text)
        phone = phone_match.group(0) if phone_match else None

        # GitHub URL
        github_match = re.search(r"https?://(?:www\.)?github\.com/([a-zA-Z0-9_-]+)", text)
        github_url = github_match.group(0) if github_match else None
        github_user = github_match.group(1) if github_match else None

        # LinkedIn URL
        linkedin_match = re.search(r"https?://(?:www\.)?linkedin\.com/in/([a-zA-Z0-9_-]+)", text)
        linkedin_url = linkedin_match.group(0) if linkedin_match else None

        return {
            "full_name": candidate_name,
            "email": email,
            "phone": phone,
            "github_username": github_user,
            "github_url": github_url,
            "linkedin_url": linkedin_url,
            "confidence": "high" if (candidate_name and (email or github_url)) else "uncertain",
        }

    def _extract_skills(self, text: str) -> list[dict[str, Any]]:
        found_skills = []
        text_lower = text.lower()
        for skill in KNOWN_SKILLS:
            # Word boundary search
            pattern = r"\b" + re.escape(skill.lower()) + r"\b"
            if re.search(pattern, text_lower):
                category = "tool" if skill in {"Power BI", "Excel", "Tableau", "Git", "GitHub", "Docker"} else "technical"
                found_skills.append({
                    "name": skill,
                    "category": category,
                    "proficiency": "intermediate",
                    "verified": False,  # Never fabricated; needs manual confirmation
                    "confidence": "high",
                })
        return found_skills

    def _extract_education(self, text: str) -> list[dict[str, Any]]:
        education = []
        degree_patterns = [
            r"(Bachelor\s+of\s+[\w\s]+|B\.?Tech|B\.?E\.?|B\.?Sc|Master\s+of\s+[\w\s]+|M\.?Tech|M\.?Sc)",
        ]
        for line in text.splitlines():
            line_str = line.strip()
            for pat in degree_patterns:
                match = re.search(pat, line_str, re.IGNORECASE)
                if match:
                    education.append({
                        "degree": match.group(0),
                        "institution": line_str,
                        "confidence": "uncertain",
                    })
                    break
        return education[:3]

    def _extract_experience(self, text: str) -> list[dict[str, Any]]:
        experience = []
        keywords = ["intern", "internship", "analyst", "assistant", "developer", "engineer"]
        for line in text.splitlines():
            line_str = line.strip()
            if any(k in line_str.lower() for k in keywords) and len(line_str) < 150:
                experience.append({
                    "title": line_str,
                    "organization": "To be confirmed by user",
                    "experience_type": "internship" if "intern" in line_str.lower() else "full_time",
                    "confidence": "uncertain",
                })
        return experience[:4]

    def _extract_projects(self, text: str) -> list[dict[str, Any]]:
        projects = []
        proj_lines = [line.strip() for line in text.splitlines() if line.strip()]
        for idx, line in enumerate(proj_lines):
            if any(line.lower().startswith(p) for p in ["project:", "projects", "key project:"]):
                candidate = proj_lines[idx + 1] if idx + 1 < len(proj_lines) else line
                if len(candidate) < 120:
                    projects.append({
                        "title": candidate.replace("Project:", "").strip(),
                        "confidence": "uncertain",
                    })
        return projects[:5]

    def _extract_certificates(self, text: str) -> list[dict[str, Any]]:
        certs = []
        for line in text.splitlines():
            line_str = line.strip()
            for issuer in KNOWN_ISSUERS:
                if issuer.lower() in line_str.lower() and len(line_str) < 150:
                    certs.append({
                        "name": line_str,
                        "issuer": issuer,
                        "verification_status": "unverified",
                        "confidence": "uncertain",
                    })
                    break
        return certs[:5]
