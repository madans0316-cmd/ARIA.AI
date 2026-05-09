# ⚡ Jarvis AI Assistant

> Your personal, offline-first AI assistant — powered by Ollama + Streamlit.

---

## 📁 Project Structure

```
jarvis/
│
├── app.py                   ← Entry point (run this)
│
├── core/                    ← Business logic (no UI here)
│   ├── __init__.py
│   ├── session.py           ← Streamlit session state bootstrap
│   ├── llm.py               ← Ollama API wrapper (streaming chat)
│   ├── database.py          ← SQLite chat history (persist across sessions)
│   ├── rag.py               ← Document ingestion + retrieval (PDF/TXT/code)
│   └── voice.py             ← Speech-to-text + text-to-speech
│
├── ui/                      ← Streamlit UI components
│   ├── __init__.py
│   ├── layout.py            ← Sidebar + header
│   ├── chat_view.py         ← Chat screen (streaming, voice, RAG)
│   ├── file_view.py         ← Document upload + index management
│   └── settings_view.py     ← Model params, voice, system prompt
│
├── assets/
│   └── style.css            ← Custom dark cyberpunk CSS theme
│
├── data/                    ← Created automatically at runtime
│   ├── jarvis.db            ← SQLite database (chat history)
│   ├── uploads/             ← Temp uploaded files
│   └── history/             ← (reserved for future export)
│
└── requirements.txt         ← All Python dependencies
```

---

## 🚀 Quick Start (Step-by-Step)

### Step 1 — Install Ollama

#### macOS
```bash
brew install ollama
```

#### Linux
```bash
curl -fsSL https://ollama.ai/install.sh | sh
```

#### Windows
Download the installer from https://ollama.ai/download

---

### Step 2 — Pull an LLM model

```bash
# Start Ollama (if not already running as a service)
ollama serve

# In a NEW terminal, pull a model:
ollama pull llama3.2          # ← recommended, 2 GB, fast
# OR
ollama pull mistral           # alternative
ollama pull codellama         # great for code tasks

# Pull the embedding model (optional but improves document Q&A)
ollama pull nomic-embed-text
```

---

### Step 3 — Set up Python environment

```bash
# Create a virtual environment (recommended)
python -m venv venv

# Activate it:
source venv/bin/activate       # macOS / Linux
venv\Scripts\activate          # Windows

# Install dependencies
pip install -r requirements.txt
```

> **PyAudio note (for voice input):**
> - macOS:  `brew install portaudio && pip install pyaudio`
> - Linux:  `sudo apt install portaudio19-dev && pip install pyaudio`
> - Windows: `pip install pipwin && pipwin install pyaudio`

---

### Step 4 — Launch Jarvis

```bash
# Make sure Ollama is running first:
ollama serve &

# Then launch the app:
streamlit run app.py
```

Open your browser at **http://localhost:8501** 🎉

---

## ✨ Features

| Feature | How it works |
|---------|--------------|
| **Chat** | Streams token-by-token from a local Ollama model |
| **Memory** | Every message saved to SQLite; reload any past conversation |
| **PDF Q&A** | Upload PDF → chunked → embedded → RAG retrieval |
| **Code** | Ask Jarvis to write, debug, or explain code in any language |
| **Cybersecurity** | Jarvis knows CTF, pentesting, networking, crypto |
| **Voice Input** | Click 🎙️ → speak → transcribed via SpeechRecognition |
| **Voice Output** | Jarvis reads replies aloud via pyttsx3 (offline) |
| **Multi-model** | Switch between any Ollama model in the sidebar |

---

## 🛠 Troubleshooting

### "Ollama is not running"
```bash
ollama serve           # start the Ollama server
ollama list            # verify models are downloaded
```

### "No models found"
```bash
ollama pull llama3.2
```

### Voice input not working
```bash
# Linux
sudo apt install portaudio19-dev python3-pyaudio
pip install pyaudio SpeechRecognition

# macOS
brew install portaudio
pip install pyaudio SpeechRecognition
```

### PDF parsing fails
```bash
pip install PyMuPDF --upgrade
```

### Slow responses
- Use a smaller model: `ollama pull llama3.2:1b`
- Lower **Max Tokens** in Settings
- Close other heavy applications

---

## 📈 Optimization Tips

1. **Use `llama3.2:3b`** for speed on laptops without a GPU.
2. **GPU acceleration**: If you have NVIDIA GPU, Ollama uses it automatically.
3. **Bigger context**: Use `mistral:7b` or `llama3.1:8b` for complex tasks.
4. **Embedding model**: `nomic-embed-text` gives much better document retrieval than keyword fallback.
5. **Streamlit caching**: Add `@st.cache_resource` to LLM init for even faster cold starts.

---

## 🔮 Future Roadmap (Android Integration)

The modular `core/` layer is intentionally decoupled from Streamlit.
For a future Android app:

```
Android (Kotlin/Jetpack Compose)
    ↕ REST API (FastAPI wrapper around core/)
core/llm.py        → same Ollama calls
core/database.py   → same SQLite or swap to Room DB
core/rag.py        → same logic, expose as endpoint
core/voice.py      → replace with Android STT/TTS APIs
```

To expose Jarvis as a REST API:
```bash
pip install fastapi uvicorn
# Then wrap core/ functions in FastAPI routes
```

---

## 📜 License

MIT — free for personal and commercial use.
