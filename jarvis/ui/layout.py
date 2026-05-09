"""
ui/layout.py
────────────
Sidebar: model selector, conversation history, new chat button.
Returns the active tab name so app.py can route to the right view.
"""

from __future__ import annotations

import streamlit as st
from core.database import list_conversations, delete_conversation, load_conversation
from core.session import _new_conversation_id
from core.llm import list_models, is_ollama_running


def render_sidebar() -> str:
    with st.sidebar:
        # ── Brand ─────────────────────────────────────────────────────────────
        st.markdown(
            """
            <div class="sidebar-brand">
                <span class="brand-icon">⚡</span>
                <span class="brand-name">JARVIS</span>
                <span class="brand-sub">AI Assistant</span>
            </div>
            """,
            unsafe_allow_html=True,
        )

        st.markdown("---")

        # ── Navigation ────────────────────────────────────────────────────────
        tabs = ["💬 Chat", "📄 Documents", "⚙️ Settings"]
        active = st.radio(
            "Navigation",
            tabs,
            index=tabs.index(st.session_state.get("active_tab", "💬 Chat")),
            label_visibility="collapsed",
        )
        st.session_state["active_tab"] = active

        st.markdown("---")

        # ── Ollama status ─────────────────────────────────────────────────────
        if is_ollama_running():
            st.markdown(
                '<div class="status-badge status-ok">🟢 Ollama Running</div>',
                unsafe_allow_html=True,
            )
            models = list_models()
            if models:
                current = st.session_state.get("model", models[0])
                if current not in models:
                    current = models[0]
                st.session_state["model"] = st.selectbox(
                    "🧠 Model", models,
                    index=models.index(current),
                    key="model_selector",
                )
            else:
                st.warning("No models found.\nRun: `ollama pull llama3.2`")
        else:
            st.markdown(
                '<div class="status-badge status-err">🔴 Ollama Offline</div>',
                unsafe_allow_html=True,
            )
            st.info("Start Ollama:\n```\nollama serve\n```")

        st.markdown("---")

        # ── New conversation ───────────────────────────────────────────────────
        if st.button("➕ New Chat", use_container_width=True, type="primary"):
            st.session_state["messages"] = []
            st.session_state["conversation_id"] = _new_conversation_id()
            st.session_state["rag_enabled"] = False
            st.session_state["uploaded_docs"] = []
            st.rerun()

        # ── Past conversations ────────────────────────────────────────────────
        st.markdown("#### 🗂 History")
        convs = list_conversations(limit=20)

        if not convs:
            st.caption("No past conversations yet.")
        else:
            for conv in convs:
                col1, col2 = st.columns([4, 1])
                with col1:
                    label = conv["title"][:30] + ("…" if len(conv["title"]) > 30 else "")
                    if st.button(label, key=f"load_{conv['id']}", use_container_width=True):
                        msgs = load_conversation(conv["id"])
                        st.session_state["messages"] = msgs
                        st.session_state["conversation_id"] = conv["id"]
                        st.rerun()
                with col2:
                    if st.button("🗑", key=f"del_{conv['id']}"):
                        delete_conversation(conv["id"])
                        st.rerun()

        # ── RAG indicator ─────────────────────────────────────────────────────
        if st.session_state.get("rag_enabled"):
            docs = st.session_state.get("uploaded_docs", [])
            st.markdown("---")
            st.markdown(f"**📚 {len(docs)} doc(s) indexed**")
            for d in docs:
                st.caption(f"• {d}")

    return active


def render_header():
    """Top banner shown in the main content area."""
    model = st.session_state.get("model", "—")
    rag   = "✅ RAG ON" if st.session_state.get("rag_enabled") else "⚪ RAG OFF"
    st.markdown(
        f"""
        <div class="top-header">
            <div class="header-left">
                <span class="header-title">⚡ Jarvis</span>
                <span class="header-subtitle">Personal AI Assistant</span>
            </div>
            <div class="header-right">
                <span class="header-chip">🧠 {model}</span>
                <span class="header-chip">{rag}</span>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
