"""VoicePipeline: the real-time, low-latency orchestrator.

Loop:
  [listen for wake word] -> [collect utterance via VAD] -> [ASR]
  -> [ArcanisBrain] -> [TTS] -> [playback] -> (barge-in) repeat

Built for low latency and offline operation. Each stage is timed and an
optional event callback receives lifecycle events for UI/API binding.
"""
from __future__ import annotations

import threading
import time
from typing import Callable, Optional

import numpy as np

from . import audio_io, asr, brain, noise_filter, tts, wake_word
from .config import Config
from .utils import EventBus, Timing, logger


class VoicePipeline:
    def __init__(self, cfg: Config, event_bus: EventBus | None = None,
                 input_stream=None, output_stream=None) -> None:
        self.cfg = cfg
        self.bus = event_bus or EventBus()
        self.timing = Timing()
        self.running = threading.Event()

        self.input = input_stream or audio_io.AudioInput(cfg.audio)
        self.output = output_stream or audio_io.AudioOutput(cfg.audio)
        self.noise = noise_filter.NoiseFilter(cfg.noise_filter, cfg.audio.sample_rate)
        self.wake = wake_word.WakeWordDetector(cfg.wake_word, cfg.audio.sample_rate)
        self.recognizer = asr.SpeechRecognizer(cfg.asr, cfg.audio.sample_rate)
        self.synth = tts.SpeechSynthesizer(cfg.tts, cfg.audio)
        self.brain = brain.ArcanisBrain(cfg.brain)

        self._tts_playing = threading.Event()
        self._speak_thread: Optional[threading.Thread] = None

    # ---- event helpers ----
    def _emit(self, topic: str, payload=None) -> None:
        self.bus.publish(topic, payload)

    # ---- state machine ----
    def run(self) -> None:
        self.running.set()
        self.input.start()
        logger.info("ArcanisVoice pipeline started")
        try:
            while self.running.is_set():
                if self.wake.enabled:
                    self._emit("state", "listening_for_wake")
                    if not self._wait_for_wake():
                        continue
                self._emit("state", "capturing")
                utterance = self._capture_utterance()
                if not utterance:
                    continue
                text = self.recognizer.transcribe(utterance)
                if not text:
                    continue
                self._emit("transcript", text)
                self.timing.mark("brain_start")
                reply = self.brain.respond(text)
                self.timing.mark("brain_end")
                self._emit("response", reply)
                self.timing.mark("tts_start")
                self._speak(reply)
                self.timing.mark("tts_end")
                self._log_latency()
        finally:
            self.input.stop()
            self.output.stop()
            self.wake.close()
            logger.info("pipeline stopped")

    def _wait_for_wake(self) -> bool:
        silence = 0
        while self.running.is_set():
            frame = self.input.read_frame(timeout=1.0)
            if frame is None:
                continue
            clean = self.noise.process(frame)
            # porcupine path
            if self.wake.process(clean):
                self._emit("wake", True)
                logger.info("wake word detected (model)")
                return True
            # builtin/vosk path: feed partials
            if self.wake.model in ("builtin", "vosk"):
                partial = self.recognizer._partial_vosk(clean)
                if partial and self.wake.feed_text(partial):
                    self._emit("wake", True)
                    logger.info("wake word detected (text): %s", partial)
                    return True
        return False

    def _capture_utterance(self) -> list[np.ndarray]:
        """Collect frames until VAD silence or max duration."""
        frames: list[np.ndarray] = []
        silence_ms = 0
        max_ms = self.cfg.pipeline.max_utterance_ms
        frame_ms = self.cfg.audio.frame_ms
        for _ in range(int(max_ms / frame_ms)):
            frame = self.input.read_frame(timeout=1.0)
            if frame is None:
                continue
            clean = self.noise.process(frame)
            frames.append(clean)
            if self.cfg.pipeline.barge_in and self._tts_playing.is_set():
                self._emit("barge_in", True)
                self._stop_speaking()
                break
            # simple energy-based silence detection on cleaned frame
            energy = np.abs(clean.astype(np.float32)).mean()
            if energy < 200:
                silence_ms += frame_ms
                if silence_ms >= self.cfg.pipeline.vad_silence_ms:
                    break
            else:
                silence_ms = 0
        return frames

    def _speak(self, text: str) -> None:
        pcm = self.synth.synthesize(text)
        if pcm is None:
            return
        self._tts_playing.set()
        try:
            self.output.play(pcm)
        finally:
            self._tts_playing.clear()

    def _stop_speaking(self) -> None:
        try:
            self.output.stop()
        except Exception:  # noqa: BLE001
            pass
        self._tts_playing.clear()

    def _log_latency(self) -> None:
        b = self.timing.delta("brain_start", "brain_end")
        t = self.timing.delta("tts_start", "tts_end")
        logger.info("latency | brain=%.2fs tts=%.2fs", b, t)

    def stop(self) -> None:
        self.running.clear()
        self._stop_speaking()

    def say(self, text: str) -> None:
        """External API hook to make the assistant speak."""
        self._speak(text)
