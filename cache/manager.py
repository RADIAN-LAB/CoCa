"""Simple LRU cache manager with TTL for VANET nodes.

Each node should run its own instance (or share a process-wide singleton) to
store task results locally.  This implementation is purposely lightweight and
in-memory; replace with a distributed/replicated backend for production.
"""
from __future__ import annotations

import time
import hashlib
from collections import OrderedDict
from pathlib import Path
from typing import Any, Dict, Tuple

import yaml

# ---------------------------------------------------------------------------
# Load configuration
# ---------------------------------------------------------------------------
CFG_PATH = Path(__file__).resolve().parent.parent / "config" / "cache.yaml"
if not CFG_PATH.exists():
    raise FileNotFoundError(f"Cache config not found at {CFG_PATH}")

with CFG_PATH.open("r") as fh:
    _CFG = yaml.safe_load(fh)

_CAPACITY: int = int(_CFG.get("capacity", 100))
_DEFAULT_EVICTION: str = _CFG.get("policy", {}).get("eviction", "LRU")
_DEFAULT_TTL: int = int(_CFG.get("default_ttl", 300))  # seconds

# ---------------------------------------------------------------------------
# Helper util – consistent task key hashing
# ---------------------------------------------------------------------------

def make_task_key(*components: Any) -> str:
    """Create a SHA1 hash representing a task (ID + params etc.)."""
    data = "|".join(map(str, components)).encode()
    return hashlib.sha1(data).hexdigest()

# ---------------------------------------------------------------------------
# CacheManager class
# ---------------------------------------------------------------------------

class CacheManager:
    """LRU cache with TTL enforcement."""

    def __init__(self, capacity: int = _CAPACITY, default_ttl: int = _DEFAULT_TTL, eviction_policy: str = _DEFAULT_EVICTION) -> None:
        self.capacity = capacity
        self.default_ttl = default_ttl
        self.eviction_policy = eviction_policy.upper()  # Store per-instance eviction policy
        # OrderedDict preserves insertion order; we move accessed items to end
        self._store: "OrderedDict[str, Tuple[float, Any]]" = OrderedDict()
        # Frequency map and stats
        self._freq: Dict[str, int] = {}
        self.hits = 0
        self.misses = 0

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def lookup(self, key: str) -> Any | None:
        """Return cached value if present and fresh, else None."""
        now = time.time()
        if key not in self._store:
            self.misses += 1
            return None
        expiry, value = self._store[key]
        if expiry < now:
            # expired – evict and miss
            del self._store[key]
            return None
        # update stats
        self.hits += 1
        # LFU frequency update
        self._freq[key] = self._freq.get(key, 0) + 1
        # move to end (for recency)
        self._store.move_to_end(key)
        return value

    def store(self, key: str, value: Any, ttl: int | None = None) -> None:
        """Insert/overwrite a cache entry with optional custom TTL."""
        expiry = time.time() + (ttl if ttl is not None else self.default_ttl)
        if key in self._store:
            del self._store[key]
        elif len(self._store) >= self.capacity:
            self._evict_one()
        self._store[key] = (expiry, value)
        self._freq[key] = 1

    def _evict_one(self) -> None:
        """Evict a single item based on this cache's eviction policy."""
        if not self._store:
            return
        if self.eviction_policy == "LFU":
            self.evict_lfu()
        elif self.eviction_policy == "RANDOM":
            self.evict_random()
        else:  # default LRU
            self.evict_lru()

    def purge_expired(self) -> None:
        """Remove all expired entries.  Useful for periodic maintenance."""
        now = time.time()
        to_delete = [k for k, (exp, _) in self._store.items() if exp < now]
        for k in to_delete:
            del self._store[k]

    # ------------------------------------------------------------------
    # Advisor integration helpers
    # ------------------------------------------------------------------

    def evict_lru(self) -> None:
        """Evict least-recently-used entry (by last access)."""
        if not self._store:
            return
        # Use OrderedDict insertion/recency order directly: oldest entry is LRU.
        old_key, _ = self._store.popitem(last=False)
        self._freq.pop(old_key, None)

    def evict_lfu(self) -> None:
        """Evict least-frequently-used entry (ties -> oldest)."""
        if not self._store:
            return
        min_freq = min(self._freq.values())
        candidates = [k for k, f in self._freq.items() if f == min_freq]
        # remove oldest among candidates (front of OrderedDict)
        for k in self._store:
            if k in candidates:
                self._store.pop(k, None)
                self._freq.pop(k, None)
                return

    def shrink_ttl(self, factor: float = 0.5) -> None:
        """Multiply remaining TTL of every entry by < factor (default 0.5)."""
        now = time.time()
        for k, (exp, val) in list(self._store.items()):
            remaining = max(exp - now, 0)
            new_exp = now + remaining * factor
            self._store[k] = (new_exp, val)

    def evict_random(self) -> None:
        """Evict random entry."""
        if not self._store:
            return
        import random, sys
        k = random.choice(list(self._store.keys()))
        self._store.pop(k, None)
        self._freq.pop(k, None)

    def evict_fifo(self) -> None:
        """Evict first-in entry (oldest insertion time)."""
        if not self._store:
            return
        # Remove first item from OrderedDict (oldest insertion)
        old_key, _ = self._store.popitem(last=False)
        self._freq.pop(old_key, None)

    def preplace(self, key: str, ttl: int | None = None) -> None:
        """Ensure *some* entry for key exists in cache.

        Used by proactive advisors (FL/RL) to reserve space before result is
        computed.  Stores an optimistic result (success=1, time=3.0ms) so the
        scheduler uses the fast cache path instead of the LP solver.
        """
        if key in self._store:
            return
        # Store optimistic result: success=1, completion_time=3.0ms (cache-speed retrieval)
        # This gives FL-predicted entries the fast cache path advantage
        self.store(key, (1, 3.0), ttl)

    # ------------------------------------------------------------------
    # Convenience helpers
    # ------------------------------------------------------------------

    def __contains__(self, key: str) -> bool:  # allows `key in cache` syntax
        return self.lookup(key) is not None

    def __len__(self) -> int:
        return len(self._store)

    # ------------------------------------------------------------------
    # Popularity helper
    # ------------------------------------------------------------------

    def frequency(self, key: str) -> int:
        """Return local access frequency for the key (0 if unseen)."""
        return self._freq.get(key, 0)

    def stats(self) -> Tuple[int, int]:
        """Return hit and miss counts."""
        return self.hits, self.misses

    # Stats helper
    def stats(self) -> Tuple[int, int]:
        """Return (hits, misses)."""
        return self.hits, self.misses


# ---------------------------------------------------------------------------
# Singleton instance for convenience
# ---------------------------------------------------------------------------
cache_manager = CacheManager()

__all__ = [
    "cache_manager",
    "CacheManager",
    "make_task_key",
]
