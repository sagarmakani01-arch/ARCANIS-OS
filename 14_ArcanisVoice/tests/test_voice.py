"""Comprehensive tests for ArcanisVoice — config, utils, brain, noise filter, pipeline."""

import json
import os
import tempfile
import time
from collections import deque
from unittest.mock import MagicMock, patch

import numpy as np
import pytest

from arcanis_voice.config import (
    APIConfig,
    ASRConfig,
    AudioConfig,
    BrainConfig,
    Config,
    NoiseFilterConfig,
    PipelineConfig,
    TTSConfig,
    WakeWordConfig,
    load_config,
)
from arcanis_voice.utils import EventBus, Timing, setup_logging
from arcanis_voice.brain import ArcanisBrain, Conversation


# ===========================================================================
# 1. Config
# ===========================================================================

class TestAudioConfig:
    def test_defaults(self):
        cfg = AudioConfig()
        assert cfg.sample_rate == 16000
        assert cfg.channels == 1
        assert cfg.frame_ms == 30
        assert cfg.chunk == 1024

    def test_custom(self):
        cfg = AudioConfig(sample_rate=44100, channels=2)
        assert cfg.sample_rate == 44100
        assert cfg.channels == 2


class TestNoiseFilterConfig:
    def test_defaults(self):
        cfg = NoiseFilterConfig()
        assert cfg.enabled is True
        assert cfg.method == "webrtc"
        assert cfg.aggressiveness == 2


class TestWakeWordConfig:
    def test_defaults(self):
        cfg = WakeWordConfig()
        assert cfg.enabled is True
        assert cfg.model == "builtin"
        assert cfg.keyword == "arcanis"


class TestASRConfig:
    def test_defaults(self):
        cfg = ASRConfig()
        assert cfg.engine == "vosk"
        assert cfg.fallback_to_online is True


class TestTTSConfig:
    def test_defaults(self):
        cfg = TTSConfig()
        assert cfg.engine == "pyttsx3"
        assert cfg.rate == 175
        assert cfg.volume == 0.9


class TestBrainConfig:
    def test_defaults(self):
        cfg = BrainConfig()
        assert cfg.endpoint == "http://localhost:8001/v1/chat"
        assert cfg.timeout_s == 2.0
        assert cfg.offline_mode is False


class TestPipelineConfig:
    def test_defaults(self):
        cfg = PipelineConfig()
        assert cfg.low_latency is True
        assert cfg.barge_in is True
        assert cfg.vad_silence_ms == 700


class TestAPIConfig:
    def test_defaults(self):
        cfg = APIConfig()
        assert cfg.host == "0.0.0.0"
        assert cfg.port == 8000
        assert cfg.enable_websocket is True


class TestConfig:
    def test_creation(self):
        cfg = Config()
        assert isinstance(cfg.audio, AudioConfig)
        assert isinstance(cfg.noise_filter, NoiseFilterConfig)
        assert isinstance(cfg.wake_word, WakeWordConfig)
        assert isinstance(cfg.asr, ASRConfig)
        assert isinstance(cfg.tts, TTSConfig)
        assert isinstance(cfg.brain, BrainConfig)
        assert isinstance(cfg.pipeline, PipelineConfig)
        assert isinstance(cfg.api, APIConfig)

    def test_to_dict(self):
        cfg = Config()
        d = cfg.to_dict()
        assert "audio" in d
        assert "brain" in d
        assert d["audio"]["sample_rate"] == 16000

    def test_load_config_no_file(self):
        cfg = load_config(None)
        assert isinstance(cfg, Config)
        assert cfg.audio.sample_rate == 16000

    def test_load_config_nonexistent_file(self):
        cfg = load_config("/nonexistent/path.yaml")
        assert isinstance(cfg, Config)

    def test_load_config_from_yaml(self):
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            f.write("audio:\n  sample_rate: 44100\n  channels: 2\n")
            f.write("brain:\n  offline_mode: true\n")
            path = f.name
        try:
            cfg = load_config(path)
            assert cfg.audio.sample_rate == 44100
            assert cfg.audio.channels == 2
            assert cfg.brain.offline_mode is True
        finally:
            os.remove(path)

    def test_load_config_partial_yaml(self):
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            f.write("tts:\n  rate: 200\n")
            path = f.name
        try:
            cfg = load_config(path)
            assert cfg.tts.rate == 200
            assert cfg.audio.sample_rate == 16000  # default preserved
        finally:
            os.remove(path)

    def test_env_overrides(self):
        os.environ["ARCANIS_BRAIN_KEY"] = "test-secret-key"
        try:
            cfg = load_config(None)
            assert cfg.brain.api_key == "test-secret-key"
        finally:
            del os.environ["ARCANIS_BRAIN_KEY"]


# ===========================================================================
# 2. Utils
# ===========================================================================

class TestTiming:
    def test_mark_and_delta(self):
        t = Timing()
        t.mark("start")
        time.sleep(0.01)
        t.mark("end")
        delta = t.delta("start", "end")
        assert delta > 0

    def test_delta_missing_marks(self):
        t = Timing()
        assert t.delta("a", "b") == 0.0

    def test_mark_returns_timestamp(self):
        t = Timing()
        ts = t.mark("x")
        assert ts > 0


class TestEventBus:
    def test_subscribe_and_publish(self):
        bus = EventBus()
        received = []
        bus.subscribe("test", lambda x: received.append(x))
        bus.publish("test", "hello")
        assert received == ["hello"]

    def test_multiple_subscribers(self):
        bus = EventBus()
        results = []
        bus.subscribe("t", lambda x: results.append(1))
        bus.subscribe("t", lambda x: results.append(2))
        bus.publish("t")
        assert results == [1, 2]

    def test_publish_no_subscribers(self):
        bus = EventBus()
        bus.publish("nonexistent", "data")

    def test_handler_exception_does_not_propagate(self):
        bus = EventBus()
        bus.subscribe("t", lambda x: 1 / 0)
        bus.publish("t", "data")

    def test_multiple_topics(self):
        bus = EventBus()
        a, b = [], []
        bus.subscribe("a", lambda x: a.append(x))
        bus.subscribe("b", lambda x: b.append(x))
        bus.publish("a", 1)
        bus.publish("b", 2)
        assert a == [1]
        assert b == [2]


# ===========================================================================
# 3. Conversation
# ===========================================================================

class TestConversation:
    def test_add_and_history(self):
        conv = Conversation(max_turns=10)
        conv.add("user", "hello")
        conv.add("assistant", "hi there")
        history = conv.history()
        assert len(history) == 2
        assert history[0]["role"] == "user"
        assert history[1]["content"] == "hi there"

    def test_max_turns(self):
        conv = Conversation(max_turns=2)
        conv.add("user", "1")
        conv.add("assistant", "1")
        conv.add("user", "2")
        conv.add("assistant", "2")
        conv.add("user", "3")
        history = conv.history()
        assert len(history) <= 4

    def test_reset(self):
        conv = Conversation(max_turns=5)
        conv.add("user", "hello")
        conv.reset()
        assert conv.history() == []


# ===========================================================================
# 4. ArcanisBrain
# ===========================================================================

class TestArcanisBrain:
    def test_offline_mode(self):
        cfg = BrainConfig(offline_mode=True)
        brain = ArcanisBrain(cfg)
        reply = brain.respond("hello")
        assert "offline" in reply.lower()
        assert brain.conversation.history().__len__() == 2

    def test_empty_endpoint(self):
        cfg = BrainConfig(endpoint="")
        brain = ArcanisBrain(cfg)
        reply = brain.respond("test")
        assert "offline" in reply.lower()

    def test_conversation_context(self):
        cfg = BrainConfig(offline_mode=True, max_context_turns=5)
        brain = ArcanisBrain(cfg)
        brain.respond("first")
        brain.respond("second")
        history = brain.conversation.history()
        assert len(history) == 4
        assert history[0]["content"] == "first"
        assert history[2]["content"] == "second"

    def test_reset(self):
        cfg = BrainConfig(offline_mode=True)
        brain = ArcanisBrain(cfg)
        brain.respond("hello")
        brain.reset()
        assert brain.conversation.history() == []

    def test_extract_reply_openai_format(self):
        cfg = BrainConfig(offline_mode=True)
        brain = ArcanisBrain(cfg)
        data = {"choices": [{"message": {"content": "Hello!"}}]}
        reply = brain._extract_reply(data)
        assert reply == "Hello!"

    def test_extract_reply_reply_key(self):
        cfg = BrainConfig(offline_mode=True)
        brain = ArcanisBrain(cfg)
        data = {"reply": "Custom reply"}
        reply = brain._extract_reply(data)
        assert reply == "Custom reply"

    def test_extract_reply_response_key(self):
        cfg = BrainConfig(offline_mode=True)
        brain = ArcanisBrain(cfg)
        data = {"response": "Response text"}
        reply = brain._extract_reply(data)
        assert reply == "Response text"

    def test_extract_reply_unknown_format(self):
        cfg = BrainConfig(offline_mode=True)
        brain = ArcanisBrain(cfg)
        data = {"unknown": "format"}
        reply = brain._extract_reply(data)
        assert "unknown" in reply

    @patch("arcanis_voice.brain.requests.Session")
    def test_respond_success(self, mock_session_cls):
        mock_session = MagicMock()
        mock_resp = MagicMock()
        mock_resp.json.return_value = {"choices": [{"message": {"content": "AI reply"}}]}
        mock_resp.raise_for_status = MagicMock()
        mock_session.post.return_value = mock_resp
        mock_session_cls.return_value = mock_session

        cfg = BrainConfig(endpoint="http://test/v1/chat", api_key="key123")
        brain = ArcanisBrain(cfg)
        brain._session = mock_session
        reply = brain.respond("what is AI?")
        assert reply == "AI reply"
        mock_session.post.assert_called_once()

    @patch("arcanis_voice.brain.requests.Session")
    def test_respond_failure_fallback(self, mock_session_cls):
        mock_session = MagicMock()
        mock_session.post.side_effect = Exception("connection refused")
        mock_session_cls.return_value = mock_session

        cfg = BrainConfig(endpoint="http://test/v1/chat")
        brain = ArcanisBrain(cfg)
        brain._session = mock_session
        reply = brain.respond("hello")
        assert "offline" in reply.lower()

    def test_api_key_header(self):
        cfg = BrainConfig(api_key="secret123")
        brain = ArcanisBrain(cfg)
        assert brain._session.headers.get("Authorization") == "Bearer secret123"


# ===========================================================================
# 5. Noise Filter
# ===========================================================================

class TestNoiseFilter:
    def test_none_method(self):
        from arcanis_voice.noise_filter import NoiseFilter
        cfg = NoiseFilterConfig(enabled=False)
        nf = NoiseFilter(cfg, sample_rate=16000)
        pcm = np.array([100, -200, 300, -400], dtype=np.int16)
        result = nf.process(pcm)
        np.testing.assert_array_equal(result, pcm)

    def test_spectral_method(self):
        from arcanis_voice.noise_filter import NoiseFilter
        cfg = NoiseFilterConfig(enabled=True, method="spectral")
        nf = NoiseFilter(cfg, sample_rate=16000)
        pcm = np.sin(np.linspace(0, 2 * np.pi * 440, 480)).astype(np.float32)
        pcm = (pcm * 32767).astype(np.int16)
        result = nf.process(pcm)
        assert result.dtype == np.int16
        assert len(result) == len(pcm)

    def test_highpass_filter(self):
        from arcanis_voice.noise_filter import NoiseFilter
        cfg = NoiseFilterConfig(enabled=True, method="spectral", highpass_hz=100)
        nf = NoiseFilter(cfg, sample_rate=16000)
        # Generate low-frequency signal
        t = np.arange(480) / 16000.0
        low_freq = np.sin(2 * np.pi * 10 * t)  # 10 Hz
        pcm = (low_freq * 32767).astype(np.int16)
        result = nf.process(pcm)
        assert result.dtype == np.int16

    def test_short_frame(self):
        from arcanis_voice.noise_filter import NoiseFilter
        cfg = NoiseFilterConfig(enabled=True, method="spectral")
        nf = NoiseFilter(cfg, sample_rate=16000)
        pcm = np.array([100, -200, 300, -400, 500], dtype=np.int16)
        result = nf.process(pcm)
        assert result.dtype == np.int16
        assert len(result) > 0


# ===========================================================================
# 6. Pipeline (mocked hardware)
# ===========================================================================

class TestPipeline:
    @patch("arcanis_voice.audio_io.AudioInput")
    @patch("arcanis_voice.audio_io.AudioOutput")
    @patch("arcanis_voice.asr.SpeechRecognizer")
    @patch("arcanis_voice.tts.SpeechSynthesizer")
    @patch("arcanis_voice.wake_word.WakeWordDetector")
    def test_pipeline_init(self, mock_wake, mock_tts, mock_asr, mock_out, mock_in):
        from arcanis_voice.pipeline import VoicePipeline
        cfg = Config()
        pipeline = VoicePipeline(cfg)
        assert pipeline is not None

    @patch("arcanis_voice.audio_io.AudioInput")
    @patch("arcanis_voice.audio_io.AudioOutput")
    @patch("arcanis_voice.asr.SpeechRecognizer")
    @patch("arcanis_voice.tts.SpeechSynthesizer")
    @patch("arcanis_voice.wake_word.WakeWordDetector")
    def test_pipeline_brain_offline(self, mock_wake, mock_tts, mock_asr, mock_out, mock_in):
        from arcanis_voice.pipeline import VoicePipeline
        cfg = Config()
        cfg.brain.offline_mode = True
        pipeline = VoicePipeline(cfg)
        # Brain should be in offline mode
        assert pipeline.brain.cfg.offline_mode is True
