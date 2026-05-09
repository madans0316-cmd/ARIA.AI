"""
ui/chat_view.py
───────────────
Main chat UI:
  • Renders message history with role-based styling
  • Streams token-by-token responses from Ollama
  • Injects RAG context when documents are indexed
  • Optional voice input (mic button) and voice output (auto-speak)
  • Saves every message to SQLite
"""

from __future__ import annotations

import streamlit as st
from datetime import datetime

from core.llm import chat_stream, is_ollama_running
from core.database import save_message
from core.rag import retrieve
import core.voice as voice


# ── Helpers ───────────────────────────────────────────────────────────────────

def _ts() -> str:
    return datetime.now().strftime("%H:%M")


def _render_message(role: str, content: str, timestamp: str = ""):
    avatar = "⚡" if role == "assistant" else "👤"
    css_class = "msg-assistant" if role == "assistant" else "msg-user"
    ts_html = f'<span class="msg-ts">{timestamp}</span>' if timestamp else ""
    st.markdown(
        f"""
        <div class="chat-message {css_class}">
            <div class="msg-avatar">{avatar}</div>
            <div class="msg-body">
                {ts_html}
                <div class="msg-content">{_format_content(content)}</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def _format_content(text: str) -> str:
    """
    Minimal safe HTML: convert fenced code blocks to <pre><code> tags.
    Everything else stays as-is (Streamlit's st.markdown handles it better,
    but we're inside an HTML block here so we escape carefully).
    """
    import re, html
    # We'll render raw markdown via st.markdown later for assistant messages
    return html.escape(text).replace("\n", "<br>")


# ── Streaming writer ──────────────────────────────────────────────────────────

def _stream_response(messages: list[dict]) -> str:
    """
    Stream tokens into a st.empty() placeholder.
    Returns the full assembled response text.
    """
    system = st.session_state["system_prompt"]

    # Inject RAG context if enabled
    if st.session_state.get("rag_enabled"):
        last_user = next(
            (m["content"] for m in reversed(messages) if m["role"] == "user"),
            "",
        )
        ctx = retrieve(last_user, top_k=4)
        if ctx:
            system = system + "\n\n" + ctx

    placeholder = st.empty()
    full_text = ""

    with placeholder.container():
        # Use a code-friendly text area while streaming
        response_area = st.empty()

    for token in chat_stream(
        messages=messages,
        model=st.session_state["model"],
        system=system,
        temperature=st.session_state["temperature"],
        max_tokens=st.session_state["max_tokens"],
    ):
        full_text += token
        response_area.markdown(
            f'<div class="streaming-bubble">⚡ {full_text}▌</div>',
            unsafe_allow_html=True,
        )

    # Replace streaming bubble with final rendered markdown
    placeholder.empty()
    return full_text


# ── Main render ───────────────────────────────────────────────────────────────

def render_chat():
    messages: list[dict] = st.session_state["messages"]
    conv_id  = st.session_state["conversation_id"]
    show_ts  = st.session_state.get("show_timestamps", False)

    # ── History ───────────────────────────────────────────────────────────────
    chat_container = st.container()
    with chat_container:
        if not messages:
            _render_welcome()
        else:
            for msg in messages:
                ts = msg.get("timestamp", "") if show_ts else ""
                with st.chat_message(msg["role"], avatar="⚡" if msg["role"] == "assistant" else "👤"):
                    st.markdown(msg["content"])
                    if ts:
                        st.caption(ts)

    # ── Input row ─────────────────────────────────────────────────────────────
    col_input, col_mic = st.columns([10, 1])

    with col_input:
        user_input = st.chat_input(
            "Ask Jarvis anything… (Shift+Enter for new line)",
            key="chat_input",
        )

    with col_mic:
        voice_clicked = False
        if voice.is_stt_available() and st.session_state.get("voice_input_enabled"):
            voice_clicked = st.button("🎙️", help="Click to speak", use_container_width=True)

    # Voice input takes priority
    if voice_clicked:
        with st.spinner("🎙️ Listening…"):
            spoken = voice.listen()
        if spoken:
            user_input = spoken
            st.info(f"🎙️ You said: *{spoken}*")
        else:
            st.warning("Couldn't hear you. Try again.")

    # ── Process user message ──────────────────────────────────────────────────
    if user_input:
        ollama_ok = is_ollama_running()
        
        # Demo mode if Ollama not running (for testing voice features)
        if not ollama_ok:
            st.warning("⚠️ **Ollama is not running.** Using demo mode to test voice features.")
            st.info("To enable full chat: `ollama serve` in a terminal. See [VOICE_SETUP_GUIDE.md](VOICE_SETUP_GUIDE.md)")
            demo_reply = _get_demo_reply(user_input)
        else:
            demo_reply = None

        # Append user message
        user_msg = {"role": "user", "content": user_input, "timestamp": _ts()}
        st.session_state["messages"].append(user_msg)
        
        if ollama_ok:
            save_message(conv_id, "user", user_input, st.session_state["model"])

        with st.chat_message("user", avatar="👤"):
            st.markdown(user_input)

        # Stream assistant reply
        with st.chat_message("assistant", avatar="⚡"):
            with st.spinner("Thinking…"):
                if demo_reply:
                    # Demo mode response (no Ollama)
                    reply = demo_reply
                    st.markdown(reply)
                else:
                    # Normal LLM response (Ollama running)
                    # Build message list without timestamp keys for LLM
                    llm_msgs = [
                        {"role": m["role"], "content": m["content"]}
                        for m in st.session_state["messages"]
                    ]
                    reply = _stream_response(llm_msgs)
                    st.markdown(reply)

        # Save assistant message
        asst_msg = {"role": "assistant", "content": reply, "timestamp": _ts()}
        st.session_state["messages"].append(asst_msg)
        
        if ollama_ok:
            save_message(conv_id, "assistant", reply, st.session_state["model"])

        # Voice output
        if st.session_state.get("voice_output_enabled") and voice.is_tts_available():
            voice.speak(reply[:500], engine=st.session_state.get("tts_engine", "pyttsx3"))

        st.rerun()


def _get_demo_reply(user_input: str) -> str:
    """
    Generate a demo reply when Ollama is not available.
    Useful for testing UI and voice features.
    """
    user_lower = user_input.lower()
    
    # Simple keyword matching for demo responses
    demo_responses = {
        "hello": "Hello! I'm Jarvis, your personal AI assistant. I'm currently in demo mode since Ollama isn't running. To enable full AI capabilities, start Ollama by running `ollama serve` in a terminal.",
        "how are you": "I'm doing great! Thanks for asking. I'm running in demo mode right now. To unlock my full capabilities, please start Ollama with `ollama serve`.",
        "test": "This is a test response! I'm running in demo mode. Voice features should work fine for testing. Start `ollama serve` to enable real AI conversations.",
        "voice": "Voice features are fully functional! You can use voice input with the 🎙️ button and enable voice output in Settings. Try clicking the microphone button in the chat to test voice input.",
        "help": "I can help! In demo mode, I provide basic responses to test the UI and voice features. For full functionality, please start Ollama. Visit VOICE_SETUP_GUIDE.md for setup instructions.",
    }
    
    # Check for keyword matches
    for keyword, response in demo_responses.items():
        if keyword in user_lower:
            return response
    
    # Default demo response
    return (
        f"Thanks for asking: *{user_input}*\n\n"
        "I'm currently in **demo mode** (Ollama isn't running). I can still help you test voice features! "
        "To enable full AI conversations:\n\n"
        "1. Open a terminal and run: `ollama serve`\n"
        "2. Reload this page\n"
        "3. Start chatting with me using text or voice\n\n"
        "See [VOICE_SETUP_GUIDE.md](VOICE_SETUP_GUIDE.md) for detailed setup instructions."
    )



def _render_welcome():
    st.markdown(
        """
        <div class="welcome-container">
            <div class="welcome-icon">⚡</div>
            <h2 class="welcome-title">Hello, I'm Jarvis</h2>
            <p class="welcome-sub">Your personal AI assistant — running 100 % locally.</p>
            <div class="welcome-chips">
                <span class="chip">💻 Write & debug code</span>
                <span class="chip">🔐 Cybersecurity help</span>
                <span class="chip">📄 Analyse documents</span>
                <span class="chip">🎓 Explain concepts</span>
                <span class="chip">🗣️ Voice conversation</span>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
