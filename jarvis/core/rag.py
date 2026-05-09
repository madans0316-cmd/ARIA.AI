"""
core/rag.py
───────────
Document ingestion + Retrieval-Augmented Generation (RAG).

Strategy
────────
  1. Parse PDF / TXT / MD / code files → plain text
  2. Split into overlapping chunks (~500 tokens each)
  3. Embed with a lightweight local model via Ollama  (or TF-IDF fallback)
  4. On each user query, retrieve the top-k most relevant chunks
  5. Inject retrieved text into the system prompt before the LLM call

Embedding backend
─────────────────
  Primary   : Ollama  /api/embeddings  (nomic-embed-text recommended)
  Fallback  : TF-IDF cosine similarity (pure Python, no GPU needed)

Public API
──────────
  ingest_file(path, filename) → int   (number of chunks indexed)
  retrieve(query, top_k=4)   → str   (formatted context block)
  clear_index()
  get_indexed_docs()         → list[str]
"""

from __future__ import annotations

import os
import re
import math
import json
import hashlib
import requests
from pathlib import Path
from collections import defaultdict
from typing import Optional

# ── Optional heavy deps (graceful degradation) ────────────────────────────────
try:
    import fitz  # PyMuPDF
    HAS_PYMUPDF = True
except ImportError:
    HAS_PYMUPDF = False

OLLAMA_BASE = "http://localhost:11434"
EMBED_MODEL  = "nomic-embed-text"   # pull with: ollama pull nomic-embed-text
CHUNK_SIZE   = 500    # approximate words per chunk
CHUNK_OVERLAP = 80    # words of overlap between consecutive chunks


# ── In-memory vector store (simple list of dicts) ────────────────────────────
# For a production system swap this for ChromaDB / FAISS.
_store: list[dict] = []   # [{text, embedding|None, source, chunk_id}, ...]
_indexed_docs: set[str] = set()


# ── Text extraction ───────────────────────────────────────────────────────────

def _extract_text(path: str, filename: str) -> str:
    ext = Path(filename).suffix.lower()

    if ext == ".pdf":
        if HAS_PYMUPDF:
            doc = fitz.open(path)
            return "\n".join(page.get_text() for page in doc)
        else:
            # Very basic fallback – read raw bytes and decode printable chars
            with open(path, "rb") as f:
                raw = f.read()
            # Strip binary, keep printable ASCII
            text = raw.decode("latin-1", errors="ignore")
            text = re.sub(r"[^\x20-\x7E\n\t]", " ", text)
            return re.sub(r"\s{3,}", "\n", text)

    # Plain text, markdown, code files
    with open(path, "r", encoding="utf-8", errors="ignore") as f:
        return f.read()


# ── Chunking ──────────────────────────────────────────────────────────────────

def _chunk_text(text: str) -> list[str]:
    words = text.split()
    chunks, i = [], 0
    while i < len(words):
        chunk = " ".join(words[i : i + CHUNK_SIZE])
        chunks.append(chunk)
        i += CHUNK_SIZE - CHUNK_OVERLAP
    return [c.strip() for c in chunks if len(c.strip()) > 60]


# ── Embeddings ────────────────────────────────────────────────────────────────

def _embed_ollama(text: str) -> Optional[list[float]]:
    try:
        r = requests.post(
            f"{OLLAMA_BASE}/api/embeddings",
            json={"model": EMBED_MODEL, "prompt": text},
            timeout=30,
        )
        r.raise_for_status()
        return r.json().get("embedding")
    except Exception:
        return None


def _cosine(a: list[float], b: list[float]) -> float:
    dot = sum(x * y for x, y in zip(a, b))
    na  = math.sqrt(sum(x * x for x in a))
    nb  = math.sqrt(sum(x * x for x in b))
    return dot / (na * nb + 1e-9)


# ── TF-IDF fallback ───────────────────────────────────────────────────────────

def _tfidf_score(query: str, text: str) -> float:
    """Very simple word-overlap score as embedding fallback."""
    q_words = set(re.findall(r"\w+", query.lower()))
    t_words = re.findall(r"\w+", text.lower())
    if not t_words:
        return 0.0
    t_freq: dict[str, int] = defaultdict(int)
    for w in t_words:
        t_freq[w] += 1
    score = sum(t_freq[w] for w in q_words if w in t_freq)
    return score / (len(t_words) ** 0.5 + 1)


# ── Public API ────────────────────────────────────────────────────────────────

def ingest_file(path: str, filename: str) -> int:
    """
    Parse → chunk → embed the file at `path`.
    Returns number of chunks stored.
    """
    global _store, _indexed_docs

    text   = _extract_text(path, filename)
    chunks = _chunk_text(text)

    new_entries = []
    for i, chunk in enumerate(chunks):
        emb = _embed_ollama(chunk)   # None if Ollama embed unavailable
        new_entries.append({
            "text":     chunk,
            "embedding": emb,
            "source":   filename,
            "chunk_id": i,
        })

    _store.extend(new_entries)
    _indexed_docs.add(filename)
    return len(new_entries)


def retrieve(query: str, top_k: int = 4) -> str:
    """
    Find the top-k chunks most relevant to `query`.
    Returns a formatted string ready to inject into the system prompt.
    """
    if not _store:
        return ""

    query_emb = _embed_ollama(query)

    scored = []
    for entry in _store:
        if query_emb and entry["embedding"]:
            score = _cosine(query_emb, entry["embedding"])
        else:
            score = _tfidf_score(query, entry["text"])
        scored.append((score, entry))

    scored.sort(key=lambda x: x[0], reverse=True)
    top = scored[:top_k]

    if not top:
        return ""

    lines = ["--- RELEVANT DOCUMENT EXCERPTS ---"]
    for rank, (score, entry) in enumerate(top, 1):
        lines.append(
            f"\n[Source: {entry['source']} | Chunk {entry['chunk_id']+1}]\n"
            f"{entry['text']}"
        )
    lines.append("\n--- END OF EXCERPTS ---")
    return "\n".join(lines)


def clear_index():
    global _store, _indexed_docs
    _store.clear()
    _indexed_docs.clear()


def get_indexed_docs() -> list[str]:
    return list(_indexed_docs)
