"""Small reusable Streamlit fragments."""

from __future__ import annotations

import pandas as pd
import streamlit as st


def sample_badge(is_sample: bool) -> None:
    if is_sample:
        st.markdown(
            '<span class="pcm-badge sample">FICTIONAL SAMPLE</span>',
            unsafe_allow_html=True,
        )


def status_badge(status: str) -> str:
    mapping = {
        "completed": "ok",
        "in_progress": "info",
        "planning": "warn",
        "archived": "muted",
        "open": "info",
        "wishlist": "muted",
        "applied": "info",
        "interview": "warn",
        "offer": "ok",
        "rejected": "muted",
    }
    kind = mapping.get(status, "muted")
    label = status.replace("_", " ").title()
    return f'<span class="pcm-badge {kind}">{label}</span>'


def empty_state(title: str, body: str) -> None:
    st.markdown(
        f"""
        <div class="pcm-card">
          <h3>{title}</h3>
          <p class="pcm-muted">{body}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )


def dataframe_download(df: pd.DataFrame, filename: str, label: str) -> None:
    csv = df.to_csv(index=False).encode("utf-8")
    st.download_button(label, data=csv, file_name=filename, mime="text/csv")
    buffer_xlsx = df.copy()
    from io import BytesIO

    bio = BytesIO()
    buffer_xlsx.to_excel(bio, index=False)
    st.download_button(
        label.replace("CSV", "Excel"),
        data=bio.getvalue(),
        file_name=filename.replace(".csv", ".xlsx"),
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )
