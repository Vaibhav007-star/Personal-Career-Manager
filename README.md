# Personal Career Management System

Local-first Streamlit app for internship and placement preparation (Data Analyst, Data Scientist, AI/ML).  
**Owner GitHub username:** `vaibhav007-star`  
**Phase 1 (this folder):** architecture, SQLite schema, dashboard, profile CRUD, projects CRUD. Later phases are not implemented yet.

The app binds to `127.0.0.1` only. It does not upload your records to the cloud. **The database is not encrypted in Phase 1.** Local files do not protect you from malware or from anyone who can use your Windows account.

---

## Architecture

```
Browser (http://127.0.0.1:8501)
        │
        ▼
Streamlit UI  (app.py + pages/)     ← presentation only
        │
        ▼
components/                         ← layout, badges, export widgets
        │
        ▼
database/crud.py                    ← validation + ORM (parameterized)
        │
        ▼
SQLite file  data/career.db         ← never commit this file
```

| Layer | Role |
| --- | --- |
| `pages/` | User-facing CRUD and dashboard |
| `components/` | Shared UI chrome |
| `database/` | SQLAlchemy models, sessions, CRUD |
| `services/` | External APIs (GitHub client **not active** in Phase 1) |
| `utils/` | Paths, config, validation, logging redaction, file safety |
| `alembic/` | Schema versioning (`001_initial`) |
| `tests/` | Database, CRUD, sample-data labels, token/gitignore checks |

**Privacy defaults:** one profile row; email/phone not exported publicly unless you opt in later; GitHub tokens only from `.env`; logs redact `ghp_` / `github_pat_` / Bearer tokens.

---

## Database schema (normalized SQLite)

Implemented in `database/models.py` (relationships, unique constraints, timestamps):

- `profile` — singleton personal profile  
- `education`  
- `skills` — unique `name`; `verified` is never inferred  
- `projects` + `project_technologies` (project ↔ skill) + `project_assets`  
- `certificates` + `project_certificates`  
- `experience`  
- `github_repositories` + `project_github_links`  
- `applications` + `job_descriptions` + `application_required_skills`  
- `interviews`  
- `tasks`  
- `activity_logs` — no secrets  
- `schema_meta` — version `1.0.0`

Phase 1 UI writes **profile**, **projects**, **skills** (via project tags), and **activity_logs**. Other tables exist so later phases do not rename files.

---

## Folder map

```
personal-career-manager/
  app.py                      Home
  pages/1_Dashboard.py
  pages/2_Profile.py
  pages/3_Projects.py
  pages/4_Settings.py
  database/models.py
  database/engine.py
  database/session.py
  database/crud.py
  database/init_db.py
  database/seed.py            Fictional samples only
  alembic/                    Migrations
  components/
  services/github_client.py   Raises until Phase 2
  utils/
  tests/
  .streamlit/config.toml      address = 127.0.0.1
  .env.example
  .gitignore
  requirements.txt
  setup_windows.ps1
  README.md
  data/                       gitignored; created at runtime
```

---

## Development milestones

| Phase | Scope | Status |
| --- | --- | --- |
| **1** | Schema, dashboard, profile, projects, Windows setup, tests | **This delivery** |
| **2** | Education/skills/certs/experience CRUD, GitHub REST importer, document import + review | Wait for your confirmation |
| **3** | Internship tracker, interviews, tasks, skill-gap (verified skills only) | Not started |
| **4** | ATS DOCX/PDF resume + public portfolio export (no invented achievements) | Not started |
| **5** | Encrypted backup/restore, extra hardening, remaining tests | Not started |

---

## Windows setup (Python 3.12, PowerShell, VS Code)

Open PowerShell:

```powershell
cd C:\Users\Vaibhav\Projects\personal-career-manager

# If `python` is not recognized, use the launcher or a full path:
#   py -3.12 --version
#   & "$env:LOCALAPPDATA\Programs\Python\Python312\python.exe" --version

py -3.12 --version
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1

python -m pip install --upgrade pip
python -m pip install -r requirements.txt

Copy-Item .env.example .env
python -m database.init_db

python -m pytest -q
python -m streamlit run app.py --server.address 127.0.0.1
```

Or run `.\setup_windows.ps1` from the project folder.

If activation is blocked:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\.venv\Scripts\Activate.ps1
```

Open **http://127.0.0.1:8501**

Optional fictional UI demo (not real credentials):

```powershell
python -m database.seed
```

Remove samples later in **Settings**.

VS Code: File → Open Folder → `C:\Users\Vaibhav\Projects\personal-career-manager`, then select the `.venv` interpreter.

---

## Troubleshooting

| Symptom | What to do |
| --- | --- |
| `python` not found | Install Python 3.12 from python.org; check “Add python.exe to PATH”; reopen the terminal |
| `Activate.ps1` cannot be loaded | `Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass` |
| Streamlit not found | Confirm `(.venv)` is in the prompt; `pip install -r requirements.txt` |
| Browser opens a LAN URL | Stop the app; always pass `--server.address 127.0.0.1` (also set in `.streamlit/config.toml`) |
| `database is locked` | Close extra Streamlit processes; only one app instance |
| Page is empty | Save a profile first; empty charts are expected |
| Port 8501 in use | `python -m streamlit run app.py --server.address 127.0.0.1 --server.port 8502` |

---

## Security notes (Phase 1)

- Server address is loopback. Do not change it to `0.0.0.0`.
- `.gitignore` excludes `.env`, `*.db`, `data/`, uploads, backups, exports, resumes, certificates.
- `.env.example` has an empty `GITHUB_TOKEN`.
- Phase 1 **does not** call GitHub, document AI APIs, or encrypt backups. Settings will not claim those features work.

---

## Tests

```powershell
.\.venv\Scripts\Activate.ps1
python -m pytest -q
```

Covered now: table creation, profile/project CRUD, duplicates, sample-data labeling/removal, gitignore/env placeholders, loopback bind override, log redaction, path traversal helper.
