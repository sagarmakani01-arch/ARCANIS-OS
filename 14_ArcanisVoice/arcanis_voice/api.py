"""REST + WebSocket API for ArcanisVoice.

Exposes:
  GET  /health              - liveness + backend availability
  GET  /config              - current configuration (secrets redacted)
  POST /speak               - make the assistant speak
  POST /ask                 - text-in, text-out (bypass mic)
  POST /voice/reset         - reset conversation context
  POST /voice/set           - update TTS voice customization
  WS   /stream              - bidirectional: send text, receive events

The API binds to an existing VoicePipeline instance. Audio capture still
runs in-process; the API is a control/observability surface.
"""
from __future__ import annotations

import threading
from typing import Any

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from pydantic import BaseModel

from .pipeline import VoicePipeline
from .utils import logger


class SpeakRequest(BaseModel):
    text: str


class AskRequest(BaseModel):
    text: str


class VoiceSettings(BaseModel):
    profile: str | None = None
    rate: int | None = None
    pitch: int | None = None
    volume: float | None = None


def _redact(cfg: dict) -> dict:
    out = dict(cfg)
    for section in ("brain", "asr", "tts", "wake_word"):
        if section in out and isinstance(out[section], dict):
            for key in list(out[section]):
                if "key" in key.lower() or "secret" in key.lower():
                    out[section][key] = "***"
    return out


def create_app(pipeline: VoicePipeline) -> FastAPI:
    app = FastAPI(title="ArcanisVoice", version="0.1.0")

    @app.get("/health")
    def health() -> dict:
        return {
            "status": "ok",
            "running": pipeline.running.is_set(),
            "asr_available": pipeline.recognizer.available,
            "wake_enabled": pipeline.wake.enabled,
        }

    @app.get("/config")
    def get_config() -> dict:
        return _redact(pipeline.cfg.to_dict())

    @app.post("/speak")
    def speak(req: SpeakRequest) -> dict:
        threading.Thread(target=pipeline._speak, args=(req.text,), daemon=True).start()
        return {"queued": True, "text": req.text}

    @app.post("/ask")
    def ask(req: AskRequest) -> dict:
        reply = pipeline.brain.respond(req.text)
        return {"reply": reply}

    @app.post("/voice/reset")
    def reset() -> dict:
        pipeline.brain.reset()
        return {"reset": True}

    @app.post("/voice/set")
    def set_voice(req: VoiceSettings) -> dict:
        pipeline.synth.set_voice(req.profile, req.rate, req.pitch, req.volume)
        return {"applied": True}

    @app.websocket("/stream")
    async def stream(ws: WebSocket) -> None:
        await ws.accept()
        pipeline.bus.subscribe("transcript", lambda p: _send(ws, "transcript", p))
        pipeline.bus.subscribe("response", lambda p: _send(ws, "response", p))
        pipeline.bus.subscribe("wake", lambda p: _send(ws, "wake", p))
        pipeline.bus.subscribe("state", lambda p: _send(ws, "state", p))
        pipeline.bus.subscribe("barge_in", lambda p: _send(ws, "barge_in", p))
        try:
            while True:
                data = await ws.receive_text()
                # Client can push text to make assistant speak or ask.
                msg = _parse(data)
                if msg.get("action") == "speak":
                    pipeline.say(msg.get("text", ""))
                elif msg.get("action") == "ask":
                    reply = pipeline.brain.respond(msg.get("text", ""))
                    await ws.send_json({"event": "response", "payload": reply})
        except WebSocketDisconnect:
            logger.info("websocket client disconnected")

    return app


async def _send(ws: WebSocket, event: str, payload: Any) -> None:
    try:
        await ws.send_json({"event": event, "payload": payload})
    except Exception:  # noqa: BLE001
        pass


def _parse(data: str) -> dict:
    import json
    try:
        return json.loads(data)
    except Exception:  # noqa: BLE001
        return {}
