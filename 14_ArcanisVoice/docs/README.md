# ArcanisVoice — Documentation

Natural, privacy-focused voice interaction system.

## Architecture

```
            ┌─────────────┐
 mic ──────▶│ AudioInput  │  (sounddevice, 16k mono int16)
            └──────┬──────┘
                   ▼
            ┌─────────────┐
            │ NoiseFilter │  (webrtc / spectral / high-pass)  [offline]
            └──────┬──────┘
                   ▼
        ┌──────────┴───────────┐
        ▼                      ▼
 ┌──────────────┐      ┌──────────────┐
 │ WakeWord     │      │   VAD / ASR  │  (Vosk offline, online fallback)
 │ Detector     │      └──────┬───────┘
 └──────┬───────┘             │ transcript
        │ wake                ▼
        └──────────▶  ┌──────────────┐
                      │ ArcanisBrain │  (context + conversation)  [offline fallback]
                      └──────┬───────┘
                             │ reply
                             ▼
                      ┌──────────────┐
                      │   TTS        │  (pyttsx3 / piper / online)
                      └──────┬───────┘
                             ▼
                        AudioOutput
```

All stages run locally by default. Network is only used when an explicit
online endpoint is configured (ASR/TTS/Brain). No audio or transcripts are
sent to third parties.

## Modules

| Module | Responsibility |
|--------|----------------|
| `config.py` | Load YAML config over safe dataclass defaults; env secret overrides |
| `audio_io.py` | Threaded mic capture + playback; `FileInput` for replay/tests |
| `noise_filter.py` | WebRTC comfort-gating, spectral gate, high-pass |
| `wake_word.py` | Builtin keyword spotting, Porcupine, Vosk-stream modes |
| `asr.py` | Vosk streaming ASR + online HTTP fallback |
| `tts.py` | pyttsx3/online TTS with rate/pitch/volume/voice profile |
| `brain.py` | ArcanisBrain client + rolling conversation context |
| `pipeline.py` | Real-time state machine: wake → capture → ASR → brain → TTS |
| `api.py` | FastAPI REST + WebSocket control/observability surface |
| `test_tools.py` | Mic/noise/wake/latency self-tests and benchmarks |
| `cli.py` | `run`, `api`, `test` entry points |

## Installation

```bash
pip install -r requirements.txt
# optional higher-quality offline TTS:
pip install piper-tts
# Vosk model (offline ASR):
#   download vosk-model-small-en-us-0.15 and place path in config.yaml
```

## Usage

```bash
# Run the full voice loop (mic → wake → speak)
python -m arcanis_voice.cli run

# Run pipeline + API server
python -m arcanis_voice.cli api

# Testing tools
python -m arcanis_voice.cli test mic
python -m arcanis_voice.cli test noise
python -m arcanis_voice.cli test wake
python -m arcanis_voice.cli test latency
python -m arcanis_voice.cli test selftest
```

## Configuration

See `config.yaml`. Key privacy/offline knobs:

- `asr.engine: vosk` — offline transcription.
- `tts.engine: pyttsx3` — offline synthesis.
- `brain.offline_mode: true` — never contact ArcanisBrain; use local response.
- `wake_word.model: builtin` — no model download required.

Secrets (`api_key`, `access_key`) can be injected via environment variables
instead of the file: `ARCANIS_BRAIN_KEY`, `ARCANIS_PORCUPINE_KEY`,
`ARCANIS_ASR_KEY`, `ARCANIS_TTS_KEY`.

## API Reference

| Method | Path | Purpose |
|--------|------|---------|
| GET | `/health` | liveness + backend availability |
| GET | `/config` | current config (secrets redacted) |
| POST | `/speak` | make assistant speak |
| POST | `/ask` | text-in → text-out (no mic) |
| POST | `/voice/reset` | clear conversation context |
| POST | `/voice/set` | update voice customization |
| WS | `/stream` | receive live events: `transcript`, `response`, `wake`, `state`, `barge_in`; send `{"action":"speak"/"ask","text":...}` |

## Privacy & Offline

- Default configuration performs all recognition/synthesis locally.
- Conversation history is kept in-process only; it is never persisted or
  transmitted unless an online endpoint is explicitly set.
- Online features are strictly opt-in per stage.

## Latency

The pipeline timestamps each stage (`brain_start/end`, `tts_start/end`) and
logs deltas. `test latency` reports TTS + Brain round-trip. For lowest
latency: keep `asr.engine: vosk`, `tts.engine: pyttsx3`, and avoid online
endpoints. Barge-in interrupts playback when the user starts speaking.
