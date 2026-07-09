# ArcanisVoice

A natural, privacy-focused voice interaction system.

- **Wake word detection** (offline, lightweight)
- **Speech recognition** (offline Vosk + online fallback)
- **Noise filtering** (webrtc + spectral gate)
- **Natural speech generation** (offline espeak/piper + online TTS)
- **Voice customization** (pitch, rate, voice profile)
- **Real-time, low-latency pipeline**
- **ArcanisBrain AI integration** with context-aware conversation
- Offline-capable, privacy-first design

## Quick start

```bash
pip install -r requirements.txt
python -m arcanis_voice.cli
```

See [docs/](docs/) for details.
