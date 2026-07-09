"""Testing and benchmarking tools for ArcanisVoice."""
from __future__ import annotations

import time

import numpy as np

from . import audio_io, noise_filter, asr, tts, wake_word, brain
from .config import Config
from .utils import logger


def test_microphone(cfg: Config, seconds: float = 3.0) -> None:
    """Capture from mic and report level / device health."""
    inp = audio_io.AudioInput(cfg.audio)
    inp.start()
    print(f"Capturing {seconds}s of audio from input device...")
    n = int(seconds * 1000 / cfg.audio.frame_ms)
    peak = 0
    for _ in range(n):
        f = inp.read_frame(timeout=1.0)
        if f is not None:
            peak = max(peak, int(np.abs(f.astype(np.float32)).max()))
    inp.stop()
    print(f"Mic test done. Peak amplitude: {peak} (0-32767). "
          f"{'OK' if peak > 500 else 'LOW SIGNAL — check mic/levels'}")
    if peak < 500:
        print("Tip: increase input gain or check the selected device.")


def test_noise_filter(cfg: Config, seconds: float = 3.0) -> None:
    inp = audio_io.AudioInput(cfg.audio)
    nf = noise_filter.NoiseFilter(cfg.noise_filter, cfg.audio.sample_rate)
    inp.start()
    print(f"Filtering {seconds}s of audio (method={cfg.noise_filter.method})...")
    n = int(seconds * 1000 / cfg.audio.frame_ms)
    before = after = 0
    for _ in range(n):
        f = inp.read_frame(timeout=1.0)
        if f is None:
            continue
        before += float(np.abs(f.astype(np.float32)).mean())
        out = nf.process(f)
        after += float(np.abs(out.astype(np.float32)).mean())
    inp.stop()
    b, a = (before / max(n, 1)), (after / max(n, 1))
    print(f"Mean energy before={b:.1f} after={a:.1f} reduction={100*(1-a/max(b,1e-6)):.0f}%")


def test_wake_word(cfg: Config, seconds: float = 10.0) -> None:
    inp = audio_io.AudioInput(cfg.audio)
    ww = wake_word.WakeWordDetector(cfg.wake_word, cfg.audio.sample_rate)
    rec = asr.SpeechRecognizer(cfg.asr, cfg.audio.sample_rate)
    inp.start()
    print(f"Say the wake word '{cfg.wake_word.keyword}' within {seconds}s...")
    n = int(seconds * 1000 / cfg.audio.frame_ms)
    for _ in range(n):
        f = inp.read_frame(timeout=1.0)
        if f is None:
            continue
        if ww.process(f):
            print("Detected via model!")
            break
        if ww.model in ("builtin", "vosk"):
            p = rec._partial_vosk(f)
            if p and ww.feed_text(p):
                print(f"Detected via transcript: '{p}'")
                break
    else:
        print("No wake word detected in time window.")
    inp.stop()
    ww.close()


def bench_latency(cfg: Config, text: str = "Hello Arcanis, what is the time?") -> None:
    """Measure TTS + Brain latency."""
    synth = tts.SpeechSynthesizer(cfg.tts, cfg.audio)
    br = brain.ArcanisBrain(cfg.brain)
    t0 = time.perf_counter()
    pcm = synth.synthesize(text)
    t1 = time.perf_counter()
    t2 = time.perf_counter()
    reply = br.respond(text)
    t3 = time.perf_counter()
    print(f"TTS synthesis: {(t1-t0)*1000:.1f} ms ({'OK' if pcm is not None else 'FAILED'})")
    print(f"Brain respond:  {(t3-t2)*1000:.1f} ms")
    print(f"Reply: {reply[:120]}")


def run_self_test(cfg: Config) -> None:
    print("=== ArcanisVoice self-test ===")
    br = brain.ArcanisBrain(cfg.brain)
    print("Brain offline reply:", br.respond("test")[:60], "...")
    synth = tts.SpeechSynthesizer(cfg.tts, cfg.audio)
    print("TTS available:", synth._engine is not None or synth._online)
    rec = asr.SpeechRecognizer(cfg.asr, cfg.audio.sample_rate)
    print("ASR available:", rec.available)
    print("=== done ===")
