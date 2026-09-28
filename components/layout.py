"""Shared CSS and layout chrome."""

from __future__ import annotations

import streamlit as st

CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Source+Sans+3:wght@400;600;700&family=IBM+Plex+Sans:wght@400;500;600&display=swap');

html, body, [class*="css"]  {
  font-family: "Source Sans 3", "IBM Plex Sans", sans-serif;
}

.block-container {
  padding-top: 1.4rem;
  max-width: 1200px;
}

div[data-testid="stMetric"] {
  background: var(--secondary-background-color);
  border: 1px solid rgba(148, 163, 184, 0.35);
  border-radius: 16px;
  padding: 12px 16px;
  box-shadow: 0 8px 24px rgba(15, 23, 42, 0.04);
}

.pcm-hero {
  background: linear-gradient(135deg, #1d4ed8 0%, #0f172a 70%);
  color: #f8fafc;
  padding: 1.6rem 1.8rem;
  border-radius: 20px;
  margin-bottom: 1.2rem;
}
.pcm-hero h1 { color: #fff; margin: 0 0 0.35rem 0; font-size: 1.7rem; }
.pcm-hero p { color: #e2e8f0; margin: 0; }

.pcm-badge {
  display: inline-block;
  padding: 0.15rem 0.55rem;
  border-radius: 999px;
  font-size: 0.75rem;
  font-weight: 600;
}
.pcm-badge.ok { background: #dcfce7; color: #166534; }
.pcm-badge.warn { background: #fef3c7; color: #92400e; }
.pcm-badge.info { background: #dbeafe; color: #1e40af; }
.pcm-badge.sample { background: #fae8ff; color: #86198f; }
.pcm-badge.muted { background: #e2e8f0; color: #334155; }

.pcm-card {
  border: 1px solid rgba(148, 163, 184, 0.35);
  border-radius: 16px;
  padding: 1rem 1.1rem;
  background: var(--secondary-background-color);
  margin-bottom: 0.8rem;
}
.pcm-muted { color: #64748b; font-size: 0.92rem; }
.pcm-lock { font-size: 0.85rem; color: #475569; }
</style>
"""


def inject_css() -> None:
    st.markdown(CSS, unsafe_allow_html=True)


def page_setup(title: str, icon: str = "📌") -> None:
    st.set_page_config(
        page_title=f"{title} · Career OS",
        page_icon=icon,
        layout="wide",
        initial_sidebar_state="expanded",
    )
    inject_css()
    with st.sidebar:
        st.markdown("**Career OS**")
        st.caption("Local-first · 127.0.0.1 only")
        st.caption("Your records stay on this Windows PC. This does not protect against malware or someone using your Windows account.")
