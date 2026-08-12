"""Distributed cache management for VANET RSUs.

Each RSU maintains its own cache with coordination through the FL and RL agents.
"""
from __future__ import annotations

import logging
from typing import Dict, List, Any, Tuple, Optional

from .manager import CacheManager, is_placeholder
from .fl_agent import FLAdvisor
from .fl_aggregator import FLAggregator
from sdn_core.timing import estimate_proactive_computation_ms

logger = logging.getLogger(__name__)

class DistributedCacheManager:
    HOT_REPLICATION_INTERVAL = 100  # tasks
    HOT_TOP_K = 10
    ENABLE_AUTO_CACHE = True  # Global flag: if False, scheduler won't auto-cache
    ENABLE_CACHE_LOOKUP = True  # Global flag: if False, scheduler won't lookup cache
    ENABLE_FORWARDING = True    # Global flag: if False, only check local RSU cache

    """Manages distributed caches across multiple RSUs."""
    
    def __init__(self, rsu_ids: List[int], cache_capacity: int = 200, default_ttl: int = 300, eviction_policy: str = "LRU"):
        self.rsu_ids = rsu_ids
        self.cache_capacity = cache_capacity
        self.default_ttl = default_ttl
        self.eviction_policy = eviction_policy
        
        # Create individual cache for each RSU with proper capacity and eviction policy
        self.rsu_caches = {
            rid: CacheManager(capacity=cache_capacity, default_ttl=default_ttl, eviction_policy=eviction_policy)
            for rid in rsu_ids
        }
        # stats
        self.total_hits = 0
        self.total_misses = 0
        self._ops = 0  # operation counter

        # Speculative (FL-driven) computation accounting
        self.proactive_computations = 0
        self.proactive_compute_ms = 0.0
        self.proactive_hits = 0
        # Keys whose result was computed speculatively and not yet served. A key
        # leaves the set on first hit, so proactive_hits counts distinct useful
        # predictions rather than repeat accesses.
        self._proactive_keys: set[str] = set()
        
        # Initialize FLAdvisor clients for each RSU
        self.fl_clients = {rid: FLAdvisor() for rid in rsu_ids}
        # Initialize central FLAggregator
        self.fl_aggregator = FLAggregator(self.fl_clients)
    
    def lookup(self, key: str, rsu_id: int, enable_forwarding: bool = True) -> Any | None:
        """Lookup key in specified RSU cache with optional forwarding."""
        # Primary lookup at specified RSU
        result = self.rsu_caches[rsu_id].lookup(key)
        if result is not None:
            self.total_hits += 1
            self._credit_proactive(key)
            return result

        # If forwarding enabled (both per-call and global flag), check neighboring RSUs
        if enable_forwarding and self.ENABLE_FORWARDING:
            for neighbor_rsu in self.rsu_ids:
                if neighbor_rsu != rsu_id:
                    neighbor_result = self.rsu_caches[neighbor_rsu].lookup(key)
                    if neighbor_result is not None:
                        # Found in neighbor - replicate to primary RSU
                        self.rsu_caches[rsu_id].store(key, neighbor_result)
                        self.total_hits += 1
                        self._credit_proactive(key)
                        return neighbor_result

        # Complete miss
        self.total_misses += 1
        return None

    def _credit_proactive(self, key: str) -> None:
        """Mark a speculatively computed result as having paid off.

        Counted once per key: a prediction is useful or not, and repeat accesses
        should not inflate the precision figure.
        """
        if key in self._proactive_keys:
            self._proactive_keys.discard(key)
            self.proactive_hits += 1
    
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
        """Reserve space for a predicted-hot key without computing anything.

        Retained for the reservation-only ablation. The reservation holds no
        result, so a lookup against it is a miss until the scheduler stores a
        real one. See ``CacheManager.preplace``.
        """
        self.rsu_caches[rsu_id].preplace(key, ttl)

    def precompute(self, key: str, rsu_id: int, attrs: Dict[str, Any],
                   ttl: Optional[int] = None) -> Optional[float]:
        """Speculatively compute a predicted-hot result and cache it.

        This is what pre-placement actually costs: the RSU runs the task before
        anyone asks for it, pays the computation whether or not the prediction
        was right, and stores a genuine result.

        Returns:
            Computation time in ms, or None if the key already held a real
            result (nothing to recompute, nothing to charge).
        """
        cache = self.rsu_caches[rsu_id]
        existing = cache._store.get(key)
        if existing is not None and not is_placeholder(existing[1]):
            return None

        compute_ms = estimate_proactive_computation_ms(
            task_type=int(attrs.get("task_type", 0)),
            priority=int(attrs.get("priority", 1)),
            data_size_kb=int(attrs.get("data_size_kB", attrs.get("data_size", 500))),
            rsu_id=rsu_id,
        )

        # A speculatively computed result is indistinguishable from a reactively
        # computed one once cached; only its cost and provenance differ.
        cache.store(key, (1, compute_ms), ttl)

        self.proactive_computations += 1
        self.proactive_compute_ms += compute_ms
        self._proactive_keys.add(key)
        return compute_ms

    @property
    def total_preplacements(self) -> int:
        """Reservations made across all RSUs, for energy accounting."""
        return sum(cache.preplacements for cache in self.rsu_caches.values())

    @property
    def proactive_wasted(self) -> int:
        """Speculative computations never served before eviction or run end.

        This is the cost of FL mispredictions, and it is the number a reviewer
        will ask for when a paper claims predictive placement helps.
        """
        return max(self.proactive_computations - self.proactive_hits, 0)

    def proactive_stats(self) -> Dict[str, Any]:
        """Summary of speculative computation, for the result JSON."""
        computations = self.proactive_computations
        return {
            "proactive_computations": computations,
            "proactive_hits": self.proactive_hits,
            "proactive_wasted": self.proactive_wasted,
            "proactive_precision": (
                self.proactive_hits / computations if computations else 0.0
            ),
            "proactive_compute_ms": self.proactive_compute_ms,
        }
    
    # ---------------------------------------------------------------------
    # Federated-learning helpers
    # ---------------------------------------------------------------------
    def fl_observe_tasks(self, rsu_id: int, items: List[tuple[str, dict]]):
        """Pass task observations to the RSU-local FLAdvisor."""
        self.fl_clients[rsu_id].observe_tasks(items)

    def fl_observe_cache_result(self, rsu_id: int, key: str, hit: bool):
        self.fl_clients[rsu_id].observe_cache_result(key, hit)

    def fl_attrs(self, rsu_id: int, key: str) -> Dict[str, Any]:
        """Task attributes the RSU-local advisor last saw for a key."""
        return self.fl_clients[rsu_id].attrs_for(key)

    def fl_select_pool(self, rsu_id: int) -> List[str]:
        """Return keys to pre-place for a given RSU (after latest aggregation)."""
        return self.fl_clients[rsu_id].select_pool()

    def fl_step(self, timestep: int):
        """Run local updates + maybe aggregate."""
        # Local SGD happens inside each client when they observe tasks / results
        for adv in self.fl_clients.values():
            adv.maybe_fedavg_round()
        # Global aggregation
        round_freq = next(iter(self.fl_clients.values())).round_freq
        self.fl_aggregator.maybe_aggregate(timestep, round_freq)

    # ---------------------------------------------------------------------
    # Cache eviction (RL controlled)
    # ---------------------------------------------------------------------
    def evict_action(self, action: str, rsu_id: int) -> None:
        """Execute eviction action on specified RSU cache."""
        cache = self.rsu_caches[rsu_id]
        if action == "evict_lru":
            cache.evict_lru()
        elif action == "evict_random":
            cache.evict_random()
        elif action == "evict_lfu":
            cache.evict_lfu()
        elif action == "evict_fifo":
            cache.evict_fifo()
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

# Create distributed cache instance with moderate capacity to demonstrate policy differences
# 100 entries per RSU = 500 total
distributed_cache_manager = DistributedCacheManager(rsu_ids=[1, 2, 3, 4, 5], cache_capacity=100, default_ttl=30)

__all__ = ["DistributedCacheManager", "distributed_cache_manager"]
