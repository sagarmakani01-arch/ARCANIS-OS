"""Speech recognition (ASR).

Offline-first: uses Vosk for local transcription (privacy, no network).
If offline model unavailable and online fallback enabled, sends 16k PCM
to a configurable HTTP endpoint. Streaming partial results are also yielded
so the wake-word / barge-in stages can react early.
"""
from __future__ import annotations

import json
import threading
from typing import Iterator, Optional

import numpy as np
import requests

try:
    from vosk import Model, KaldiRecognizer
except Exception:  # noqa: BLE001
    Model = None  # type: ignore
    KaldiRecognizer = None  # type: ignore

from .config import ASRConfig
from .utils import logger


class SpeechRecognizer:
    def __init__(self, cfg: ASRConfig, sample_rate: int) -> None:
        self.cfg = cfg
        self.sample_rate = sample_rate
        self._model = None
        self._recognizer = None
        self._online = False
        if cfg.engine == "vosk" and Model is not None:
            try:
                self._model = Model(cfg.offline_model)
                self._recognizer = KaldiRecognizer(self._model, sample_rate)
                self._recognizer.SetWords(False)
                logger.info("Vosk model loaded: %s", cfg.offline_model)
            except Exception as exc:  # noqa: BLE001
                logger.warning("Vosk model load failed: %s", exc)
                self._model = None
        if self._model is None:
            if cfg.fallback_to_online and cfg.online_endpoint:
                self._online = True
                logger.info("ASR using online endpoint (offline unavailable)")
            else:
                logger.error("No ASR backend available")

    @property
    def available(self) -> bool:
        return self._model is not None or self._online

    def _finalize_vosk(self, frame_int16: np.ndarray) -> Optional[str]:
        if self._recognizer.AcceptWaveform(frame_int16.tobytes()):
            res = json.loads(self._recognizer.Result())
            return res.get("text", "").strip() or None
        return None

    def _partial_vosk(self, frame_int16: np.ndarray) -> str:
        if self._recognizer is None:
            return ""
        self._recognizer.AcceptWaveform(frame_int16.tobytes())
        res = json.loads(self._recognizer.PartialResult())
        return res.get("partial", "").strip()

    def _online_transcribe(self, audio: np.ndarray) -> Optional[str]:
        try:
            resp = requests.post(
                self.cfg.online_endpoint,
                headers={"Authorization": f"Bearer {self.cfg.online_api_key}"},
                files={"audio": ("audio.pcm", audio.tobytes(), "application/octet-stream")},
                data={"rate": str(self.sample_rate)},
                timeout=self.cfg.timeout_s if hasattr(self.cfg, "timeout_s") else 8,
            )
            resp.raise_for_status()
            return resp.json().get("text", "").strip() or None
        except Exception as exc:  # noqa: BLE001
            logger.warning("online ASR failed: %s", exc)
            return None

    def stream(self, frames: Iterator[np.ndarray]) -> Iterator[tuple[str, str]]:
        """Yield (event, text) where event in {partial, final}."""
        buf = []
        for frame in frames:
            if self._online:
                buf.append(frame)
                continue
            if self._model is not None:
                partial = self._partial_vosk(frame)
                if partial:
                    yield ("partial", partial)
                final = self._finalize_vosk(frame)
                if final:
                    yield ("final", final)
        if self._online and buf:
            text = self._online_transcribe(np.concatenate(buf))
            if text:
                yield ("final", text)

    def transcribe(self, frames: list[np.ndarray]) -> Optional[str]:
        texts = [t for ev, t in self.stream(iter(frames)) if ev == "final"]
        return " ".join(texts).strip() or None
