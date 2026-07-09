"""Noise filtering / pre-processing for incoming audio.

Three selectable methods, all run locally (no cloud):
  - webrtc: WebRTC VAD-based comfort noise + high-pass (fast, good for speech)
  - spectral: spectral gating using STFT
  - rnnoise: placeholder hook for an external RNNoise model

All operate on int16 frames and return cleaned int16 frames.
"""
from __future__ import annotations

import numpy as np
from scipy.signal import butter, sosfilt

try:
    import webrtcvad
except Exception:  # noqa: BLE001
    webrtcvad = None  # type: ignore

from .config import NoiseFilterConfig
from .utils import logger


class NoiseFilter:
    def __init__(self, cfg: NoiseFilterConfig, sample_rate: int) -> None:
        self.cfg = cfg
        self.sample_rate = sample_rate
        self.method = cfg.method if cfg.enabled else "none"
        self._vad = None
        if self.method == "webrtc":
            if webrtcvad is None:
                logger.warning("webrtcvad not installed; falling back to spectral")
                self.method = "spectral"
            else:
                self._vad = webrtcvad.Vad(cfg.aggressiveness)
        self._hp = butter(
            4,
            max(cfg.highpass_hz, 1.0),
            btype="highpass",
            fs=sample_rate,
            output="sos",
        )
        self._hp_state = np.zeros((self._hp.shape[0], 2))

    def _to_float(self, pcm: np.ndarray) -> np.ndarray:
        return pcm.astype(np.float32) / 32768.0

    def _to_int(self, x: np.ndarray) -> np.ndarray:
        return np.clip(x * 32768.0, -32768, 32767).astype(np.int16)

    def _highpass(self, x: np.ndarray) -> np.ndarray:
        y, self._hp_state = sosfilt(self._hp, x, zi=self._hp_state)
        return y

    def _spectral_gate(self, x: np.ndarray) -> np.ndarray:
        n = len(x)
        if n == 0:
            return x
        window = np.hanning(n)
        spec = np.fft.rfft(x * window)
        mag = np.abs(spec)
        floor = 10 ** (self.cfg.spectral_floor_db / 20.0) * np.max(mag) if np.max(mag) > 0 else 0
        mask = mag > floor
        spec *= mask
        out = np.fft.irfft(spec)[:n]
        return out

    def process(self, pcm_int16: np.ndarray) -> np.ndarray:
        if self.method == "none":
            return pcm_int16
        x = self._to_float(pcm_int16)
        x = self._highpass(x)
        if self.method == "spectral":
            x = self._spectral_gate(x)
        elif self.method == "webrtc":
            # WebRTC VAD is frame-classification; we apply comfort gating:
            # frames detected as non-speech are attenuated, not dropped,
            # to preserve barge-in responsiveness.
            try:
                is_speech = self._vad.is_speech(pcm_int16.tobytes(), self.sample_rate)
            except Exception:  # noqa: BLE001
                is_speech = True
            if not is_speech:
                x *= 0.35
        return self._to_int(x)
