"""Tests for verity.memory.store.MemoryStore."""

from pathlib import Path

import pytest

from verity.memory.store import MemoryStore, MemoryEntry


class TestMemoryStoreBasic:
    """Core store/retrieve functionality."""

    def test_store_and_retrieve_roundtrip(self, tmp_path: Path):
        store = MemoryStore(tmp_path / "mem")
        store.store("climate", "temp_rise", "1.5C by 2030", source="researcher", confidence=0.8)

        entries = store.retrieve("climate")
        assert len(entries) == 1
        assert entries[0].topic == "climate"
        assert entries[0].key == "temp_rise"
        assert entries[0].value == "1.5C by 2030"
        assert entries[0].source == "researcher"
        assert entries[0].confidence == 0.8
        assert entries[0].timestamp  # not empty

    def test_retrieve_with_key_filter(self, tmp_path: Path):
        store = MemoryStore(tmp_path / "mem")
        store.store("topic", "key_a", "value_a", source="s")
        store.store("topic", "key_b", "value_b", source="s")
        store.store("topic", "key_a", "value_a2", source="s")

        all_entries = store.retrieve("topic")
        assert len(all_entries) == 3

        filtered = store.retrieve("topic", key="key_a")
        assert len(filtered) == 2
        assert all(e.key == "key_a" for e in filtered)

    def test_retrieve_empty_topic(self, tmp_path: Path):
        store = MemoryStore(tmp_path / "mem")
        assert store.retrieve("nonexistent") == []

    def test_multiple_topics_stay_separate(self, tmp_path: Path):
        store = MemoryStore(tmp_path / "mem")
        store.store("alpha", "k", "v1", source="s")
        store.store("beta", "k", "v2", source="s")

        assert len(store.retrieve("alpha")) == 1
        assert len(store.retrieve("beta")) == 1
        assert store.retrieve("alpha")[0].value == "v1"

    def test_invalid_confidence_raises(self, tmp_path: Path):
        store = MemoryStore(tmp_path / "mem")
        with pytest.raises(ValueError, match="Confidence must be between"):
            store.store("t", "k", "v", source="s", confidence=1.5)
        with pytest.raises(ValueError, match="Confidence must be between"):
            store.store("t", "k", "v", source="s", confidence=-0.1)


class TestMemoryStoreTopics:
    """Topic-level operations: related topics, summary, clear."""

    def test_get_related_topics(self, tmp_path: Path):
        store = MemoryStore(tmp_path / "mem")
        store.store("climate change", "k", "v", source="s")
        store.store("climate policy", "k", "v", source="s")
        store.store("economics", "k", "v", source="s")

        related = store.get_related_topics("climate")
        assert len(related) == 2
        assert all("climate" in t for t in related)

    def test_get_related_topics_no_match(self, tmp_path: Path):
        store = MemoryStore(tmp_path / "mem")
        store.store("climate", "k", "v", source="s")
        assert store.get_related_topics("economics") == []

    def test_get_topic_summary(self, tmp_path: Path):
        store = MemoryStore(tmp_path / "mem")
        store.store("topic", "k1", "v1", source="agent_a", confidence=0.6)
        store.store("topic", "k2", "v2", source="agent_b", confidence=0.9)

        summary = store.get_topic_summary("topic")
        assert summary["entry_count"] == 2
        assert sorted(summary["sources"]) == ["agent_a", "agent_b"]
        assert summary["confidence_min"] == 0.6
        assert summary["confidence_max"] == 0.9
        assert summary["earliest_timestamp"] is not None
        assert summary["latest_timestamp"] is not None

    def test_get_topic_summary_empty(self, tmp_path: Path):
        store = MemoryStore(tmp_path / "mem")
        summary = store.get_topic_summary("nonexistent")
        assert summary["entry_count"] == 0
        assert summary["sources"] == []
        assert summary["confidence_min"] is None

    def test_clear_topic(self, tmp_path: Path):
        store = MemoryStore(tmp_path / "mem")
        store.store("topic", "k", "v", source="s")
        assert len(store.retrieve("topic")) == 1

        store.clear_topic("topic")
        assert store.retrieve("topic") == []

    def test_clear_nonexistent_topic_is_noop(self, tmp_path: Path):
        store = MemoryStore(tmp_path / "mem")
        store.clear_topic("nonexistent")  # should not raise


class TestMemoryStorePersistence:
    """Test that data survives across MemoryStore instances."""

    def test_persistence_across_instances(self, tmp_path: Path):
        mem_dir = tmp_path / "mem"

        store1 = MemoryStore(mem_dir)
        store1.store("science", "gravity", "9.81 m/s^2", source="physicist", confidence=1.0)

        # Create a brand-new instance pointing at the same directory
        store2 = MemoryStore(mem_dir)
        entries = store2.retrieve("science")

        assert len(entries) == 1
        assert entries[0].key == "gravity"
        assert entries[0].value == "9.81 m/s^2"
        assert entries[0].confidence == 1.0
