"""Pre-placement is modelled as speculative computation with a real cost.

Reserving capacity without producing a result cannot help — the reservation is
unservable and evicts real entries. Pre-placement therefore runs the predicted
task early, pays for it whether or not the prediction was right, and caches a
genuine result. These tests pin that contract and the misprediction accounting
a reviewer will ask for.
"""
from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from cache.distributed_manager import DistributedCacheManager
from cache.manager import is_placeholder, make_task_key
from sdn_core.timing import estimate_proactive_computation_ms

ATTRS = {"task_type": 3, "priority": 2, "data_size_kB": 256}


def _manager(**kwargs) -> DistributedCacheManager:
    kwargs.setdefault("rsu_ids", [1, 2])
    kwargs.setdefault("cache_capacity", 16)
    return DistributedCacheManager(**kwargs)


# ---------------------------------------------------------------------------
# Cost model
# ---------------------------------------------------------------------------

def test_proactive_computation_costs_time():
    cost = estimate_proactive_computation_ms(task_type=3, priority=2,
                                             data_size_kb=256, rsu_id=1)
    assert cost > 0.0


def test_heavier_task_types_cost_more():
    """CoopPerception (factor 1.8) must outcost MediaStreaming (factor 0.6)."""
    samples = 40
    heavy = sum(
        estimate_proactive_computation_ms(task_type=4, priority=2, data_size_kb=512)
        for _ in range(samples)
    )
    light = sum(
        estimate_proactive_computation_ms(task_type=2, priority=2, data_size_kb=512)
        for _ in range(samples)
    )
    assert heavy > light


# ---------------------------------------------------------------------------
# Placement produces a real, servable result
# ---------------------------------------------------------------------------

def test_precompute_stores_a_real_result_not_a_placeholder():
    manager = _manager()
    key = make_task_key(3, 2, 256)

    cost = manager.precompute(key, 1, ATTRS)

    assert cost is not None and cost > 0.0
    stored = manager.rsu_caches[1]._store[key][1]
    assert not is_placeholder(stored)
    assert manager.lookup(key, 1, enable_forwarding=False) is not None


def test_precompute_is_charged_once_and_recorded():
    manager = _manager()
    key = make_task_key(3, 2, 256)

    manager.precompute(key, 1, ATTRS)

    assert manager.proactive_computations == 1
    assert manager.proactive_compute_ms > 0.0


def test_precompute_skips_keys_that_already_hold_a_real_result():
    """Recomputing a cached result would be pure waste and must not be charged."""
    manager = _manager()
    key = make_task_key(3, 2, 256)
    manager.store(key, (1, 4.2), 1, replicate=False)

    assert manager.precompute(key, 1, ATTRS) is None
    assert manager.proactive_computations == 0
    assert manager.lookup(key, 1, enable_forwarding=False) == (1, 4.2)


def test_precompute_replaces_a_bare_reservation():
    manager = _manager()
    key = make_task_key(3, 2, 256)
    manager.preplace(key, 1)

    assert manager.precompute(key, 1, ATTRS) is not None
    assert not is_placeholder(manager.rsu_caches[1]._store[key][1])


# ---------------------------------------------------------------------------
# Misprediction accounting
# ---------------------------------------------------------------------------

def test_useful_prediction_counts_as_a_hit_once():
    manager = _manager()
    key = make_task_key(3, 2, 256)
    manager.precompute(key, 1, ATTRS)

    manager.lookup(key, 1, enable_forwarding=False)
    manager.lookup(key, 1, enable_forwarding=False)

    # Repeat accesses must not inflate precision: the prediction was useful once.
    assert manager.proactive_hits == 1
    assert manager.proactive_wasted == 0
    assert manager.proactive_stats()["proactive_precision"] == 1.0


def test_unused_prediction_counts_as_waste():
    manager = _manager()
    manager.precompute(make_task_key(3, 2, 256), 1, ATTRS)
    manager.precompute(make_task_key(4, 1, 512), 1, {"task_type": 4, "priority": 1,
                                                     "data_size_kB": 512})

    manager.lookup(make_task_key(3, 2, 256), 1, enable_forwarding=False)

    assert manager.proactive_computations == 2
    assert manager.proactive_hits == 1
    assert manager.proactive_wasted == 1


def test_proactive_stats_block_is_complete():
    manager = _manager()
    manager.precompute(make_task_key(3, 2, 256), 1, ATTRS)
    stats = manager.proactive_stats()

    assert set(stats) == {
        "proactive_computations",
        "proactive_hits",
        "proactive_wasted",
        "proactive_precision",
        "proactive_compute_ms",
    }
    assert stats["proactive_precision"] == 0.0  # nothing served yet


def test_precision_is_zero_when_nothing_was_placed():
    manager = _manager()
    assert manager.proactive_stats()["proactive_precision"] == 0.0
    assert manager.proactive_wasted == 0
