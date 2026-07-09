"""Audio capture/playback abstraction over sounddevice.

Provides a threaded input stream that yields fixed-size frames of int16 PCM
at the configured sample rate, and a blocking/streaming output player.
Designed to be swapped for file or test sources without touching the pipeline.
"""
from __future__ import annotations

import queue
import threading
from typing import Callable, Iterator

import numpy as np
import sounddevice as sd

from .config import AudioConfig
from .utils import logger


class AudioInput:
    def __init__(self, cfg: AudioConfig) -> None:
        self.cfg = cfg
        self._queue: "queue.Queue[np.ndarray]" = queue.Queue(maxsize=64)
        self._stream: sd.InputStream | None = None
        self._stop = threading.Event()
        self._frame_samples = int(cfg.sample_rate * cfg.frame_ms / 1000)

    def _callback(self, indata, frames, time_info, status) -> None:
        if status:
            logger.debug("audio input status: %s", status)
        # Copy because the buffer is reused by the underlying stream.
        self._queue.put(np.frombuffer(indata, dtype=np.int16).copy())

    def start(self) -> None:
        self._stop.clear()
        self._stream = sd.InputStream(
            samplerate=self.cfg.sample_rate,
            channels=self.cfg.channels,
            dtype="int16",
            blocksize=self._frame_samples,
            device=self.cfg.device_input,
            callback=self._callback,
        )
        self._stream.start()
        logger.info("audio input started @ %d Hz", self.cfg.sample_rate)

    def stop(self) -> None:
        self._stop.set()
        if self._stream is not None:
            try:
                self._stream.stop()
                self._stream.close()
            except Exception:  # noqa: BLE001
                pass
            self._stream = None

    def read_frame(self, timeout: float = 1.0) -> np.ndarray | None:
        """Return one frame of int16 PCM, or None on timeout."""
        try:
            return self._queue.get(timeout=timeout)
        except queue.Empty:
            return None

    def iter_frames(self) -> Iterator[np.ndarray]:
        while not self._stop.is_set():
            frame = self.read_frame()
            if frame is not None:
                yield frame


class AudioOutput:
    def __init__(self, cfg: AudioConfig) -> None:
        self.cfg = cfg
        self._stream: sd.OutputStream | None = None

    def _ensure_stream(self) -> None:
        if self._stream is None:
            self._stream = sd.OutputStream(
                samplerate=self.cfg.sample_rate,
                channels=self.cfg.channels,
                dtype="int16",
                device=self.cfg.device_output,
            )
            self._stream.start()

    def play(self, pcm_int16: np.ndarray) -> None:
        self._ensure_stream()
        self._stream.write(pcm_int16)

    def stop(self) -> None:
        if self._stream is not None:
            try:
                self._stream.stop()
                self._stream.close()
            except Exception:  # noqa: BLE001
                pass
            self._stream = None


class FileInput(AudioInput):
    """Replay a recorded int16 PCM file for testing/offline simulation."""

    def __init__(self, cfg: AudioConfig, path: str) -> None:
        super().__init__(cfg)
        self.path = path
        self._data: np.ndarray | None = None

    def start(self) -> None:
        self._data = np.fromfile(self.path, dtype=np.int16)  # type: ignore
        self._stop.clear()
        logger.info("file input loaded: %s (%d samples)", self.path, len(self._data))

    def read_frame(self, timeout: float = 1.0) -> np.ndarray | None:
        if self._data is None or len(self._data) == 0:
            return None
        frame = self._data[: self._frame_samples]
        self._data = self._data[self._frame_samples:]
        if len(frame) == 0:
            return None
        return frame
