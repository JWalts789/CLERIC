"""Persistent JSON-based memory store for research context.

Stores structured memory entries organized by topic, with each topic
persisted as a separate human-readable JSON file. Supports cross-session
research continuity, source attribution, and confidence tracking.
"""

import json
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


@dataclass
class MemoryEntry:
    """A single piece of stored research knowledge.

    Attributes:
        topic: The research topic this entry belongs to.
        key: A specific label within the topic (e.g., "GDP growth rate").
        value: The stored information (any JSON-serializable value).
        source: Which agent or process stored this entry.
        timestamp: ISO 8601 timestamp of when the entry was created.
        confidence: Confidence score from 0.0 (uncertain) to 1.0 (certain).
    """

    topic: str
    key: str
    value: Any
    source: str
    timestamp: str
    confidence: float


class MemoryStore:
    """Persistent, topic-partitioned memory store backed by JSON files.

    Each topic is stored in its own JSON file under the storage directory,
    making entries human-readable and easy to inspect. Entries are append-only
    within a topic, preserving the full research trail.
    """

    def __init__(self, storage_dir: str | Path) -> None:
        self._storage_dir = Path(storage_dir)
        self._storage_dir.mkdir(parents=True, exist_ok=True)

    def _topic_path(self, topic: str) -> Path:
        """Return the file path for a topic's JSON store."""
        safe_name = self._sanitize_topic(topic)
        return self._storage_dir / f"{safe_name}.json"

    @staticmethod
    def _sanitize_topic(topic: str) -> str:
        """Convert a topic string to a safe filename."""
        return "".join(c if c.isalnum() or c in "-_ " else "_" for c in topic).strip().replace(" ", "_").lower()

    def _load_topic(self, topic: str) -> list[dict[str, Any]]:
        """Load all entries for a topic from disk."""
        path = self._topic_path(topic)
        if not path.exists():
            return []
        with path.open("r", encoding="utf-8") as f:
            return json.load(f)

    def _save_topic(self, topic: str, entries: list[dict[str, Any]]) -> None:
        """Write all entries for a topic to disk."""
        path = self._topic_path(topic)
        with path.open("w", encoding="utf-8") as f:
            json.dump(entries, f, indent=2, ensure_ascii=False, default=str)

    def store(
        self,
        topic: str,
        key: str,
        value: Any,
        source: str,
        confidence: float = 1.0,
    ) -> None:
        """Store a memory entry, appending to the topic file.

        Args:
            topic: The research topic to file this under.
            key: A specific label for this piece of knowledge.
            value: The information to store (must be JSON-serializable).
            source: The agent or process that produced this entry.
            confidence: Confidence score between 0.0 and 1.0.

        Raises:
            ValueError: If confidence is outside [0.0, 1.0].
        """
        if not 0.0 <= confidence <= 1.0:
            raise ValueError(f"Confidence must be between 0.0 and 1.0, got {confidence}")

        entry = MemoryEntry(
            topic=topic,
            key=key,
            value=value,
            source=source,
            timestamp=datetime.now(timezone.utc).isoformat(),
            confidence=confidence,
        )

        entries = self._load_topic(topic)
        entries.append(asdict(entry))
        self._save_topic(topic, entries)

    def retrieve(self, topic: str, key: str | None = None) -> list[MemoryEntry]:
        """Retrieve memory entries for a topic.

        Args:
            topic: The research topic to retrieve entries for.
            key: Optional key to filter entries. If None, returns all entries.

        Returns:
            List of matching MemoryEntry objects, ordered by storage time.
        """
        raw_entries = self._load_topic(topic)
        entries = [MemoryEntry(**e) for e in raw_entries]

        if key is not None:
            entries = [e for e in entries if e.key == key]

        return entries

    def get_related_topics(self, query: str) -> list[str]:
        """Find topics related to a query using keyword matching.

        Performs case-insensitive matching of query words against
        existing topic names.

        Args:
            query: A search string to match against topic names.

        Returns:
            List of matching topic names, sorted alphabetically.
        """
        query_words = set(query.lower().split())
        related = []

        for path in self._storage_dir.glob("*.json"):
            topic_name = path.stem.replace("_", " ")
            topic_words = set(topic_name.lower().split())
            if query_words & topic_words:
                related.append(topic_name)

        return sorted(related)

    def get_topic_summary(self, topic: str) -> dict[str, Any]:
        """Return a summary of entries stored under a topic.

        Args:
            topic: The research topic to summarize.

        Returns:
            Dictionary with entry_count, sources, confidence_min,
            confidence_max, earliest_timestamp, and latest_timestamp.
            Returns an empty summary if the topic has no entries.
        """
        entries = self._load_topic(topic)

        if not entries:
            return {
                "entry_count": 0,
                "sources": [],
                "confidence_min": None,
                "confidence_max": None,
                "earliest_timestamp": None,
                "latest_timestamp": None,
            }

        confidences = [e["confidence"] for e in entries]
        timestamps = [e["timestamp"] for e in entries]
        sources = sorted(set(e["source"] for e in entries))

        return {
            "entry_count": len(entries),
            "sources": sources,
            "confidence_min": min(confidences),
            "confidence_max": max(confidences),
            "earliest_timestamp": min(timestamps),
            "latest_timestamp": max(timestamps),
        }

    def clear_topic(self, topic: str) -> None:
        """Remove all entries for a topic by deleting its file.

        Args:
            topic: The research topic to clear. No-op if topic doesn't exist.
        """
        path = self._topic_path(topic)
        if path.exists():
            path.unlink()
