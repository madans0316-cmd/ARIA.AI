"""
╔══════════════════════════════════════════════╗
║         JARVIS AI ASSISTANT - v1.0           ║
║     Your Personal Offline AI Companion       ║
╚══════════════════════════════════════════════╝

Entry point: run with  →  streamlit run app.py
"""

import streamlit as st
import sys
import os

# ── Make sure sub-packages are importable ─────────────────────────────────────
sys.path.insert(0, os.path.dirname(__file__))

from ui.layout import render_sidebar, render_header
from ui.chat_view import render_chat
from ui.file_view import render_file_upload
from ui.settings_view import render_settings
from core.session import init_session

# ── Page config ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Jarvis AI Assistant",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Load custom CSS ───────────────────────────────────────────────────────────
with open(os.path.join(os.path.dirname(__file__), "assets", "style.css"), encoding='utf-8') as f:
    st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

# ── Initialise session state on first load ────────────────────────────────────
init_session()

# ── Sidebar ───────────────────────────────────────────────────────────────────
active_tab = render_sidebar()

# ── Main area ─────────────────────────────────────────────────────────────────
render_header()

if active_tab == "💬 Chat":
    render_chat()
elif active_tab == "📄 Documents":
    render_file_upload()
elif active_tab == "⚙️ Settings":
    render_settings()
