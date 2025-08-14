"""Distributed cache management for VANET RSUs.

Each RSU maintains its own cache with coordination through the FL and RL agents.
"""
from __future__ import annotations

import time
import logging
from typing import Dict, List, Any, Tuple, Optional
from collections import defaultdict

from .manager import CacheManager

logger = logging.getLogger(__name__)

class DistributedCacheManager:
    HOT_REPLICATION_INTERVAL = 100  # tasks
    HOT_TOP_K = 10

    """Manages distributed caches across multiple RSUs."""
    
    def __init__(self, rsu_ids: List[int], cache_capacity: int = 200, default_ttl: int = 300):
        self.rsu_ids = rsu_ids
        self.cache_capacity = cache_capacity
        self.default_ttl = default_ttl
        
        # Create individual cache for each RSU
        self.rsu_caches = {rid: CacheManager() for rid in rsu_ids}
        self.rsu_ids = rsu_ids
        # stats
        self.total_hits = 0
        self.total_misses = 0
        self._ops = 0  # operation counter
        
    def lookup(self, key: str, rsu_id: int, enable_forwarding: bool = True) -> Any | None:
        """Lookup key in specified RSU cache with optional forwarding."""
        # Primary lookup at specified RSU
        result = self.rsu_caches[rsu_id].lookup(key)
        if result is not None:
            self.total_hits += 1
            return result
            
        # If forwarding enabled, check neighboring RSUs
        if enable_forwarding:
            for neighbor_rsu in self.rsu_ids:
                if neighbor_rsu != rsu_id:
                    neighbor_result = self.rsu_caches[neighbor_rsu].lookup(key)
                    if neighbor_result is not None:
                        # Found in neighbor - replicate to primary RSU
                        self.rsu_caches[rsu_id].store(key, neighbor_result)
                        self.total_hits += 1
                        return neighbor_result
        
        # Complete miss
        self.total_misses += 1
        return None
    
    def store(self, key: str, value: Any, rsu_id: int, ttl: Optional[int] = None,
              admission_threshold: int = 1, hot_threshold: int = 2, replicate: bool = True) -> None:
        # Increment global op counter for periodic hot replication
        self._ops += 1
        if self._ops % self.HOT_REPLICATION_INTERVAL == 0:
            self.replicate_hot()

        """Store key-value pair in specified RSU cache.
        Admission: only store if local frequency after insert ≥ admission_threshold.
        If the key becomes *hot* (frequency ≥ hot_threshold), optionally replicate to neighbours.
        """
        cache = self.rsu_caches[rsu_id]
        prev_freq = cache.frequency(key)
        # Perform admission check
        will_freq = prev_freq + 1
        if will_freq < admission_threshold:
            # Skip storing yet; it hasn't reached admission threshold
            return
        cache.store(key, value, ttl)
        if replicate and cache.frequency(key) >= hot_threshold:
            for nbr in self.rsu_ids:
                if nbr != rsu_id:
                    self.rsu_caches[nbr].store(key, value, ttl)
    
    def replicate_hot(self) -> None:
        """Replicate top-K hot keys from each RSU to all other RSUs."""
        for rsu_id, cache in self.rsu_caches.items():
            # sort keys by frequency desc
            hot_keys = sorted(cache._freq.items(), key=lambda kv: kv[1], reverse=True)[:self.HOT_TOP_K]
            for key, _ in hot_keys:
                value = cache.lookup(key)  # returns None if expired
                if value is None:
                    continue
                for nbr in self.rsu_ids:
                    if nbr != rsu_id:
                        self.rsu_caches[nbr].store(key, value, None)

    def preplace(self, key: str, rsu_id: int, ttl: Optional[int] = None) -> None:
        """Pre-place placeholder in specified RSU cache."""
        self.rsu_caches[rsu_id].preplace(key, ttl)
    
    def get_rsu_state(self, rsu_id: int):
        """Return cache_usage (0-1) and hit_rate for an RSU."""
        cache = self.rsu_caches[rsu_id]
        usage = len(cache) / (getattr(cache, "_capacity", len(cache) or 1))
        hits, misses = cache.stats()
        hit_rate = hits / (hits + misses + 1e-9)
        return {"cache_usage": usage, "hit_rate": hit_rate}

    def get_aggregated_state(self):
        """Aggregate usage and hit_rate across all RSUs."""
        usages = []
        hit_rates = []
        for rid in self.rsu_ids:
            st = self.get_rsu_state(rid)
            usages.append(st["cache_usage"])
            hit_rates.append(st["hit_rate"])
        return {
            "cache_usage": sum(usages) / len(usages),
            "hit_rate": sum(hit_rates) / len(hit_rates),
        }

    def evict_action(self, action: str, rsu_id: int) -> None:
        """Execute eviction action on specified RSU cache."""
        cache = self.rsu_caches[rsu_id]
        if action == "evict_lru":
            cache.evict_lru()
        elif action == "evict_random":
            cache.evict_random()
        elif action == "evict_lfu":
            cache.evict_lfu()
        elif action == "shrink_ttl":
            cache.shrink_ttl()
    
    def get_global_stats(self) -> Tuple[int, int]:
        """Get aggregated hit/miss stats across all RSUs."""
        return self.total_hits, self.total_misses
    
    def popular_keys(self, rsu_id: int, min_freq: int = 2, top_k: int = 10) -> List[Tuple[str, int]]:
        """Return keys whose local frequency >= min_freq sorted by freq desc."""
        if rsu_id not in self.rsu_caches:
            return []
        cache = self.rsu_caches[rsu_id]
        freq_pairs = [(k, f) for k, f in cache._freq.items() if f >= min_freq]
        return sorted(freq_pairs, key=lambda t: t[1], reverse=True)[:top_k]

    def get_rsu_state(self, rsu_id: int) -> Dict[str, float]:
        """Get cache state for a specific RSU.
        
        Args:
            rsu_id: ID of the RSU to get state for
            
        Returns:
            Dictionary with RSU cache state metrics
        """
        if rsu_id not in self.rsu_caches:
            return {"cache_usage": 0.0, "entries": 0, "capacity": 0}
        
        cache = self.rsu_caches[rsu_id]
        return {
            "cache_usage": len(cache._store) / cache.capacity,
            "entries": len(cache._store),
            "capacity": cache.capacity,
            "hit_rate": cache.hits / (cache.hits + cache.misses + 1e-9)
        }
    
    def get_aggregated_state(self) -> Dict[str, float]:
        """Get aggregated cache state across all RSUs."""
        total_capacity = sum(cache.capacity for cache in self.rsu_caches.values())
        total_entries = sum(len(cache._store) for cache in self.rsu_caches.values())
        
        return {
            "cache_usage": total_entries / total_capacity,
            "hit_rate": self.total_hits / (self.total_hits + self.total_misses + 1e-9),
            "total_entries": total_entries,
        }

# Create distributed cache instance
distributed_cache_manager = DistributedCacheManager(rsu_ids=[1, 2, 3, 4, 5])

__all__ = ["DistributedCacheManager", "distributed_cache_manager"]
