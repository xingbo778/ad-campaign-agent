"""Tests for Agent memory: short-term and long-term."""

import time
import pytest
from app.agent.memory import ShortTermMemory, LongTermMemory, MemoryEntry


class TestMemoryEntry:
    def test_not_expired_without_ttl(self):
        entry = MemoryEntry(key="test", value="data")
        assert entry.expired is False

    def test_expired_with_ttl(self):
        entry = MemoryEntry(key="test", value="data", timestamp=time.time() - 10, ttl=5)
        assert entry.expired is True

    def test_not_expired_within_ttl(self):
        entry = MemoryEntry(key="test", value="data", timestamp=time.time(), ttl=60)
        assert entry.expired is False


class TestShortTermMemory:
    def test_add_and_get(self):
        memory = ShortTermMemory()
        memory.add("key1", "value1")
        assert memory.get("key1") == "value1"

    def test_get_missing_returns_none(self):
        memory = ShortTermMemory()
        assert memory.get("missing") is None

    def test_get_returns_most_recent(self):
        memory = ShortTermMemory()
        memory.add("key", "old")
        memory.add("key", "new")
        assert memory.get("key") == "new"

    def test_get_all(self):
        memory = ShortTermMemory()
        memory.add("key", "v1")
        memory.add("key", "v2")
        memory.add("other", "v3")
        assert memory.get_all("key") == ["v1", "v2"]

    def test_eviction_on_max_entries(self):
        memory = ShortTermMemory(max_entries=3)
        memory.add("a", 1)
        memory.add("b", 2)
        memory.add("c", 3)
        memory.add("d", 4)  # Should evict "a"
        assert memory.get("a") is None
        assert memory.get("d") == 4

    def test_expired_entries_skipped(self):
        memory = ShortTermMemory()
        memory.add("key", "old", ttl=0.001)
        time.sleep(0.01)
        assert memory.get("key") is None

    def test_to_context_string(self):
        memory = ShortTermMemory()
        memory.add("tool_result", {"products": 5})
        memory.add("step", "selected products")
        context = memory.to_context_string()
        assert "tool_result" in context
        assert "step" in context

    def test_to_context_string_max_chars(self):
        memory = ShortTermMemory()
        for i in range(100):
            memory.add(f"key_{i}", f"value_{i}" * 50)
        context = memory.to_context_string(max_chars=200)
        assert len(context) <= 500  # Some tolerance for entry formatting

    def test_clear(self):
        memory = ShortTermMemory()
        memory.add("key", "value")
        memory.clear()
        assert memory.get("key") is None


class TestLongTermMemory:
    def test_store_and_retrieve(self):
        memory = LongTermMemory()
        memory.store_campaign_result(
            campaign_id="c1", category="electronics", budget=5000.0,
            products_count=10, creatives_count=5,
        )
        results = memory.get_similar_campaigns("electronics", 5000.0)
        assert len(results) == 1
        assert results[0]["campaign_id"] == "c1"

    def test_similar_campaigns_filter_by_category(self):
        memory = LongTermMemory()
        memory.store_campaign_result("c1", "electronics", 5000.0, 10, 5)
        memory.store_campaign_result("c2", "fashion", 5000.0, 8, 4)
        results = memory.get_similar_campaigns("electronics", 5000.0)
        assert len(results) == 1
        assert results[0]["category"] == "electronics"

    def test_similar_campaigns_filter_by_budget(self):
        memory = LongTermMemory()
        memory.store_campaign_result("c1", "electronics", 5000.0, 10, 5)
        memory.store_campaign_result("c2", "electronics", 50000.0, 20, 10)  # Way different budget
        results = memory.get_similar_campaigns("electronics", 5000.0)
        assert len(results) == 1
        assert results[0]["campaign_id"] == "c1"

    def test_get_context_string_empty(self):
        memory = LongTermMemory()
        assert memory.get_context_string() == ""

    def test_get_context_string_with_data(self):
        memory = LongTermMemory()
        memory.store_campaign_result(
            "c1", "electronics", 5000.0, 10, 5, performance={"roas": 3.2}
        )
        context = memory.get_context_string("electronics", 5000.0)
        assert "electronics" in context
        assert "3.2" in context

    def test_limit(self):
        memory = LongTermMemory()
        for i in range(10):
            memory.store_campaign_result(f"c{i}", "electronics", 5000.0, 10, 5)
        results = memory.get_similar_campaigns("electronics", 5000.0, limit=3)
        assert len(results) == 3
