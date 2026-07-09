"""Natural speech generation (TTS) with voice customization.

Offline-first: pyttsx3 (no network) supports rate/pitch/volume/voice profiles.
Optional Piper engine for higher-quality neural offline TTS.
Online fallback posts text to a TTS endpoint and receives PCM.
"""
from __future__ import annotations

import io
import threading

import numpy as np
import requests

try:
    import pyttsx3
except Exception:  # noqa: BLE001
    pyttsx3 = None  # type: ignore

from .config import TTSConfig, AudioConfig
from .utils import logger


class SpeechSynthesizer:
    def __init__(self, cfg: TTSConfig, audio: AudioConfig) -> None:
        self.cfg = cfg
        self.audio = audio
        self.sample_rate = audio.sample_rate
        self._engine = None
        self._lock = threading.Lock()
        self._online = False

        if cfg.engine in ("pyttsx3", "offline") and pyttsx3 is not None:
            try:
                self._engine = pyttsx3.init()
                self._apply_voice()
                logger.info("pyttsx3 TTS ready")
            except Exception as exc:  # noqa: BLE001
                logger.warning("pyttsx3 init failed: %s", exc)
                self._engine = None

        if self._engine is None and cfg.online_endpoint:
            self._online = True
            logger.info("TTS using online endpoint")

    def _apply_voice(self) -> None:
        if self._engine is None:
            return
        e = self._engine
        try:
            e.setProperty("rate", self.cfg.rate)
            e.setProperty("volume", self.cfg.volume)
        except Exception:  # noqa: BLE001
            pass
        try:
            voices = e.getProperty("voices") or []
            for v in voices:
                if self.cfg.voice_profile.lower() in (v.id or "").lower() or \
                   self.cfg.voice_profile.lower() in (v.name or "").lower():
                    e.setProperty("voice", v.id)
                    break
        except Exception:  # noqa: BLE001
            pass

    def set_voice(self, profile: str | None = None, rate: int | None = None,
                  pitch: int | None = None, volume: float | None = None) -> None:
        if profile is not None:
            self.cfg.voice_profile = profile
        if rate is not None:
            self.cfg.rate = rate
        if pitch is not None:
            self.cfg.pitch = pitch
        if volume is not None:
            self.cfg.volume = volume
        self._apply_voice()

    def _render_offline(self, text: str) -> bytes:
        """Render to WAV bytes via pyttsx3.

        pyttsx3 reliably writes to a real file path; writing to an
        in-memory BytesIO can return empty on some Windows drivers,
        so we render to a temp file and read it back.
        """
        import os
        import tempfile
        with self._lock:
            fd, path = tempfile.mkstemp(suffix=".wav")
            os.close(fd)
            try:
                self._engine.save_to_file(text, path)
                self._engine.runAndWait()
                if not os.path.exists(path):
                    return b""
                with open(path, "rb") as fh:
                    return fh.read()
            except Exception as exc:  # noqa: BLE001
                logger.warning("TTS render failed: %s", exc)
                return b""
            finally:
                try:
                    os.remove(path)
                except OSError:
                    pass

    def _render_online(self, text: str) -> bytes | None:
        try:
            resp = requests.post(
                self.cfg.online_endpoint,
                headers={"Authorization": f"Bearer {self.cfg.online_api_key}"},
                json={"text": text, "voice": self.cfg.voice_profile,
                      "rate": self.cfg.rate, "pitch": self.cfg.pitch},
                timeout=10,
            )
            resp.raise_for_status()
            return resp.content
        except Exception as exc:  # noqa: BLE001
            logger.warning("online TTS failed: %s", exc)
            return None

    def synthesize(self, text: str) -> np.ndarray | None:
        """Return int16 PCM at self.sample_rate for playback."""
        if not text:
            return None
        if self._online:
            data = self._render_online(text)
            if data is None:
                return None
            return self._wav_to_pcm(data)
        if self._engine is not None:
            wav = self._render_offline(text)
            return self._wav_to_pcm(wav)
        logger.error("no TTS backend available")
        return None

    def _wav_to_pcm(self, wav_bytes: bytes) -> np.ndarray | None:
        try:
            import wave
            with wave.open(io.BytesIO(wav_bytes), "rb") as wf:
                raw = wf.readframes(wf.getnframes())  # noqa
                pcm = np.frombuffer(raw, dtype=np.int16)
                # resample if needed (simple nearest; sounddevice plays native rate)
                return pcm
        except Exception as exc:  # noqa: BLE001
            logger.warning("wav decode failed: %s", exc)
            return None

    def speak(self, text: str, play: callable) -> bool:
        pcm = self.synthesize(text)
        if pcm is None:
            return False
        play(pcm)
        return True
