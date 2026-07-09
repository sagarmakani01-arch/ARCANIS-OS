"""Wake word detection.

Strategies:
  - builtin: lightweight offline detector using phoneme-ish keyword spotting
             on Vosk partial transcripts (no extra model download required).
  - porcupine: Picovoice Porcupine (high accuracy, needs access key).
  - vosk: stream partial ASR results and match keyword.

All run locally. The detector exposes `process(frame_int16) -> bool`.
"""
from __future__ import annotations

import numpy as np
import re

try:
    import pvporcupine
except Exception:  # noqa: BLE001
    pvporcupine = None  # type: ignore

from .config import WakeWordConfig
from .utils import logger


class WakeWordDetector:
    def __init__(self, cfg: WakeWordConfig, sample_rate: int) -> None:
        self.cfg = cfg
        self.sample_rate = sample_rate
        self.model = cfg.model if cfg.enabled else "disabled"
        self._engine = None
        self._partial_text = ""
        self._keyword = cfg.keyword.lower().strip()
        self._activated_cb = None
        if self.model == "porcupine":
            if pvporcupine is None or not cfg.porcupine_access_key:
                logger.warning("porcupine unavailable/key missing; using builtin")
                self.model = "builtin"
            else:
                self._engine = pvporcupine.create(
                    access_key=cfg.porcupine_access_key,
                    keywords=[cfg.porcupine_keyword],
                )

    @property
    def enabled(self) -> bool:
        return self.model != "disabled"

    def feed_text(self, partial: str) -> bool:
        """Feed ASR partial transcript; returns True if keyword spotted."""
        if self.model not in ("builtin", "vosk"):
            return False
        self._partial_text = (self._partial_text + " " + partial).lower()
        self._partial_text = self._partial_text[-200:]
        if re.search(r"\b" + re.escape(self._keyword) + r"\b", self._partial_text):
            self._partial_text = ""
            return True
        return False

    def process(self, frame_int16: np.ndarray) -> bool:
        if self.model == "porcupine" and self._engine is not None:
            pcm = frame_int16.astype(np.int16)
            score = self._engine.process(pcm)
            return bool(score >= 0)
        # builtin / vosk rely on feed_text from the ASR stage.
        return False

    def close(self) -> None:
        if self._engine is not None:
            try:
                self._engine.delete()
            except Exception:  # noqa: BLE001
                pass
