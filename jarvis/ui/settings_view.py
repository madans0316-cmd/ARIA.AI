"""
ui/settings_view.py
───────────────────
Settings tab: model params, system prompt, voice, UI prefs.
All changes write directly to st.session_state.
"""

from __future__ import annotations

import streamlit as st
import core.voice as voice
from core.session import _default_system_prompt


def render_settings():
    st.markdown("## ⚙️ Settings")

    # ── Model parameters ──────────────────────────────────────────────────────
    with st.expander("🧠 Model Parameters", expanded=True):
        st.session_state["temperature"] = st.slider(
            "Temperature  (creativity)",
            0.0, 1.0,
            value=float(st.session_state.get("temperature", 0.7)),
            step=0.05,
            help="Lower = more deterministic. Higher = more creative.",
        )
        st.session_state["max_tokens"] = st.slider(
            "Max tokens  (response length)",
            256, 8192,
            value=int(st.session_state.get("max_tokens", 2048)),
            step=256,
        )

    # ── System prompt ─────────────────────────────────────────────────────────
    with st.expander("📝 System Prompt"):
        new_prompt = st.text_area(
            "Jarvis's personality & instructions",
            value=st.session_state.get("system_prompt", _default_system_prompt()),
            height=200,
        )
        col1, col2 = st.columns(2)
        with col1:
            if st.button("💾 Save Prompt"):
                st.session_state["system_prompt"] = new_prompt
                st.success("Saved!")
        with col2:
            if st.button("🔄 Reset to Default"):
                st.session_state["system_prompt"] = _default_system_prompt()
                st.rerun()

    # ── Voice ─────────────────────────────────────────────────────────────────
    with st.expander("🎙️ Voice"):
        stt_ok = voice.is_stt_available()
        tts_ok = voice.is_tts_available()

        if not stt_ok:
            st.warning("Speech-to-text not available. Install: `pip install SpeechRecognition pyaudio`")
        st.session_state["voice_input_enabled"] = st.toggle(
            "🎤 Voice Input (microphone → text)",
            value=st.session_state.get("voice_input_enabled", False),
            disabled=not stt_ok,
        )

        if not tts_ok:
            st.warning("Text-to-speech not available. Install: `pip install pyttsx3`")
        st.session_state["voice_output_enabled"] = st.toggle(
            "🔊 Voice Output (Jarvis speaks replies)",
            value=st.session_state.get("voice_output_enabled", False),
            disabled=not tts_ok,
        )

        if tts_ok:
            st.session_state["tts_engine"] = st.radio(
                "TTS Engine",
                ["pyttsx3 (offline)", "gtts (online, better quality)"],
                index=0,
            ).split(" ")[0]

    # ── UI preferences ────────────────────────────────────────────────────────
    with st.expander("🎨 UI Preferences"):
        st.session_state["show_timestamps"] = st.toggle(
            "Show message timestamps",
            value=st.session_state.get("show_timestamps", False),
        )

    # ── About ─────────────────────────────────────────────────────────────────
    with st.expander("ℹ️ About Jarvis"):
        st.markdown(
            """
            **Jarvis AI Assistant v1.0**

            | Component | Technology |
            |-----------|------------|
            | LLM backend | [Ollama](https://ollama.ai) |
            | Interface | Streamlit |
            | Database | SQLite |
            | Document RAG | PyMuPDF + embeddings |
            | STT | SpeechRecognition |
            | TTS | pyttsx3 / gTTS |
            | Language | Python 3.10+ |

            100 % open-source. Runs fully offline (except gTTS).
            """
        )
