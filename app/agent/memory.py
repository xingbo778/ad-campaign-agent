"""
Agent memory: short-term (conversation) and long-term (campaign history).
"""

import json
import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class MemoryEntry:
    """A single memory entry."""
    key: str
    value: Any
    timestamp: float = field(default_factory=time.time)
    ttl: Optional[float] = None  # Time-to-live in seconds

    @property
    def expired(self) -> bool:
        if self.ttl is None:
            return False
        return (time.time() - self.timestamp) > self.ttl


class ShortTermMemory:
    """
    In-conversation memory for tracking tool calls, results, and reasoning.

    Automatically manages context window size by summarizing old entries.
    """

    def __init__(self, max_entries: int = 50):
        self.max_entries = max_entries
        self._entries: List[MemoryEntry] = []

    def add(self, key: str, value: Any, ttl: Optional[float] = None) -> None:
        """Add an entry to short-term memory."""
        self._entries.append(MemoryEntry(key=key, value=value, ttl=ttl))
        # Evict oldest if over limit
        if len(self._entries) > self.max_entries:
            self._entries = self._entries[-self.max_entries:]

    def get(self, key: str) -> Optional[Any]:
        """Get the most recent value for a key."""
        for entry in reversed(self._entries):
            if entry.key == key and not entry.expired:
                return entry.value
        return None

    def get_all(self, key: str) -> List[Any]:
        """Get all non-expired values for a key."""
        return [e.value for e in self._entries if e.key == key and not e.expired]

    def to_context_string(self, max_chars: int = 2000) -> str:
        """Convert memory to a context string for the LLM."""
        active = [e for e in self._entries if not e.expired]
        parts = []
        total_chars = 0
        for entry in reversed(active):
            entry_str = f"- {entry.key}: {json.dumps(entry.value, default=str)[:200]}"
            if total_chars + len(entry_str) > max_chars:
                break
            parts.append(entry_str)
            total_chars += len(entry_str)
        parts.reverse()
        return "\n".join(parts) if parts else ""

    def clear(self) -> None:
        self._entries.clear()


class LongTermMemory:
    """
    Persistent memory for campaign history and learned patterns.

    Currently in-memory; can be backed by a database in production.
    """

    def __init__(self):
        self._campaigns: List[Dict[str, Any]] = []

    def store_campaign_result(
        self,
        campaign_id: str,
        category: str,
        budget: float,
        products_count: int,
        creatives_count: int,
        performance: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Store a campaign result for future reference."""
        self._campaigns.append({
            "campaign_id": campaign_id,
            "category": category,
            "budget": budget,
            "products_count": products_count,
            "creatives_count": creatives_count,
            "performance": performance or {},
            "timestamp": time.time(),
        })

    def get_similar_campaigns(self, category: str, budget: float, limit: int = 3) -> List[Dict[str, Any]]:
        """Find similar past campaigns for reference."""
        # Simple similarity: same category, similar budget
        matches = []
        for campaign in self._campaigns:
            if campaign["category"].lower() == category.lower():
                budget_ratio = campaign["budget"] / budget if budget > 0 else 0
                if 0.5 <= budget_ratio <= 2.0:
                    matches.append(campaign)

        # Sort by recency
        matches.sort(key=lambda x: x["timestamp"], reverse=True)
        return matches[:limit]

    def get_context_string(self, category: str = "", budget: float = 0) -> str:
        """Get relevant campaign history as context string."""
        if not self._campaigns:
            return ""

        similar = self.get_similar_campaigns(category, budget)
        if not similar:
            return ""

        parts = ["Previous similar campaigns:"]
        for c in similar:
            perf = c.get("performance", {})
            roas = perf.get("roas", "N/A")
            parts.append(f"- {c['category']} campaign, budget=${c['budget']}, "
                         f"{c['products_count']} products, ROAS={roas}")
        return "\n".join(parts)
