"""
ui/file_view.py
───────────────
Document upload tab:
  • Accepts PDF, TXT, MD, PY, JS, C, CPP, JAVA files
  • Ingests each into the RAG index
  • Shows currently indexed documents
  • Lets the user clear the index
"""

from __future__ import annotations

import os
import tempfile
import streamlit as st

from core.rag import ingest_file, clear_index, get_indexed_docs


ALLOWED_TYPES = ["pdf", "txt", "md", "py", "js", "ts", "c", "cpp", "java", "go", "rs", "html", "css"]
MAX_SIZE_MB   = 20


def render_file_upload():
    st.markdown("## 📄 Document Intelligence")
    st.markdown(
        "Upload files to let Jarvis read and answer questions from them. "
        "Supported: **PDF, TXT, Markdown, and source code files**."
    )

    # ── Upload widget ─────────────────────────────────────────────────────────
    uploaded_files = st.file_uploader(
        "Drop files here",
        type=ALLOWED_TYPES,
        accept_multiple_files=True,
        help=f"Max {MAX_SIZE_MB} MB per file",
    )

    if uploaded_files:
        for uf in uploaded_files:
            fname = uf.name

            # Skip already-indexed files
            if fname in st.session_state.get("uploaded_docs", []):
                st.info(f"ℹ️ **{fname}** is already indexed.")
                continue

            # Size check
            size_mb = len(uf.getvalue()) / (1024 * 1024)
            if size_mb > MAX_SIZE_MB:
                st.error(f"❌ **{fname}** is {size_mb:.1f} MB — too large (max {MAX_SIZE_MB} MB).")
                continue

            # Write to temp file and ingest
            with st.spinner(f"📖 Indexing **{fname}**…"):
                with tempfile.NamedTemporaryFile(
                    delete=False,
                    suffix=os.path.splitext(fname)[1],
                ) as tmp:
                    tmp.write(uf.getvalue())
                    tmp_path = tmp.name

                try:
                    n_chunks = ingest_file(tmp_path, fname)
                    st.session_state.setdefault("uploaded_docs", []).append(fname)
                    st.session_state["rag_enabled"] = True
                    st.success(f"✅ **{fname}** indexed → {n_chunks} chunks.")
                except Exception as e:
                    st.error(f"❌ Failed to index **{fname}**: {e}")
                finally:
                    os.unlink(tmp_path)   # clean up temp file

    st.markdown("---")

    # ── Indexed docs list ─────────────────────────────────────────────────────
    indexed = get_indexed_docs()

    if indexed:
        st.markdown("### 📚 Indexed Documents")
        for doc in indexed:
            col1, col2 = st.columns([5, 1])
            col1.markdown(f"📄 `{doc}`")

        st.markdown("")
        if st.button("🗑️ Clear All Documents", type="secondary"):
            clear_index()
            st.session_state["uploaded_docs"] = []
            st.session_state["rag_enabled"]   = False
            st.success("Index cleared.")
            st.rerun()

        st.markdown("---")
        st.info(
            "💡 **Tip:** Switch to the **Chat** tab and ask questions about your documents. "
            "Jarvis will automatically find relevant passages."
        )
    else:
        st.markdown(
            """
            <div class="empty-state">
                <div style="font-size:3rem">📂</div>
                <p>No documents indexed yet.</p>
                <p style="color:#888; font-size:0.85rem">
                    Upload a PDF or text file above to get started.
                </p>
            </div>
            """,
            unsafe_allow_html=True,
        )

    # ── How it works ──────────────────────────────────────────────────────────
    with st.expander("ℹ️ How document Q&A works"):
        st.markdown(
            """
            1. **Upload** a PDF or text file.
            2. Jarvis **splits** it into overlapping 500-word chunks.
            3. Each chunk is **embedded** (converted to a number vector).
            4. When you ask a question, the most **relevant chunks** are retrieved.
            5. Those chunks are injected into Jarvis's context before it answers.

            **For best results** with the embedding model, run:
            ```bash
            ollama pull nomic-embed-text
            ```
            Without it, Jarvis uses a keyword-matching fallback (still works well).
            """
        )
