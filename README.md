# Personal Career Management System (CareerOS)

[![Python 3.12](https://img.shields.io/badge/Python-3.12-3776AB?logo=python&logoColor=white)](https://www.python.org/)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.32+-FF4B4B?logo=streamlit&logoColor=white)](https://streamlit.io/)
[![SQLite](https://img.shields.io/badge/Database-SQLite%203-003B57?logo=sqlite&logoColor=white)](https://www.sqlite.org/)
[![SQLAlchemy](https://img.shields.io/badge/ORM-SQLAlchemy%202.0-D71F00)](https://www.sqlalchemy.org/)
[![Security: Local-First](https://img.shields.io/badge/Security-Local--First%20%26%20Private-success)](https://github.com/)
[![Tests: Passing](https://img.shields.io/badge/Tests-36%20Passed-brightgreen)](https://github.com/)

A local-first, privacy-respecting career command center engineered specifically for students, graduates, and aspiring professionals preparing for **Data Science**, **Data Analytics**, and **AI/ML** internships and placements.

All personal records, resumes, certificates, and job applications stay strictly on your local machine. No third-party AI APIs, no paid cloud subscriptions, and no external tracking.

---

## Key Highlights & Modules

- **📊 Executive Dashboard (`1_Dashboard.py`)**  
  Real-time KPI metrics, placement funnel status, skills distribution charts, upcoming interview reminders, and active tasks.

- **👤 Profile Manager (`2_Profile.py`)**  
  Single-source personal record: headline, biography, target tracks (Data Analyst, Data Scientist, AI/ML Engineer), contact links, and custom portfolio URLs.

- **💼 Project Portfolio Hub (`3_Projects.py`)**  
  Rich project catalog with technology tagging, dataset links, live demos, technical write-ups, GitHub repository associations, and certificates.

- **🛠️ Skills & Certifications Hub (`4_Skills_Certificates.py`)**  
  Categorized taxonomy (Technical, Analytical, Tools, Soft Skills) with explicit verification tracking and credential validation URLs.

- **🎓 Education & Experience (`5_Experience_Education.py`)**  
  Academic degree tracking (degrees, institutions, GPAs, coursework) and work/internship histories.

- **🐙 Official GitHub REST Synchronization (`6_GitHub_Sync.py`)**  
  Direct, rate-limit aware public repository synchronization using official GitHub APIs (and optional fine-grained personal access token support).

- **📄 Document Import Center (`7_Document_Import.py`)**  
  Automated document parsing for **PDF, DOCX, CSV, XLSX, and Markdown** files with a human-in-the-loop review screen before saving to your database.

- **🎯 Internship & Placement Tracker (`8_Applications_Tracker.py`)**  
  Complete lifecycle tracking (Applied, Online Assessment, Technical Round, HR Interview, Offer, Rejected) featuring **automated Skill-Gap Analysis** comparing job descriptions directly against your verified skills.

- **📝 ATS-Friendly Resume & Portfolio Generator (`9_Resume_Generator.py`)**  
  Generates clean, ATS-compliant **editable DOCX** and **formatted PDF** resumes tailored for Data Analyst, Data Scientist, and AI/ML tracks, alongside anonymized public portfolio exports.

- **🔐 Settings & AES-256 Encrypted Backups (`10_Settings.py`)**  
  Profile configuration, one-click fictional sample data cleanup, database health stats, and military-grade password-protected **AES-256-GCM backup and restore**.

- **⚡ Fast CLI Auto-Ingestion (`auto_import.py`)**  
  Command-line ingestion tool allowing instant automated loading of resumes, CSV skill inventories, or GitHub repositories directly into your SQLite database.

---

## Architecture

```
                            Browser (http://127.0.0.1:8501)
                                         │
                                         ▼
                      Streamlit Application (app.py + pages/)
                                         │
                 ┌───────────────────────┼────────────────────────┐
                 ▼                       ▼                        ▼
          UI Components          Business Services          File Safety
         (components/)             (services/)               (utils/)
                 │                       │                        │
                 │   ┌───────────────────┘                        │
                 ▼   ▼                                            ▼
         Database ORM Layer (database/crud.py)           Encrypted Backups
                     │                                   (AES-256-GCM)
                     ▼
           Local Relational SQLite
              (data/career.db)
```

| Layer | Path | Responsibility |
| --- | --- | --- |
| **Presentation** | `app.py`, `pages/*.py` | Responsive Streamlit UI with metric cards, Plotly charts, and forms |
| **Components** | `components/` | Reusable UI chrome (header, sidebar, status badges, metric cards) |
| **Data Layer** | `database/` | Normalized SQLAlchemy 2.0 models, migrations, CRUD, and seed routines |
| **Services** | `services/` | GitHub REST client, document parser, skill-gap engine, ATS resume generator, AES backup engine |
| **Utilities** | `utils/` | Local paths, config validation, logging with automatic token redaction, safe file paths |
| **CLI Ingestion** | `auto_import.py` | Fast command-line ingestion for resumes, spreadsheets, and GitHub |
| **Test Suite** | `tests/` | 36 automated unit & integration tests |

---

## Database Schema

Normalized relational SQLite schema managed via SQLAlchemy in `database/models.py`:

- `profile`: Singleton personal career profile.
- `education`: Academic history, degrees, GPAs, and coursework.
- `skills`: Categorized skill directory with explicit `verified` flags (never automatically assumed).
- `projects` & `project_technologies`: Portfolio projects mapped to required skills.
- `project_assets`: Links to live demos, datasets, GitHub repos, and screenshots.
- `certificates` & `project_certificates`: Industry credentials linked to projects.
- `experience`: Professional experience and internships with bullet-point responsibilities.
- `github_repositories`: Synced public repositories (stars, forks, languages, topics, README).
- `applications` & `job_descriptions`: Placement pipeline with embedded job descriptions.
- `application_required_skills`: Extracted job requirements for skill-gap scoring.
- `interviews`: Scheduled rounds, dates, interviewer notes, and outcomes.
- `tasks`: Action items, placement prep goals, deadlines, and priorities.
- `activity_logs`: Local audit trail (sanitized of sensitive tokens).

---

## Quick Start (Windows 10/11)

### Option A: Automated PowerShell Setup (Recommended)

1. Open PowerShell and navigate to the project directory:
   ```powershell
   cd path\to\personal-career-manager
   ```

2. If PowerShell script execution is restricted on your system, enable it for this process:
   ```powershell
   Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
   ```

3. Run the automated setup script:
   ```powershell
   .\setup_windows.ps1
   ```
   *This creates `.venv`, installs dependencies from `requirements.txt`, creates `.env`, creates required directories, and initializes the SQLite database.*

4. Launch the application:
   ```powershell
   python -m streamlit run app.py --server.address 127.0.0.1
   ```
   Then open **http://127.0.0.1:8501** in your browser.

---

### Option B: Manual Setup

1. **Create and activate a virtual environment (Python 3.12 recommended):**
   ```powershell
   python -m venv .venv
   .\.venv\Scripts\Activate.ps1
   ```

2. **Install dependencies:**
   ```powershell
   python -m pip install --upgrade pip
   python -m pip install -r requirements.txt
   ```

3. **Configure environment:**
   ```powershell
   Copy-Item .env.example .env
   ```

4. **Initialize database:**
   ```powershell
   python -m database.init_db
   ```

5. **(Optional) Load comprehensive demo sample data:**
   ```powershell
   python -m database.seed
   ```
   *Seeds realistic sample profile, projects, skills, certificates, applications, and interviews labeled `is_sample=True`. You can remove them at any time in **Settings**.*

6. **Start the application:**
   ```powershell
   python -m streamlit run app.py --server.address 127.0.0.1
   ```

---

## Automated CLI Ingestion (`auto_import.py`)

Quickly ingest your existing data without typing everything manually:

```powershell
# 1. Ingest your resume (PDF or DOCX)
python auto_import.py C:\Users\Username\Documents\resume.pdf

# 2. Ingest your skills inventory (CSV or XLSX)
python auto_import.py C:\Users\Username\Documents\skills.csv

# 3. Ingest your public GitHub repositories
python auto_import.py --github your-github-username
```

---

## Security, Privacy & Threat Model

1. **Local-First Binding:**  
   The application server is strictly bound to `127.0.0.1` (loopback). It will never expose ports to public networks or local area networks (`0.0.0.0`).
2. **Zero-Cloud Leakage:**  
   No user data, resumes, certificates, or notes are uploaded to any cloud service or third-party AI provider.
3. **Defense Against Secret Leaks:**  
   `.gitignore` comprehensively excludes the database (`data/career.db`), environment files (`.env`), uploaded files (`uploads/`), generated resumes (`resumes/`, `*.docx`, `*.pdf`), log files (`logs/`), and backup archives (`backups/`).
4. **Log Token Redaction:**  
   Application loggers automatically filter and redact `ghp_*`, `github_pat_*`, and `Bearer *` authorization tokens.
5. **Encrypted Backups:**  
   Full SQLite database backups can be encrypted using **AES-256-GCM** with a user-provided passphrase via `cryptography`.
6. **Local Security Disclaimer:**  
   *Local-first storage does not protect against local malware or unauthorized physical/account access to your Windows user profile. Secure your operating system user account and avoid running untrusted binaries.*

---

## Running the Automated Test Suite

The project includes a comprehensive test suite covering database models, CRUD operations, duplicate detection, document parsing, GitHub API error handling, AES encryption, and resume generation:

```powershell
.\.venv\Scripts\Activate.ps1
python -m pytest -v
```

All 36 tests execute against an in-memory SQLite database without modifying your local `data/career.db`.

---

## Project Structure

```
personal-career-manager/
├── app.py                      # Application landing page & system navigation
├── auto_import.py              # CLI automated ingestion tool
├── setup_windows.ps1           # Automated Windows setup script
├── requirements.txt            # Python dependencies
├── .env.example                # Environment variables template
├── .gitignore                  # Git privacy & secrets exclusion rules
├── README.md                   # Project documentation
│
├── pages/                      # Multi-page Streamlit application
│   ├── 1_Dashboard.py          # Metrics, funnel charts, and quick actions
│   ├── 2_Profile.py            # Personal career profile CRUD
│   ├── 3_Projects.py           # Portfolio projects, tech stack, assets
│   ├── 4_Skills_Certificates.py# Skills taxonomy & certificate manager
│   ├── 5_Experience_Education.py# Work history & academic qualifications
│   ├── 6_GitHub_Sync.py        # GitHub REST integration & repo manager
│   ├── 7_Document_Import.py    # PDF, DOCX, CSV, XLSX, MD parser & review
│   ├── 8_Applications_Tracker.py# Job tracker & automated skill-gap analysis
│   ├── 9_Resume_Generator.py   # ATS DOCX/PDF resume generator & public export
│   └── 10_Settings.py          # Backups, sample data purge, security
│
├── database/                   # Relational database layer
│   ├── models.py               # SQLAlchemy 2.0 ORM schemas
│   ├── engine.py               # SQLite engine & connection configuration
│   ├── session.py              # Scoped session context managers
│   ├── crud.py                 # Parameterized database operations
│   ├── init_db.py              # Database initialization & table creation
│   └── seed.py                 # Fictional demonstration dataset generator
│
├── services/                   # Business logic & integrations
│   ├── backup_manager.py       # AES-256-GCM encrypted backup & restore
│   ├── document_parser.py      # Resumes, certificates, and spreadsheet parsers
│   ├── github_client.py        # Official GitHub REST API client
│   ├── resume_generator.py     # ATS DOCX & PDF document synthesis
│   └── skill_gap_analyzer.py   # Job description vs. verified skills engine
│
├── components/                 # Reusable UI widgets
│   ├── badges.py               # Status & verification badges
│   ├── cards.py                # Metric & summary cards
│   ├── export_widgets.py       # Data export helper widgets
│   ├── header.py               # Page headers and status indicator
│   └── sidebar.py              # Navigation sidebar
│
├── utils/                      # Utilities & helpers
│   ├── config.py               # Application configuration & env loader
│   ├── file_safety.py          # Path traversal prevention & upload limits
│   ├── logging_config.py       # Token-redacting application logger
│   ├── paths.py                # Project paths & directory management
│   └── validation.py           # Form input validators
│
└── tests/                      # Automated test suite (36 tests)
    ├── test_backup.py          # Backup & AES-256 encryption tests
    ├── test_crud.py            # ORM CRUD & duplicate handling tests
    ├── test_document_parser.py # Document extraction tests
    ├── test_github_client.py   # GitHub API mock & error handling tests
    ├── test_resume_generator.py# DOCX & PDF generation tests
    ├── test_sample_data.py     # Sample data isolation & removal tests
    ├── test_security.py        # Token protection & path traversal tests
    └── test_skill_gap.py       # Skill-gap analysis engine tests
```

---

## License

Distributed under the MIT License. See `LICENSE` for details.
