"""62_ArcanisFederated — Privacy-preserving federated learning framework."""

from __future__ import annotations

import hashlib
import time
from dataclasses import dataclass, field
from typing import Any, Optional


@dataclass
class ModelUpdate:
    participant_id: str = ""
    weights: list[list[float]] = field(default_factory=list)
    num_samples: int = 0
    loss: float = 0.0
    timestamp: float = field(default_factory=time.time)
    checksum: str = ""


@dataclass
class GlobalModel:
    weights: list[list[float]] = field(default_factory=list)
    version: int = 0
    round: int = 0
    participants: int = 0
    avg_loss: float = 0.0


class SecureAggregator:
    def __init__(self):
        self._update_buffer: list[ModelUpdate] = []

    def add_update(self, update: ModelUpdate) -> None:
        if self._verify_checksum(update):
            self._update_buffer.append(update)

    def aggregate(self) -> Optional[GlobalModel]:
        if not self._update_buffer:
            return None

        total_samples = sum(u.num_samples for u in self._update_buffer)
        if total_samples == 0:
            return None

        weighted_weights: list[list[float]] = []
        for update in self._update_buffer:
            weight = update.num_samples / total_samples
            for i, layer in enumerate(update.weights):
                if i >= len(weighted_weights):
                    weighted_weights.append([0.0] * len(layer))
                for j, val in enumerate(layer):
                    if j < len(weighted_weights[i]):
                        weighted_weights[i][j] += val * weight

        avg_loss = sum(u.loss * u.num_samples for u in self._update_buffer) / total_samples
        participants = len(set(u.participant_id for u in self._update_buffer))

        model = GlobalModel(
            weights=weighted_weights,
            version=0,
            round=0,
            participants=participants,
            avg_loss=avg_loss,
        )
        self._update_buffer.clear()
        return model

    def _verify_checksum(self, update: ModelUpdate) -> bool:
        if not update.checksum:
            return True
        data = str(update.weights).encode()
        expected = hashlib.sha256(data).hexdigest()[:16]
        return update.checksum == expected

    def pending_count(self) -> int:
        return len(self._update_buffer)


class PrivacyEngine:
    def __init__(self, epsilon: float = 1.0, delta: float = 1e-5):
        self.epsilon = epsilon
        self.delta = delta

    def add_noise(self, weights: list[list[float]], sensitivity: float = 1.0) -> list[list[float]]:
        import random
        noise_scale = sensitivity / self.epsilon
        noisy: list[list[float]] = []
        for layer in weights:
            noisy_layer = [w + random.gauss(0, noise_scale) for w in layer]
            noisy.append(noisy_layer)
        return noisy

    def clip_gradients(self, weights: list[list[float]], max_norm: float = 1.0) -> list[list[float]]:
        clipped: list[list[float]] = []
        for layer in weights:
            norm = sum(w ** 2 for w in layer) ** 0.5
            if norm > max_norm:
                scale = max_norm / norm
                clipped.append([w * scale for w in layer])
            else:
                clipped.append(list(layer))
        return clipped


class FederatedCoordinator:
    def __init__(self, num_rounds: int = 10, min_participants: int = 2):
        self.num_rounds = num_rounds
        self.min_participants = min_participants
        self.aggregator = SecureAggregator()
        self.privacy = PrivacyEngine()
        self._global_model: Optional[GlobalModel] = None
        self._round_history: list[dict[str, Any]] = []
        self._initialized = False

    def initialize(self, initial_weights: Optional[list[list[float]]] = None) -> None:
        if initial_weights:
            self._global_model = GlobalModel(weights=initial_weights)
        self._initialized = True

    def receive_update(self, update: ModelUpdate) -> bool:
        update.weights = self.privacy.clip_gradients(update.weights)
        self.aggregator.add_update(update)
        return self.aggregator.pending_count() >= self.min_participants

    def run_round(self) -> Optional[GlobalModel]:
        model = self.aggregator.aggregate()
        if model:
            model.round = (self._global_model.round + 1) if self._global_model else 1
            model.version = (self._global_model.version + 1) if self._global_model else 1
            self._global_model = model
            self._round_history.append({
                "round": model.round,
                "participants": model.participants,
                "avg_loss": model.avg_loss,
                "timestamp": time.time(),
            })
        return model

    def get_global_model(self) -> Optional[GlobalModel]:
        return self._global_model

    def get_history(self) -> list[dict[str, Any]]:
        return list(self._round_history)

    def get_status(self) -> dict:
        return {
            "initialized": self._initialized,
            "current_round": self._global_model.round if self._global_model else 0,
            "total_rounds": self.num_rounds,
            "pending_updates": self.aggregator.pending_count(),
            "history": len(self._round_history),
        }
