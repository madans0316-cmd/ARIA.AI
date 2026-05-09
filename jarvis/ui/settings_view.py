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
            st.error("🔴 Speech-to-text not available")
            st.code("pip install SpeechRecognition>=3.10.0", language="bash")
        else:
            st.success("🟢 Speech-to-text available")
            
        st.session_state["voice_input_enabled"] = st.toggle(
            "🎤 Voice Input (microphone → text)",
            value=st.session_state.get("voice_input_enabled", False),
            disabled=not stt_ok,
            help="Click the 🎙️ button in chat to record your voice"
        )

        if not tts_ok:
            st.error("🔴 Text-to-speech not available")
            st.code("pip install pyttsx3>=2.90", language="bash")
        else:
            st.success("🟢 Text-to-speech available")
            
        st.session_state["voice_output_enabled"] = st.toggle(
            "🔊 Voice Output (Jarvis speaks replies)",
            value=st.session_state.get("voice_output_enabled", False),
            disabled=not tts_ok,
            help="Jarvis will speak all responses aloud"
        )

        if tts_ok:
            st.session_state["tts_engine"] = st.radio(
                "TTS Engine",
                ["pyttsx3 (offline, fast)", "gtts (online, better quality)"],
                index=0 if st.session_state.get("tts_engine", "pyttsx3") == "pyttsx3" else 1,
            ).split(" ")[0]
        
        # ── Voice Diagnostics ─────────────────────────────────────────────
        with st.expander("🔍 Voice Diagnostics"):
            diag = voice.get_diagnostics()
            
            cols = st.columns(2)
            with cols[0]:
                st.metric("STT Available", "✅" if diag["stt_available"] else "❌")
                st.metric("TTS (pyttsx3)", "✅" if diag["tts_pyttsx3_available"] else "❌")
            with cols[1]:
                st.metric("TTS (gTTS)", "✅" if diag["tts_gtts_available"] else "❌")
                st.metric("Microphones", diag.get("mic_count", "?"))
            
            st.markdown("**Test Voice Features:**")
            col1, col2 = st.columns(2)
            
            with col1:
                if st.button("🎤 Test Microphone", disabled=not stt_ok):
                    with st.spinner("Listening... speak now!"):
                        result = voice.listen(timeout=5)
                    if result:
                        st.success(f"Heard: *{result}*")
                    else:
                        st.warning("Could not detect speech")
            
            with col2:
                if st.button("🔊 Test Speaker", disabled=not tts_ok):
                    with st.spinner("Speaking..."):
                        voice.speak("Hello! Jarvis voice system is working perfectly.")
                    st.success("Audio played!")
            
            st.info("💡 **Tip:** If voice features aren't working, check the diagnostic info above and see [VOICE_SETUP_GUIDE.md](VOICE_SETUP_GUIDE.md)")

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
