"""Invariants for the authoritative task taxonomy and the deadline model.

These lock in two corrections:

  * every consumer of ``task_type`` reads from one table, so the trace
    generator, the deadline model, the timing model, the FL feature builder and
    the intent classifier cannot drift apart again;
  * deadlines are milliseconds, in V2X-plausible ranges, rather than values
    documented in seconds and compared against millisecond completion times.
"""
from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from cache.fl_agent import FLAdvisor
from sdn_core.deadline_calculator import calculate_deadline_ms, deadline_class_of
from sdn_core.task_taxonomy import (
    DEADLINE_CLASSES,
    INTENT_LABELS,
    NUM_INTENTS,
    NUM_TASK_TYPES,
    TASK_TYPES,
    compute_factor,
    intent_of,
    priority_weights,
    size_buckets_kb,
    type_onehot,
)

PRIORITIES = (1, 2, 3)


# ---------------------------------------------------------------------------
# Taxonomy structure
# ---------------------------------------------------------------------------

def test_task_type_ids_are_contiguous():
    assert [spec.type_id for spec in TASK_TYPES] == list(range(NUM_TASK_TYPES))


def test_every_intent_label_is_registered():
    for spec in TASK_TYPES:
        assert spec.intent in INTENT_LABELS
        assert 0 <= spec.intent_idx < NUM_INTENTS


def test_every_deadline_class_is_defined():
    for spec in TASK_TYPES:
        assert spec.deadline_class in DEADLINE_CLASSES


def test_compute_factor_defined_for_all_types():
    """Regression: the old inline table only covered types 0-3."""
    for spec in TASK_TYPES:
        assert compute_factor(spec.type_id) == spec.compute_factor
        assert compute_factor(spec.type_id) > 0.0


def test_size_buckets_and_priority_weights_are_wellformed():
    for spec in TASK_TYPES:
        buckets = size_buckets_kb(spec.type_id)
        assert buckets and all(b > 0 for b in buckets)
        weights = priority_weights(spec.type_id)
        assert len(weights) == len(PRIORITIES)
        assert abs(sum(weights) - 1.0) < 1e-9, f"type {spec.type_id} weights {weights}"


# ---------------------------------------------------------------------------
# Semantic correctness of the mapping
# ---------------------------------------------------------------------------

def test_safety_critical_types_share_the_hazard_intent():
    """SafetyAlert and Emergency must both be hazard_detection.

    Under the previous ``task_type % 5`` mapping Emergency became
    route_optimization, which carried the slowest freshness decay of any intent.
    """
    assert intent_of(1) == "hazard_detection"
    assert intent_of(7) == "hazard_detection"


def test_emergency_is_not_treated_as_infotainment():
    """Emergency used to receive an infotainment-grade deadline."""
    assert deadline_class_of(7) == "safety"
    assert deadline_class_of(8) == "infotainment"
    assert calculate_deadline_ms(7, 3) < calculate_deadline_ms(8, 3)


def test_media_streaming_is_not_safety_critical():
    assert deadline_class_of(2) == "infotainment"
    assert intent_of(2) == "content_delivery"


# ---------------------------------------------------------------------------
# Deadline units and ordering
# ---------------------------------------------------------------------------

def test_deadlines_are_milliseconds_in_v2x_range():
    """Milliseconds, not seconds: 20 ms (pre-crash) to 1000 ms (infotainment)."""
    for spec in TASK_TYPES:
        for priority in PRIORITIES:
            ms = calculate_deadline_ms(spec.type_id, priority)
            assert 20.0 <= ms <= 1000.0, f"type {spec.type_id} p{priority} -> {ms}"


def test_higher_priority_gets_tighter_deadline():
    for spec in TASK_TYPES:
        budgets = [calculate_deadline_ms(spec.type_id, p) for p in PRIORITIES]
        assert budgets == sorted(budgets, reverse=True), f"type {spec.type_id}: {budgets}"


def test_deadline_classes_are_strictly_ordered():
    """safety < awareness < traffic < infotainment at equal priority."""
    for priority in PRIORITIES:
        ordered = [
            DEADLINE_CLASSES[cls][priority]
            for cls in ("safety", "awareness", "traffic", "infotainment")
        ]
        assert ordered == sorted(ordered)
        assert len(set(ordered)) == len(ordered)


def test_priority_is_clamped_not_crashing():
    assert calculate_deadline_ms(0, 0) == calculate_deadline_ms(0, 1)
    assert calculate_deadline_ms(0, 99) == calculate_deadline_ms(0, 3)


# ---------------------------------------------------------------------------
# Downstream consumers
# ---------------------------------------------------------------------------

def test_onehot_covers_every_task_type():
    """Regression: FL encoded only 4 of 10 types, zeroing out types 4-9."""
    for spec in TASK_TYPES:
        oh = type_onehot(spec.type_id)
        assert len(oh) == NUM_TASK_TYPES
        assert sum(oh) == 1.0
        assert oh[spec.type_id] == 1.0


def test_fl_feature_dim_matches_taxonomy():
    assert FLAdvisor._FEAT_DIM == FLAdvisor._SCALAR_FEATS + NUM_TASK_TYPES
    assert FLAdvisor._TYPE_COUNT == NUM_TASK_TYPES


def test_fl_model_accepts_a_taxonomy_sized_feature_vector():
    import torch

    advisor = FLAdvisor()
    features = [0.0] * FLAdvisor._SCALAR_FEATS + type_onehot(9)
    out = advisor.model(torch.tensor([features], dtype=torch.float32))
    assert out.shape == (1, 1)
