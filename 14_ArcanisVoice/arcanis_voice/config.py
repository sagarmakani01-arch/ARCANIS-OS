"""Configuration loading for ArcanisVoice."""
from __future__ import annotations

import os
from dataclasses import dataclass, field, asdict
from typing import Any

import yaml


@dataclass
class AudioConfig:
    sample_rate: int = 16000
    channels: int = 1
    device_input: int | None = None
    device_output: int | None = None
    frame_ms: int = 30
    chunk: int = 1024


@dataclass
class NoiseFilterConfig:
    enabled: bool = True
    method: str = "webrtc"
    aggressiveness: int = 2
    spectral_floor_db: float = -50.0
    highpass_hz: float = 80.0


@dataclass
class WakeWordConfig:
    enabled: bool = True
    model: str = "builtin"
    keyword: str = "arcanis"
    sensitivity: float = 0.6
    porcupine_keyword: str = "hey google"
    porcupine_access_key: str = ""


@dataclass
class ASRConfig:
    engine: str = "vosk"
    offline_model: str = "vosk-model-small-en-us-0.15"
    online_endpoint: str = ""
    online_api_key: str = ""
    fallback_to_online: bool = True


@dataclass
class TTSConfig:
    engine: str = "pyttsx3"
    voice_profile: str = "en-US"
    rate: int = 175
    pitch: int = 0
    volume: float = 0.9
    online_endpoint: str = ""
    online_api_key: str = ""


@dataclass
class BrainConfig:
    endpoint: str = "http://localhost:8001/v1/chat"
    api_key: str = ""
    model: str = "arcanis-brain"
    timeout_s: float = 2.0
    max_context_turns: int = 12
    offline_mode: bool = False


@dataclass
class PipelineConfig:
    low_latency: bool = True
    barge_in: bool = True
    vad_silence_ms: int = 700
    max_utterance_ms: int = 15000


@dataclass
class APIConfig:
    host: str = "0.0.0.0"
    port: int = 8000
    enable_websocket: bool = True


@dataclass
class Config:
    audio: AudioConfig = field(default_factory=AudioConfig)
    noise_filter: NoiseFilterConfig = field(default_factory=NoiseFilterConfig)
    wake_word: WakeWordConfig = field(default_factory=WakeWordConfig)
    asr: ASRConfig = field(default_factory=ASRConfig)
    tts: TTSConfig = field(default_factory=TTSConfig)
    brain: BrainConfig = field(default_factory=BrainConfig)
    pipeline: PipelineConfig = field(default_factory=PipelineConfig)
    api: APIConfig = field(default_factory=APIConfig)

    def to_dict(self) -> dict:
        return asdict(self)


_SECTION_CLASSES = {
    "audio": AudioConfig,
    "noise_filter": NoiseFilterConfig,
    "wake_word": WakeWordConfig,
    "asr": ASRConfig,
    "tts": TTSConfig,
    "brain": BrainConfig,
    "pipeline": PipelineConfig,
    "api": APIConfig,
}


def _apply_env_overrides(cfg: Config) -> None:
    """Allow secret overrides via environment variables."""
    env_map = {
        "ARCANIS_BRAIN_KEY": ("brain", "api_key"),
        "ARCANIS_BRAIN_ENDPOINT": ("brain", "endpoint"),
        "ARCANIS_PORCUPINE_KEY": ("wake_word", "porcupine_access_key"),
        "ARCANIS_ASR_KEY": ("asr", "online_api_key"),
        "ARCANIS_TTS_KEY": ("tts", "online_api_key"),
    }
    for env, (section, key) in env_map.items():
        if env in os.environ:
            setattr(getattr(cfg, section), key, os.environ[env])


def load_config(path: str | None = None) -> Config:
    """Load config from YAML, merging onto defaults.

    Missing sections/keys fall back to dataclass defaults so the system
    stays usable with a partial or absent config file (offline-first).
    """
    cfg = Config()
    if path is None:
        path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "config.yaml")
    if path and os.path.exists(path):
        with open(path, "r", encoding="utf-8") as fh:
            raw = yaml.safe_load(fh) or {}
        for section, klass in _SECTION_CLASSES.items():
            data = raw.get(section)
            if isinstance(data, dict):
                current = getattr(cfg, section)
                for k, v in data.items():
                    if hasattr(current, k):
                        setattr(current, k, v)
    _apply_env_overrides(cfg)
    return cfg
