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
  get_diagnostics() → dict       debug info on voice setup
"""

from __future__ import annotations
import io
import threading
from typing import Optional, Dict, Any
import logging

# Setup logging
logger = logging.getLogger(__name__)

# ── Optional imports ──────────────────────────────────────────────────────────
try:
    import speech_recognition as sr
    HAS_SR = True
    SR_VERSION = sr.__version__ if hasattr(sr, '__version__') else "unknown"
except ImportError:
    HAS_SR = False
    SR_VERSION = None

try:
    import pyttsx3
    _tts_engine = pyttsx3.init()
    _tts_engine.setProperty("rate", 175)   # words per minute
    HAS_PYTTSX3 = True
except Exception as e:
    HAS_PYTTSX3 = False
    logger.warning(f"pyttsx3 initialization failed: {e}")
    _tts_engine = None

try:
    from gtts import gTTS
    import pygame
    try:
        pygame.mixer.init()
    except Exception as e:
        logger.warning(f"pygame mixer init failed: {e}")
    HAS_GTTS = True
except (ImportError, Exception) as e:
    HAS_GTTS = False
    logger.warning(f"gTTS/pygame import failed: {e}")


# ── STT ───────────────────────────────────────────────────────────────────────

def is_stt_available() -> bool:
    """Check if speech-to-text is available."""
    return HAS_SR


def listen(timeout: int = 8, phrase_limit: int = 20) -> Optional[str]:
    """
    Record from the default microphone and return the transcribed text.
    Returns None on failure.
    
    Tries multiple recognition engines:
    1. Google Web Speech API (requires internet, most accurate)
    2. CMU Sphinx (offline fallback)
    """
    if not HAS_SR:
        logger.error("SpeechRecognition not installed")
        return None

    recognizer = sr.Recognizer()
    recognizer.energy_threshold = 300
    recognizer.dynamic_energy_threshold = True

    try:
        with sr.Microphone() as source:
            try:
                recognizer.adjust_for_ambient_noise(source, duration=0.5)
                audio = recognizer.listen(
                    source,
                    timeout=timeout,
                    phrase_time_limit=phrase_limit,
                )
            except sr.MicrophoneError as e:
                logger.error(f"Microphone error: {e}")
                return None
                
        # Try Google Web Speech (free, no key needed for moderate use)
        try:
            text = recognizer.recognize_google(audio)
            logger.debug(f"Google STT succeeded: {text[:50]}")
            return text.strip()
        except sr.WaitTimeoutError:
            logger.warning("Speech recognition timeout - no audio detected")
            return None
        except sr.UnknownValueError:
            logger.warning("Speech not understood")
            return None
        except sr.RequestError as e:
            logger.warning(f"Google API error: {e}. Trying offline Sphinx...")
            # Google unreachable → try offline Sphinx if installed
            try:
                text = recognizer.recognize_sphinx(audio)
                logger.debug(f"Sphinx STT succeeded: {text[:50]}")
                return text.strip()
            except Exception as sphinx_error:
                logger.error(f"Sphinx STT failed: {sphinx_error}")
                return None
    except Exception as e:
        logger.error(f"Unexpected error in listen(): {e}")
        return None


# ── TTS ───────────────────────────────────────────────────────────────────────

def is_tts_available() -> bool:
    """Check if text-to-speech is available."""
    return HAS_PYTTSX3 or HAS_GTTS


def speak(text: str, engine: str = "pyttsx3") -> bool:
    """
    Convert text to speech. Non-blocking (runs in a daemon thread).
    Returns True if successfully started, False otherwise.
    """
    if not text.strip():
        return False

    # Strip markdown so the assistant doesn't read asterisks aloud
    import re
    clean = re.sub(r"[*_`#>\[\]]+", "", text)
    clean = re.sub(r"\n+", ". ", clean).strip()

    if not clean:
        return False

    if engine == "pyttsx3" and HAS_PYTTSX3:
        t = threading.Thread(target=_speak_pyttsx3, args=(clean,), daemon=True)
        t.start()
        return True
    elif engine == "gtts" and HAS_GTTS:
        t = threading.Thread(target=_speak_gtts, args=(clean,), daemon=True)
        t.start()
        return True
    else:
        logger.error(f"TTS engine '{engine}' not available")
        return False


def _speak_pyttsx3(text: str):
    """Internal: speak using pyttsx3 engine."""
    try:
        if _tts_engine is None:
            logger.error("pyttsx3 engine not initialized")
            return
        _tts_engine.say(text)
        _tts_engine.runAndWait()
        logger.debug(f"pyttsx3 spoke: {text[:50]}")
    except Exception as e:
        logger.error(f"pyttsx3 error: {e}")


def _speak_gtts(text: str):
    """Internal: speak using gTTS engine."""
    try:
        tts = gTTS(text=text, lang="en", slow=False)
        buf = io.BytesIO()
        tts.write_to_fp(buf)
        buf.seek(0)
        pygame.mixer.music.load(buf)
        pygame.mixer.music.play()
        while pygame.mixer.music.get_busy():
            pygame.time.Clock().tick(10)
        logger.debug(f"gTTS spoke: {text[:50]}")
    except Exception as e:
        logger.error(f"gTTS error: {e}")


def get_diagnostics() -> Dict[str, Any]:
    """
    Return diagnostic information about voice system setup.
    Useful for debugging voice issues.
    """
    diag = {
        "stt_available": HAS_SR,
        "stt_version": SR_VERSION,
        "tts_pyttsx3_available": HAS_PYTTSX3,
        "tts_gtts_available": HAS_GTTS,
        "overall_voice_capable": is_stt_available() or is_tts_available(),
    }
    
    # Try to detect microphone
    if HAS_SR:
        try:
            mics = sr.Microphone.list_microphone_indexes()
            diag["microphones_detected"] = len(mics) > 0
            diag["mic_count"] = len(mics)
        except Exception as e:
            diag["microphones_detected"] = False
            diag["mic_error"] = str(e)
    
    return diag
