# 🎤 Voice Recognition Setup Guide

## Overview
Jarvis AI Assistant includes **full voice support** with both speech-to-text (voice input) and text-to-speech (voice output).

---

## 1. Prerequisites

### System Requirements
- **Windows 10+**, **macOS 10.14+**, or **Linux**
- **Microphone** (for voice input)
- **Speaker/Headphones** (for voice output)

### Python Requirements
- Python 3.10 or higher
- All dependencies installed: `pip install -r requirements.txt`

---

## 2. Voice Features

### 🎤 Voice Input (Speech-to-Text)
**Technology:** SpeechRecognition library
- **Online mode (default):** Google Web Speech API (free, requires internet)
- **Offline fallback:** CMU Sphinx (if available)

**Setup:**
```bash
# Already included in requirements.txt
pip install SpeechRecognition>=3.10.0

# Optional: For better offline support (Linux/Mac)
pip install PocketSphinx
```

**Testing voice input:**
1. Go to ⚙️ Settings tab
2. Expand 🎙️ Voice section
3. Toggle **🎤 Voice Input (microphone → text)**
4. Return to 💬 Chat tab
5. Click **🎙️** button and speak!

---

### 🔊 Voice Output (Text-to-Speech)
**Technology:** pyttsx3 (offline) or gTTS (online)

#### Option A: pyttsx3 (Recommended - Offline, Instant)
```bash
# Already included in requirements.txt
pip install pyttsx3>=2.90

# Windows: Usually works out-of-the-box
# macOS: Requires no additional setup
# Linux: Requires festival or espeak
```

**Linux users (Ubuntu/Debian):**
```bash
sudo apt-get install espeak
```

#### Option B: gTTS (Online - Better Quality)
```bash
# Optional - higher quality but requires internet
pip install gtts>=2.5.1 pygame>=2.5.2
```

**Testing voice output:**
1. Go to ⚙️ Settings tab
2. Expand 🎙️ Voice section
3. Toggle **🔊 Voice Output (Jarvis speaks replies)**
4. Select TTS Engine: "pyttsx3 (offline)" or "gtts (online, better quality)"
5. Send a message in the chat - Jarvis will speak the reply!

---

## 3. Troubleshooting

### ❌ "Speech-to-text not available" warning

**Solution:**
```bash
# Install missing dependencies
pip install SpeechRecognition>=3.10.0
```

**For Windows (if microphone not detected):**
- Check System Sound Settings (Settings → Sound)
- Ensure microphone is default recording device
- Test microphone with: Windows Settings → Sound → Input → Test your microphone

**For macOS:**
- Allow Streamlit microphone access: System Preferences → Security & Privacy → Microphone

**For Linux:**
```bash
# Install audio support
sudo apt-get install python3-pyaudio
pip install PyAudio
```

---

### ❌ "Text-to-speech not available" warning

**Solution:**
```bash
# Install pyttsx3
pip install pyttsx3>=2.90
```

**For Linux (Ubuntu/Debian):**
```bash
sudo apt-get install espeak-ng
# or
sudo apt-get install festival
```

**For macOS:**
Usually works out-of-the-box. If issues:
```bash
pip install --upgrade pyttsx3
```

---

### ❌ Voice input times out ("Couldn't hear you")

**Causes & Solutions:**
1. **Microphone not working**
   - Test system microphone first
   - Check permissions (macOS/Linux)
   
2. **Background noise**
   - Find quieter location
   - Adjust microphone sensitivity in code:
   ```python
   # In core/voice.py, increase this if needed:
   recognizer.energy_threshold = 3000  # Higher = more sensitive
   ```

3. **Internet issues (for Google Speech API)**
   - Check internet connection
   - Google API has rate limits - install Sphinx for offline:
   ```bash
   pip install PocketSphinx
   ```

---

### ❌ Voice output doesn't play or sounds bad

**For pyttsx3:**
```bash
# Reinstall and reinitialize
pip uninstall pyttsx3 -y && pip install pyttsx3

# Test with:
python -c "import pyttsx3; engine = pyttsx3.init(); engine.say('Hello'); engine.runAndWait()"
```

**For Linux users:**
```bash
# Use festival instead
pip install festival
# Or use espeak directly
espeak "Hello world"
```

**For gTTS (online):**
- Ensure internet connection
- Try switching to pyttsx3 (Settings → Voice → pyttsx3)

---

## 4. Advanced Configuration

### Customize Voice Output Settings

Edit `core/voice.py` to adjust:

```python
# Speech rate (words per minute)
_tts_engine.setProperty("rate", 175)  # Default: 175 wpm

# Voice volume (0.0 - 1.0)
_tts_engine.setProperty("volume", 1.0)  # Default: 1.0 (max)
```

### Speech Recognition Settings

Edit `core/voice.py` to adjust:

```python
# Listen timeout (seconds)
timeout=8  # Wait 8 seconds max for speech

# Max phrase length
phrase_limit=20  # Maximum seconds per utterance

# Energy threshold
recognizer.energy_threshold = 300  # Adjust for background noise
```

---

## 5. Full Voice Workflow

### Typical Use Case:
1. **Start Jarvis:** `streamlit run app.py`
2. **Enable voice input:** Settings → Voice → Toggle 🎤 Voice Input
3. **Enable voice output:** Settings → Voice → Toggle 🔊 Voice Output
4. **Chat with Jarvis:**
   - Click 🎙️ button and speak your question
   - Jarvis listens and displays transcribed text
   - Jarvis generates response
   - Jarvis speaks the reply aloud!

---

## 6. Offline vs Online Modes

| Feature | Offline | Online | Default |
|---------|---------|--------|---------|
| Voice Input | CMU Sphinx (limited) | Google API (better) | Google |
| Voice Output (STT) | pyttsx3 | gTTS | pyttsx3 |
| Internet Required | No | Yes | No |
| Speed | Fast | Varies | Fast |
| Accuracy | Medium | Excellent | Medium |

---

## 7. Testing All Features

### ✅ Complete Feature Test Checklist

- [ ] **Ollama Running:** `ollama serve` in terminal
- [ ] **Chat Input:** Type a message → Get AI response
- [ ] **Voice Input:** Click 🎙️ → Speak → See transcribed text
- [ ] **Voice Output:** Send message → Hear Jarvis speak reply
- [ ] **Document Upload:** Upload PDF → Ask questions about it
- [ ] **Model Selection:** Change model in sidebar
- [ ] **Settings:** Adjust temperature, max tokens, system prompt
- [ ] **Dark Mode:** Toggle visual theme
- [ ] **Timestamps:** Show/hide message timestamps
- [ ] **Chat History:** Start new chat, load past conversations

---

## 8. System Requirements Summary

### Minimum Setup
```bash
# Core dependencies (in requirements.txt)
pip install -r requirements.txt

# For voice input
pip install SpeechRecognition>=3.10.0

# For voice output
pip install pyttsx3>=2.90
```

### Full Setup (All Features)
```bash
# Install everything
pip install -r requirements.txt
pip install SpeechRecognition pyttsx3 gtts pygame PyMuPDF

# For Linux: Audio support
sudo apt-get install espeak-ng python3-pyaudio
```

### Local LLM (Required for Chat)
```bash
# Download and install Ollama from: https://ollama.ai
# Pull a model
ollama pull llama3.2

# Run in separate terminal
ollama serve
```

---

## 9. Performance Tips

- **Use pyttsx3** for voice output (fastest, offline)
- **Use Google API** for voice input (most accurate, needs internet)
- **Reduce max_tokens** if voice output is slow
- **Use smaller models** if CPU is slow (e.g., `mistral` instead of `llama3.2`)

---

## 10. Getting Help

**Check logs:**
```bash
# Monitor Streamlit output for errors
# Look for: "Uncaught app execution" or "Error" messages
```

**Enable debug mode:**
Add to top of `app.py`:
```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

**Test components individually:**
```python
# Test voice input
python -c "from core.voice import listen; print(listen())"

# Test voice output
python -c "from core.voice import speak; speak('Hello world')"

# Test Ollama connection
python -c "from core.llm import is_ollama_running; print(is_ollama_running())"
```

---

## 11. Quick Start

```bash
# 1. Navigate to project
cd c:\MADDIE\jarvis_ai_assistant\jarvis

# 2. Activate virtual environment
# Windows:
..\..\..\venv\Scripts\Activate.ps1
# macOS/Linux:
source ../../../venv/bin/activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Start Ollama (in separate terminal)
ollama serve

# 5. Start Jarvis
streamlit run app.py

# 6. Open browser and enable voice in Settings!
```

---

✅ **All voice features are now ready to use!**

For more help, check the [Jarvis GitHub](https://github.com/madans0316-cmd/ARIA.AI)
