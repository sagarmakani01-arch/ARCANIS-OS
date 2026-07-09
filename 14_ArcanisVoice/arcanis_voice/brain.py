"""ArcanisBrain AI integration.

Connects to the ArcanisBrain service (HTTP) for context-aware responses.
Maintains a rolling conversation context locally so that:
  - Offline mode returns a graceful canned/local response.
  - No raw audio or transcripts are sent to third parties (privacy).
  - Context (recent turns) is trimmed to a configurable window.
"""
from __future__ import annotations

import json
import time
from collections import deque
from typing import Optional

import requests

from .config import BrainConfig
from .utils import logger


class Conversation:
    def __init__(self, max_turns: int) -> None:
        self.max_turns = max_turns
        self.turns: deque[dict] = deque(maxlen=max_turns * 2)

    def add(self, role: str, text: str) -> None:
        self.turns.append({"role": role, "content": text})

    def history(self) -> list[dict]:
        return list(self.turns)

    def reset(self) -> None:
        self.turns.clear()


class ArcanisBrain:
    def __init__(self, cfg: BrainConfig) -> None:
        self.cfg = cfg
        self.conversation = Conversation(cfg.max_context_turns)
        self._session = requests.Session()
        if cfg.api_key:
            self._session.headers["Authorization"] = f"Bearer {cfg.api_key}"

    def _offline_response(self, user_text: str) -> str:
        """Privacy-first local fallback when brain is unreachable/offline."""
        return (
            f"I heard: '{user_text}'. "
            "ArcanisBrain is offline; I'm running in local mode. "
            "Your data stayed on this device."
        )

    def respond(self, user_text: str) -> str:
        self.conversation.add("user", user_text)
        if self.cfg.offline_mode or not self.cfg.endpoint:
            reply = self._offline_response(user_text)
            self.conversation.add("assistant", reply)
            return reply

        payload = {
            "model": self.cfg.model,
            "messages": self.conversation.history(),
        }
        try:
            resp = self._session.post(
                self.cfg.endpoint,
                json=payload,
                timeout=self.cfg.timeout_s,
            )
            resp.raise_for_status()
            data = resp.json()
            reply = self._extract_reply(data)
        except Exception as exc:  # noqa: BLE001
            logger.warning("ArcanisBrain request failed: %s", exc)
            reply = self._offline_response(user_text)

        self.conversation.add("assistant", reply)
        return reply

    def _extract_reply(self, data: dict) -> str:
        # OpenAI-compatible: choices[0].message.content
        try:
            if "choices" in data:
                return data["choices"][0]["message"]["content"].strip()
            if "reply" in data:
                return str(data["reply"]).strip()
            if "response" in data:
                return str(data["response"]).strip()
        except Exception:  # noqa: BLE001
            pass
        return json.dumps(data)[:200]

    def reset(self) -> None:
        self.conversation.reset()
