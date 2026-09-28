"""Automated Career Data Ingestion CLI.

Quickly populates your Career Management System directly from the command line:
    python auto_import.py path/to/resume.pdf
    python auto_import.py path/to/skills.csv
    python auto_import.py --github vaibhav007-star
"""

from __future__ import annotations

import argparse
from pathlib import Path
import sys

from database.init_db import init_database
from database.session import session_scope
from database.crud import (
    create_application,
    create_certificate,
    create_education,
    create_experience,
    create_project,
    get_or_create_skill,
    upsert_profile,
)
from services.document_parser import DocumentParser
from services.github_client import GitHubClient


def auto_import_file(file_path: Path) -> None:
    if not file_path.exists():
        print(f"❌ Error: File '{file_path}' does not exist.")
        return

    print(f"📄 Reading '{file_path.name}'...")
    raw_bytes = file_path.read_bytes()
    parser = DocumentParser(file_path.name, raw_bytes)
    res = parser.parse()

    init_database()

    with session_scope() as session:
        # Tabular data import
        if "tabular_data" in res:
            tab = res["tabular_data"]
            dtype = tab["type"]
            recs = tab["records"]
            print(f"📊 Found spreadsheet with {len(recs)} {dtype}...")
            count = 0
            for r in recs:
                if dtype == "applications":
                    create_application(session, {
                        "company": str(r.get("company", "Company")),
                        "role": str(r.get("role", "Role")),
                        "status": str(r.get("status", "wishlist")),
                        "application_url": r.get("application_url"),
                    })
                    count += 1
                elif dtype == "skills":
                    get_or_create_skill(session, name=str(r.get("name") or r.get("skill")), category=str(r.get("category", "technical")))
                    count += 1
            print(f"✅ Successfully auto-imported {count} {dtype}!")
            return

        # Resume / Text import
        summary = []
        prof = res.get("profile", {})
        if prof.get("full_name"):
            upsert_profile(session, {
                "full_name": prof["full_name"],
                "email": prof.get("email"),
                "phone": prof.get("phone"),
                "github_username": prof.get("github_username") or "vaibhav007-star",
                "github_url": prof.get("github_url"),
                "linkedin_url": prof.get("linkedin_url"),
            })
            summary.append(f"Profile ({prof['full_name']})")

        # Skills
        skills = res.get("skills", [])
        for s in skills:
            get_or_create_skill(session, name=s["name"], category=s["category"], verified=False, source="cli_import")
        if skills:
            summary.append(f"{len(skills)} Skills")

        # Education
        edus = res.get("education", [])
        for e in edus:
            create_education(session, {
                "institution": e.get("institution") or "University",
                "degree": e.get("degree") or "Degree",
                "currently_enrolled": True,
            })
        if edus:
            summary.append(f"{len(edus)} Education")

        # Experience
        exps = res.get("experience", [])
        for x in exps:
            create_experience(session, {
                "title": x.get("title") or "Role",
                "organization": x.get("organization") or "Organization",
                "currently_working": False,
            })
        if exps:
            summary.append(f"{len(exps)} Experience")

        # Projects
        projs = res.get("projects", [])
        for p in projs:
            create_project(session, {
                "title": p.get("title") or "Project",
                "description": "Extracted from uploaded document.",
                "allow_duplicate": True,
            })
        if projs:
            summary.append(f"{len(projs)} Projects")

        print("🎉 Auto-import completed! Successfully populated:")
        for item in summary:
            print(f"   • {item}")
        print("\nOpen your Streamlit app (http://127.0.0.1:8501) to see your live data!")


def auto_import_github(username: str) -> None:
    print(f"🐙 Connecting to GitHub REST API for '{username}'...")
    init_database()
    client = GitHubClient()
    with session_scope() as session:
        result = client.sync_to_database(session, username)
        print(f"✅ Successfully synced {result['synced']} repositories for {username}!")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Auto-import career data into local system.")
    parser.add_argument("file", nargs="?", help="Path to resume (PDF, DOCX, MD) or spreadsheet (CSV, XLSX)")
    parser.add_argument("--github", help="GitHub username to sync repositories from")

    args = parser.parse_args()

    if args.github:
        auto_import_github(args.github)
    elif args.file:
        auto_import_file(Path(args.file))
    else:
        print("Usage:")
        print("  python auto_import.py path/to/my_resume.pdf")
        print("  python auto_import.py --github vaibhav007-star")
