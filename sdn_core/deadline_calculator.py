"""Per-task deadline lookup, in milliseconds.

All deadline values now come from :mod:`sdn_core.task_taxonomy`, which carries a
single authoritative task-type table and V2X-sourced latency budgets.

Unit correction
---------------
The previous implementation documented its return value as **seconds** (range
3-20) and derived it as ``base_deadline / priority`` from hand-picked bases of
15/25/40. That value was then compared directly against completion times
produced by :mod:`sdn_core.timing`, which are in **milliseconds**
(``COMPUTATION_BASE_TIME = 25.0`` ms). Deadlines were therefore effectively 1000x
tighter than documented, which made every cache hit succeed (~2 ms) and every
fresh computation fail (~10-25 ms). That artefact — not the caching policy — was
responsible for the extreme spread between the no-cache and cache-enabled
success rates.

Deadlines are milliseconds everywhere in this module. Prefer
:func:`calculate_deadline_ms`; :func:`calculate_dynamic_deadline` is retained as
an alias for existing call sites.
"""
from __future__ import annotations

from typing import Dict, Iterable, List

from sdn_core.task_taxonomy import DEADLINE_CLASSES, deadline_ms, spec_for


def calculate_deadline_ms(task_type: int, priority: int) -> float:
    """Hard deadline in milliseconds for a task type at a given priority.

    Args:
        task_type: Task type id (0-9); see ``sdn_core.task_taxonomy.TASK_TYPES``.
        priority: 1 (low) to 3 (urgent). Values outside the range are clamped.

    Returns:
        Deadline in milliseconds.
    """
    return deadline_ms(task_type, priority)


# Backwards-compatible alias. Note the unit change: this now returns
# milliseconds, matching the completion times it is compared against.
calculate_dynamic_deadline = calculate_deadline_ms


def deadline_class_of(task_type: int) -> str:
    """Latency class name ('safety', 'awareness', 'traffic', 'infotainment')."""
    return spec_for(task_type).deadline_class


def get_deadline_statistics(tasks_data: Iterable[Dict]) -> Dict[str, float]:
    """Summarise the deadline distribution over a set of tasks.

    Args:
        tasks_data: Iterable of dicts carrying ``task_type`` and ``priority``.

    Returns:
        Dict with min, max, mean and median deadline in milliseconds.
    """
    deadlines: List[float] = [
        calculate_deadline_ms(int(t["task_type"]), int(t["priority"]))
        for t in tasks_data
    ]
    if not deadlines:
        return {"min_ms": 0.0, "max_ms": 0.0, "mean_ms": 0.0, "median_ms": 0.0}
    ordered = sorted(deadlines)
    return {
        "min_ms": ordered[0],
        "max_ms": ordered[-1],
        "mean_ms": sum(ordered) / len(ordered),
        "median_ms": ordered[len(ordered) // 2],
    }


def deadline_table_ms() -> Dict[str, Dict[int, float]]:
    """The full class x priority deadline table, for inclusion in the paper."""
    return {cls: dict(budgets) for cls, budgets in DEADLINE_CLASSES.items()}


__all__ = [
    "calculate_deadline_ms",
    "calculate_dynamic_deadline",
    "deadline_class_of",
    "deadline_table_ms",
    "get_deadline_statistics",
]
