"""
core/llm.py
───────────
Thin wrapper around the Ollama HTTP API.

Ollama exposes a REST endpoint at http://localhost:11434
No API key needed — everything is local.

Public API
──────────
  chat_stream(messages, model, system, temperature, max_tokens)
      → Generator[str]   (token-by-token)

  chat(messages, ...)
      → str              (full reply at once)

  list_models()
      → list[str]

  is_ollama_running()
      → bool
"""

from __future__ import annotations

import json
import requests
from typing import Generator

OLLAMA_BASE = "http://localhost:11434"


# ── Availability check ────────────────────────────────────────────────────────

def is_ollama_running() -> bool:
    """Return True if Ollama is reachable."""
    try:
        r = requests.get(f"{OLLAMA_BASE}/api/tags", timeout=3)
        return r.status_code == 200
    except Exception:
        return False


def list_models() -> list[str]:
    """Return names of locally available Ollama models."""
    try:
        r = requests.get(f"{OLLAMA_BASE}/api/tags", timeout=5)
        r.raise_for_status()
        data = r.json()
        return [m["name"] for m in data.get("models", [])]
    except Exception:
        return []


# ── Core chat functions ───────────────────────────────────────────────────────

def _build_payload(
    messages: list[dict],
    model: str,
    system: str,
    temperature: float,
    max_tokens: int,
    stream: bool,
) -> dict:
    """Build the JSON body for /api/chat."""
    ollama_msgs = []

    # System message first
    if system:
        ollama_msgs.append({"role": "system", "content": system})

    # Conversation history  (role = "user" | "assistant")
    for m in messages:
        ollama_msgs.append({"role": m["role"], "content": m["content"]})

    return {
        "model": model,
        "messages": ollama_msgs,
        "stream": stream,
        "options": {
            "temperature": temperature,
            "num_predict": max_tokens,
        },
    }


def chat_stream(
    messages: list[dict],
    model: str = "llama3.2",
    system: str = "",
    temperature: float = 0.7,
    max_tokens: int = 2048,
) -> Generator[str, None, None]:
    """
    Yield response tokens one-by-one as they arrive from Ollama.
    Use inside a  st.write_stream()  or a manual accumulator loop.
    """
    payload = _build_payload(messages, model, system, temperature, max_tokens, stream=True)

    with requests.post(
        f"{OLLAMA_BASE}/api/chat",
        json=payload,
        stream=True,
        timeout=120,
    ) as resp:
        resp.raise_for_status()
        for raw_line in resp.iter_lines():
            if not raw_line:
                continue
            try:
                chunk = json.loads(raw_line)
                token = chunk.get("message", {}).get("content", "")
                if token:
                    yield token
                if chunk.get("done"):
                    break
            except json.JSONDecodeError:
                continue


def chat(
    messages: list[dict],
    model: str = "llama3.2",
    system: str = "",
    temperature: float = 0.7,
    max_tokens: int = 2048,
) -> str:
    """Return the complete assistant reply as a single string."""
    return "".join(
        chat_stream(messages, model, system, temperature, max_tokens)
    )
