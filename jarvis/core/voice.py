"""
core/voice.py
─────────────
Voice input (speech-to-text) and voice output (text-to-speech).

STT  → SpeechRecognition + Google Web Speech API  (free, needs internet)
       OR Whisper via faster-whisper              (fully offline)
TTS  → pyttsx3  (offline, instant)
       OR gTTS   (online, better quality)

All functions degrade gracefully if the optional deps are missing.

Public API
──────────
  listen() → str | None          mic → text (blocks until utterance ends)
  speak(text, engine="pyttsx3")  text → speech
  is_stt_available() → bool
  is_tts_available() → bool
"""

from __future__ import annotations
import io
import threading
from typing import Optional

# ── Optional imports ──────────────────────────────────────────────────────────
try:
    import speech_recognition as sr
    HAS_SR = True
except ImportError:
    HAS_SR = False

try:
    import pyttsx3
    _tts_engine = pyttsx3.init()
    _tts_engine.setProperty("rate", 175)   # words per minute
    HAS_PYTTSX3 = True
except Exception:
    HAS_PYTTSX3 = False

try:
    from gtts import gTTS
    import pygame
    pygame.mixer.init()
    HAS_GTTS = True
except ImportError:
    HAS_GTTS = False


# ── STT ───────────────────────────────────────────────────────────────────────

def is_stt_available() -> bool:
    return HAS_SR


def listen(timeout: int = 8, phrase_limit: int = 20) -> Optional[str]:
    """
    Record from the default microphone and return the transcribed text.
    Returns None on failure.
    """
    if not HAS_SR:
        return None

    recognizer = sr.Recognizer()
    recognizer.energy_threshold = 300
    recognizer.dynamic_energy_threshold = True

    try:
        with sr.Microphone() as source:
            recognizer.adjust_for_ambient_noise(source, duration=0.5)
            audio = recognizer.listen(
                source,
                timeout=timeout,
                phrase_time_limit=phrase_limit,
            )
        # Try Google Web Speech (free, no key needed for moderate use)
        text = recognizer.recognize_google(audio)
        return text.strip()
    except sr.WaitTimeoutError:
        return None
    except sr.UnknownValueError:
        return None
    except sr.RequestError:
        # Google unreachable → try offline Sphinx if installed
        try:
            text = recognizer.recognize_sphinx(audio)
            return text.strip()
        except Exception:
            return None
    except Exception:
        return None


# ── TTS ───────────────────────────────────────────────────────────────────────

def is_tts_available() -> bool:
    return HAS_PYTTSX3 or HAS_GTTS


def speak(text: str, engine: str = "pyttsx3"):
    """Convert text to speech. Non-blocking (runs in a daemon thread)."""
    if not text.strip():
        return

    # Strip markdown so the assistant doesn't read asterisks aloud
    import re
    clean = re.sub(r"[*_`#>\[\]]+", "", text)
    clean = re.sub(r"\n+", ". ", clean).strip()

    if engine == "pyttsx3" and HAS_PYTTSX3:
        t = threading.Thread(target=_speak_pyttsx3, args=(clean,), daemon=True)
        t.start()
    elif engine == "gtts" and HAS_GTTS:
        t = threading.Thread(target=_speak_gtts, args=(clean,), daemon=True)
        t.start()


def _speak_pyttsx3(text: str):
    try:
        _tts_engine.say(text)
        _tts_engine.runAndWait()
    except Exception:
        pass


def _speak_gtts(text: str):
    try:
        tts = gTTS(text=text, lang="en", slow=False)
        buf = io.BytesIO()
        tts.write_to_fp(buf)
        buf.seek(0)
        pygame.mixer.music.load(buf)
        pygame.mixer.music.play()
        while pygame.mixer.music.get_busy():
            pygame.time.Clock().tick(10)
    except Exception:
        pass
