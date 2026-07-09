"""Arcanis Research — centralized research tracking and knowledge base."""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Optional


class ResearchStatus(Enum):
    PROPOSED = "proposed"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    ABANDONED = "abandoned"
    DEFERRED = "deferred"


@dataclass
class ResearchTopic:
    topic_id: str = ""
    title: str = ""
    description: str = ""
    status: ResearchStatus = ResearchStatus.PROPOSED
    priority: int = 5
    tags: list[str] = field(default_factory=list)
    findings: list[str] = field(default_factory=list)
    references: list[str] = field(default_factory=list)
    created_at: float = field(default_factory=time.time)
    updated_at: float = field(default_factory=time.time)


class KnowledgeBase:
    def __init__(self):
        self._topics: dict[str, ResearchTopic] = {}
        self._counter = 0

    def add_topic(self, title: str, description: str = "", tags: list[str] | None = None) -> str:
        self._counter += 1
        topic_id = f"topic_{self._counter:04d}"
        self._topics[topic_id] = ResearchTopic(
            topic_id=topic_id, title=title, description=description,
            tags=tags or [], created_at=time.time(), updated_at=time.time(),
        )
        return topic_id

    def update_status(self, topic_id: str, status: ResearchStatus) -> bool:
        topic = self._topics.get(topic_id)
        if not topic:
            return False
        topic.status = status
        topic.updated_at = time.time()
        return True

    def add_finding(self, topic_id: str, finding: str) -> bool:
        topic = self._topics.get(topic_id)
        if not topic:
            return False
        topic.findings.append(finding)
        topic.updated_at = time.time()
        return True

    def add_reference(self, topic_id: str, reference: str) -> bool:
        topic = self._topics.get(topic_id)
        if not topic:
            return False
        topic.references.append(reference)
        topic.updated_at = time.time()
        return True

    def search(self, query: str) -> list[ResearchTopic]:
        query_lower = query.lower()
        results = []
        for topic in self._topics.values():
            if query_lower in topic.title.lower() or query_lower in topic.description.lower():
                results.append(topic)
            elif any(query_lower in tag.lower() for tag in topic.tags):
                results.append(topic)
            elif any(query_lower in finding.lower() for finding in topic.findings):
                results.append(topic)
        return results

    def get_topic(self, topic_id: str) -> Optional[ResearchTopic]:
        return self._topics.get(topic_id)

    def list_by_status(self, status: ResearchStatus) -> list[ResearchTopic]:
        return [t for t in self._topics.values() if t.status == status]

    def get_stats(self) -> dict:
        statuses = {}
        for t in self._topics.values():
            statuses[t.status.value] = statuses.get(t.status.value, 0) + 1
        return {"total_topics": len(self._topics), "by_status": statuses}
