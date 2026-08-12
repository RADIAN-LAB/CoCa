"""Single authoritative taxonomy for VANET task types.

Every module that interprets ``task_type`` must read from this table. Before this
module existed the codebase carried three mutually inconsistent interpretations:

  * ``experiments/sumo/sumo_to_tasks.py`` — 0=Navigation, 1=Safety, 2=Media, ...,
    7=Emergency, 8=Infotainment, 9=V2X
  * ``sdn_core/deadline_calculator.py`` — 0-2 safety-critical, 3-5 traffic
    management, 6-9 infotainment
  * ``intent/classifier.py`` (intent-nlp-vanet) — ``task_type % 5``

Under those mappings Emergency (type 7) received an infotainment-grade deadline
and the slowest freshness decay of any class, while Media streaming (type 2) was
treated as safety-critical. The tables below replace all three.

Units
-----
All times are **milliseconds**. Names carry an explicit ``_ms`` suffix wherever a
duration is stored or returned, because the previous deadline table was
documented in seconds while being compared against millisecond completion times.

Deadline sources
----------------
Per-class latency budgets follow published V2X requirements rather than tuned
values:

  * safety        — 3GPP TR 22.885 pre-crash sensing / cooperative collision
    avoidance: 20 ms at the tightest, 100 ms for general safety messaging.
  * awareness     — ETSI EN 302 637-2 (CAM) cooperative awareness: 100 ms
    nominal, relaxed to 200 ms for low-priority perception sharing.
  * traffic       — ETSI EN 302 637-3 (DENM) / traffic management use cases:
    200-500 ms.
  * infotainment  — 3GPP TR 22.885 non-safety infotainment: 500-1000 ms.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Tuple

# ---------------------------------------------------------------------------
# Intent registry — the semantic classes used for freshness and reuse decisions
# ---------------------------------------------------------------------------

INTENT_LABELS: List[str] = [
    "traffic_analysis",
    "hazard_detection",
    "route_optimization",
    "sensor_processing",
    "environment_perception",
    "content_delivery",
    "parking_search",
]

NUM_INTENTS = len(INTENT_LABELS)

INTENT_INDEX: Dict[str, int] = {label: i for i, label in enumerate(INTENT_LABELS)}

# ---------------------------------------------------------------------------
# Deadline classes (milliseconds)
# ---------------------------------------------------------------------------
# Mapping is priority -> deadline_ms. Traces use priority 1 (low) to 3 (urgent);
# a higher priority buys a tighter latency budget within the same class.

DEADLINE_CLASSES: Dict[str, Dict[int, float]] = {
    "safety":       {3: 20.0,  2: 50.0,  1: 100.0},
    "awareness":    {3: 100.0, 2: 150.0, 1: 200.0},
    "traffic":      {3: 200.0, 2: 350.0, 1: 500.0},
    "infotainment": {3: 500.0, 2: 750.0, 1: 1000.0},
}


@dataclass(frozen=True)
class TaskTypeSpec:
    """Everything the simulator needs to know about one task type."""

    type_id: int
    name: str
    intent: str
    deadline_class: str
    compute_factor: float
    size_buckets_kb: Tuple[int, ...]
    priority_weights: Tuple[float, float, float]  # weights for priority 1, 2, 3

    @property
    def intent_idx(self) -> int:
        return INTENT_INDEX[self.intent]


# ---------------------------------------------------------------------------
# The 10 task types
# ---------------------------------------------------------------------------
# ``compute_factor`` multiplies the base edge computation time. Perception and
# sensor-fusion workloads are the most expensive; content delivery is largely a
# transfer cost rather than a compute cost.

TASK_TYPES: Tuple[TaskTypeSpec, ...] = (
    TaskTypeSpec(0, "Navigation",        "route_optimization",     "traffic",      1.0,
                 (64, 128, 192, 256, 384),      (0.2, 0.5, 0.3)),
    TaskTypeSpec(1, "SafetyAlert",       "hazard_detection",       "safety",       1.2,
                 (16, 32, 48, 64, 96),          (0.05, 0.15, 0.8)),
    TaskTypeSpec(2, "MediaStreaming",    "content_delivery",       "infotainment", 0.6,
                 (512, 768, 1024, 1280, 1536),  (0.6, 0.3, 0.1)),
    TaskTypeSpec(3, "SensorProcessing",  "sensor_processing",      "awareness",    1.5,
                 (128, 256, 384, 512, 768),     (0.3, 0.5, 0.2)),
    TaskTypeSpec(4, "CoopPerception",    "environment_perception", "awareness",    1.8,
                 (256, 384, 512, 768, 1024),    (0.1, 0.3, 0.6)),
    TaskTypeSpec(5, "TrafficInfo",       "traffic_analysis",       "traffic",      1.0,
                 (32, 64, 96, 128, 192),        (0.4, 0.4, 0.2)),
    TaskTypeSpec(6, "ParkingSearch",     "parking_search",         "infotainment", 0.8,
                 (32, 64, 96, 128, 192),        (0.5, 0.4, 0.1)),
    TaskTypeSpec(7, "Emergency",         "hazard_detection",       "safety",       1.2,
                 (16, 24, 32, 48, 64),          (0.0, 0.1, 0.9)),
    TaskTypeSpec(8, "Infotainment",      "content_delivery",       "infotainment", 0.6,
                 (512, 768, 1024, 1280, 1536),  (0.7, 0.2, 0.1)),
    TaskTypeSpec(9, "V2XMessage",        "environment_perception", "awareness",    0.9,
                 (64, 128, 192, 256, 384),      (0.2, 0.4, 0.4)),
)

NUM_TASK_TYPES = len(TASK_TYPES)

_BY_ID: Dict[int, TaskTypeSpec] = {spec.type_id: spec for spec in TASK_TYPES}


# ---------------------------------------------------------------------------
# Accessors
# ---------------------------------------------------------------------------

def spec_for(task_type: int) -> TaskTypeSpec:
    """Return the spec for a task type, falling back to type 0 if unknown."""
    return _BY_ID.get(int(task_type), _BY_ID[0])


def intent_of(task_type: int) -> str:
    """Intent label for a task type."""
    return spec_for(task_type).intent


def intent_idx_of(task_type: int) -> int:
    """Intent index for a task type."""
    return spec_for(task_type).intent_idx


def deadline_ms(task_type: int, priority: int) -> float:
    """Hard deadline in milliseconds for a task type at a given priority."""
    spec = spec_for(task_type)
    budgets = DEADLINE_CLASSES[spec.deadline_class]
    clamped = max(min(int(priority), max(budgets)), min(budgets))
    return budgets[clamped]


def compute_factor(task_type: int) -> float:
    """Multiplier on the base edge computation time."""
    return spec_for(task_type).compute_factor


def size_buckets_kb(task_type: int) -> Tuple[int, ...]:
    """Discrete payload sizes (kB) for a task type."""
    return spec_for(task_type).size_buckets_kb


def priority_weights(task_type: int) -> Tuple[float, float, float]:
    """Sampling weights over priority 1, 2, 3 for a task type."""
    return spec_for(task_type).priority_weights


def type_onehot(task_type: int) -> List[float]:
    """One-hot encoding over all task types (for FL/RL feature vectors)."""
    idx = int(task_type)
    return [1.0 if i == idx else 0.0 for i in range(NUM_TASK_TYPES)]


def intent_onehot(task_type: int) -> List[float]:
    """One-hot encoding over intent classes."""
    idx = intent_idx_of(task_type)
    return [1.0 if i == idx else 0.0 for i in range(NUM_INTENTS)]


__all__ = [
    "DEADLINE_CLASSES",
    "INTENT_INDEX",
    "INTENT_LABELS",
    "NUM_INTENTS",
    "NUM_TASK_TYPES",
    "TASK_TYPES",
    "TaskTypeSpec",
    "compute_factor",
    "deadline_ms",
    "intent_idx_of",
    "intent_of",
    "intent_onehot",
    "priority_weights",
    "size_buckets_kb",
    "spec_for",
    "type_onehot",
]
