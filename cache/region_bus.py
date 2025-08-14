"""Stub module to emulate region-level cache discovery/invalidation.

In a production system, this would use actual networking or shared memory to
query neighbouring RSU caches. For now, it keeps a simple in-process registry
per region to demonstrate the flow.
"""
from __future__ import annotations

from typing import Any, Dict
from collections import defaultdict

# GLOBAL registry: region_id -> key -> value
_REGISTRY: Dict[int, Dict[str, Any]] = defaultdict(dict)


def register(region_id: int, key: str, value: Any) -> None:
    """Register a cache entry in the region-wide registry (called by RSU)."""
    _REGISTRY[region_id][key] = value


def query(region_id: int, key: str) -> Any | None:
    """Return cached value from region registry if present."""
    return _REGISTRY[region_id].get(key)


def invalidate(region_id: int, key: str) -> None:
    """Broadcast invalidation for a key (simply deletes from registry here)."""
    _REGISTRY[region_id].pop(key, None)


__all__ = ["register", "query", "invalidate"]
