"""
core/session.py
───────────────
Centralised Streamlit session-state bootstrap.
All default values live here so every other module
can safely read st.session_state without KeyError.
"""

import streamlit as st
from datetime import datetime


def init_session():
    """Call once at app startup to guarantee every key exists."""

    defaults = {
        # ── Chat ─────────────────────────────────────────────────────────────
        "messages": [],           # list[dict]  {role, content, timestamp}
        "conversation_id": _new_conversation_id(),

        # ── Model / config ───────────────────────────────────────────────────
        "model": "llama3.2",      # active Ollama model
        "system_prompt": _default_system_prompt(),
        "temperature": 0.7,
        "max_tokens": 2048,
        "stream": True,

        # ── Document RAG ─────────────────────────────────────────────────────
        "uploaded_docs": [],      # list of doc names already indexed
        "rag_enabled": False,     # True once at least one doc is indexed
        "doc_context": "",        # top-k retrieved chunks (injected per turn)

        # ── Voice ────────────────────────────────────────────────────────────
        "voice_input_enabled": False,
        "voice_output_enabled": False,
        "tts_engine": "pyttsx3",  # "pyttsx3" | "gtts"

        # ── UI ───────────────────────────────────────────────────────────────
        "active_tab": "💬 Chat",
        "dark_mode": True,
        "show_timestamps": False,
        "thinking": False,        # spinner flag
    }

    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


def _new_conversation_id() -> str:
    return datetime.now().strftime("conv_%Y%m%d_%H%M%S")


def _default_system_prompt() -> str:
    return (
        "You are Jarvis, a brilliant personal AI assistant running locally on the user's laptop. "
        "You are helpful, precise, and concise. You excel at:\n"
        "  • General conversation and Q&A\n"
        "  • Explaining engineering and science concepts clearly\n"
        "  • Teaching and explaining cybersecurity topics\n"
        "  • Writing, reviewing, and debugging code in any language\n"
        "  • Answering questions based on documents the user uploads\n\n"
        "Always think step-by-step for complex problems. "
        "If you are unsure, say so honestly rather than guessing."
    )
