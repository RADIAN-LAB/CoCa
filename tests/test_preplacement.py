"""Pre-placement must reserve space without fabricating a result.

``preplace`` previously stored ``(success=1, completion_time=3.0)`` for a task
that had never been computed, so every later lookup counted as a hit on an
invented result. These tests pin the corrected behaviour.
"""
from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from cache.distributed_manager import DistributedCacheManager
from cache.manager import PLACEHOLDER, CacheManager, is_placeholder, make_task_key


def _cache(**kwargs) -> CacheManager:
    kwargs.setdefault("capacity", 8)
    kwargs.setdefault("default_ttl", 300)
    return CacheManager(**kwargs)


# ---------------------------------------------------------------------------
# Sentinel semantics
# ---------------------------------------------------------------------------

def test_placeholder_is_recognisable_and_falsy():
    assert is_placeholder(PLACEHOLDER)
    assert not is_placeholder((1, 3.0))
    assert not is_placeholder(None)
    assert not PLACEHOLDER


def test_preplace_does_not_fabricate_a_result():
    cache = _cache()
    cache.preplace("k")
    stored = cache._store["k"][1]
    assert is_placeholder(stored), f"preplace stored a real value: {stored!r}"


def test_lookup_of_a_reservation_is_a_miss():
    cache = _cache()
    cache.preplace("k")
    assert cache.lookup("k") is None
    assert cache.hits == 0
    assert cache.misses == 1


def test_reservation_still_occupies_capacity():
    cache = _cache(capacity=2)
    cache.preplace("a")
    cache.preplace("b")
    assert len(cache) == 2


def test_real_result_overwrites_a_reservation():
    cache = _cache()
    cache.preplace("k")
    cache.store("k", (1, 4.2))
    assert cache.lookup("k") == (1, 4.2)
    assert cache.hits == 1


def test_preplace_does_not_clobber_a_real_result():
    cache = _cache()
    cache.store("k", (1, 4.2))
    cache.preplace("k")
    assert cache.lookup("k") == (1, 4.2)


def test_preplacements_are_counted():
    cache = _cache()
    cache.preplace("a")
    cache.preplace("b")
    cache.preplace("a")  # already reserved, not counted again
    assert cache.preplacements == 2


# ---------------------------------------------------------------------------
# Distributed layer
# ---------------------------------------------------------------------------

def test_distributed_preplace_is_a_miss_then_a_hit():
    manager = DistributedCacheManager(rsu_ids=[1, 2], cache_capacity=8)
    key = make_task_key(3, 2, 256)

    manager.preplace(key, 1)
    assert manager.lookup(key, 1, enable_forwarding=False) is None
    assert manager.total_hits == 0

    manager.store(key, (1, 4.2), 1, replicate=False)
    assert manager.lookup(key, 1, enable_forwarding=False) == (1, 4.2)
    assert manager.total_hits == 1


def test_reservations_are_not_replicated_to_neighbours():
    manager = DistributedCacheManager(rsu_ids=[1, 2], cache_capacity=8)
    key = make_task_key(1, 3, 32)

    manager.preplace(key, 1)
    manager.replicate_hot()

    assert key not in manager.rsu_caches[2]._store


def test_total_preplacements_aggregates_across_rsus():
    manager = DistributedCacheManager(rsu_ids=[1, 2], cache_capacity=8)
    manager.preplace(make_task_key(0, 1, 64), 1)
    manager.preplace(make_task_key(1, 1, 32), 2)
    assert manager.total_preplacements == 2
