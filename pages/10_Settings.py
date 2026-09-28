"""Settings: Privacy controls, sample data management, and encrypted backups."""

from __future__ import annotations

from pathlib import Path
import streamlit as st

from components.layout import page_setup
from database.crud import delete_sample_records, get_profile
from database.seed import seed_sample_data
from database.session import session_scope
from services.backup_service import (
    BackupError,
    InvalidPasswordError,
    create_encrypted_backup,
    restore_encrypted_backup,
)
from utils.bootstrap import bootstrap
from utils.config import get_settings
from utils.paths import BACKUPS_DIR, DATA_DIR, ENV_EXAMPLE, PROJECT_ROOT

bootstrap()
page_setup("Settings", "⚙️")

st.title("Settings & Security")
settings = get_settings()

tab_sec, tab_sample, tab_backup = st.tabs(["🔒 Privacy & Security", "🧪 Sample Data", "💾 Encrypted Backup & Restore"])

# ==============================================================================
# 1. PRIVACY & SECURITY
# ==============================================================================
with tab_sec:
    st.subheader("Local-First Security Posture")
    st.markdown(
        f"""
- **Server Binding:** The application strictly binds to `127.0.0.1:{settings.port}` so it is not accessible across your local network or WiFi.
- **Zero Third-Party Cloud Uploads:** No career documents, contact details, or credentials are sent to external cloud or AI APIs.
- **Local Storage Limitations:** Note that local storage does **not** protect against malware, spyware, or other users with access to your Windows user profile account. Keep your Windows account password protected.
- **Secrets Management:** The SQLite database, uploaded files, and `.env` file are explicitly included in `.gitignore` so they are never committed to Git or GitHub.
"""
    )

    st.markdown("---")
    st.subheader("GitHub Integration Status")
    st.write(f"Configured username: `{settings.github_username}`")
    st.write("Token status: " + ("✅ Configured (isolated in local environment)" if settings.has_github_token else "⚠️ No token (public requests only)"))
    if settings.has_github_token:
        st.caption("Your token is read from your local `.env` and is never exposed in UI inputs, logs, or exports.")

    st.markdown("---")
    st.subheader("Local Directory Paths")
    st.code(
        f"Project Root: {PROJECT_ROOT}\nData Directory: {DATA_DIR}\nBackups Directory: {BACKUPS_DIR}\nEnv Template: {ENV_EXAMPLE}",
        language="text",
    )

# ==============================================================================
# 2. SAMPLE DATA MANAGEMENT
# ==============================================================================
with tab_sample:
    st.subheader("Fictional Sample Data")
    st.caption("Load demonstration records to test the UI. All sample records are labeled FICTIONAL and can be cleanly purged.")

    c1, c2 = st.columns(2)
    if c1.button("Load Fictional Sample Data", type="secondary"):
        seed_sample_data()
        st.success("Sample data loaded. Remember to purge it before saving your real records.")
        st.rerun()

    if c2.button("🗑️ Remove All Fictional Sample Records", type="primary"):
        with session_scope() as session:
            count = delete_sample_records(session)
        st.success(f"Successfully deleted {count} fictional sample records.")
        st.rerun()

    with session_scope() as session:
        profile = get_profile(session)
    if profile:
        st.write(f"Active Profile: **{profile.full_name}**")
        if profile.is_sample:
            st.warning("⚠️ The active profile is currently marked as a fictional sample.")

# ==============================================================================
# 3. ENCRYPTED BACKUP & RESTORE
# ==============================================================================
with tab_backup:
    st.subheader("Encrypted Backup")
    st.caption(
        "Creates a password-protected `.enc` backup using standard PBKDF2 (SHA-256) and Fernet AES encryption. "
        "Your password is required to restore the database."
    )

    with st.form("create_backup_form"):
        backup_password = st.text_input("Enter Backup Password * (min 6 characters)", type="password")
        confirm_password = st.text_input("Confirm Password", type="password")
        submit_backup = st.form_submit_button("Create Encrypted Backup", type="primary")

        if submit_backup:
            if not backup_password or len(backup_password) < 6:
                st.error("Password must be at least 6 characters.")
            elif backup_password != confirm_password:
                st.error("Passwords do not match.")
            else:
                try:
                    backup_path = create_encrypted_backup(backup_password)
                    st.success(f"Encrypted backup created successfully: `{backup_path.name}`")
                    st.download_button(
                        label="⬇️ Download Encrypted Backup File",
                        data=backup_path.read_bytes(),
                        file_name=backup_path.name,
                        mime="application/octet-stream",
                    )
                except BackupError as be:
                    st.error(str(be))

    st.markdown("---")
    st.subheader("Restore from Encrypted Backup")
    st.warning("Restoring will replace your current database records with the contents of the backup file.")

    uploaded_backup = st.file_uploader("Select `.enc` backup file to restore", type=["enc"])
    restore_pass = st.text_input("Enter the password used when creating this backup", type="password", key="restore_pass")

    if uploaded_backup is not None and st.button("🔓 Decrypt and Restore Database", type="primary"):
        if not restore_pass:
            st.error("Please enter the decryption password.")
        else:
            try:
                restore_encrypted_backup(uploaded_backup.getvalue(), restore_pass)
                st.success("Database restored and verified successfully! Refreshing...")
                st.rerun()
            except InvalidPasswordError as ipe:
                st.error(f"Authentication failed: {ipe}")
            except BackupError as be:
                st.error(f"Restore error: {be}")
