"""Physical layout of the evaluation scenario.

RSU placement and coverage were previously defined inside
``experiments/sumo/sumo_to_tasks.py``, which made them invisible to anything
that needed to reason about *where* a result was produced — in particular the
trace-grounded invalidation oracle, which must map a vehicle position to the
same RSU cell the trace generator used.
"""
from __future__ import annotations

import math
from typing import Dict, Iterable, Tuple

# RSU positions on the 5x5 grid network (1200 m x 1200 m).
RSU_POSITIONS: Dict[int, Tuple[float, float]] = {
    1: (300.0, 300.0),    # SW intersection
    2: (900.0, 300.0),    # SE intersection
    3: (600.0, 600.0),    # centre intersection
    4: (300.0, 900.0),    # NW intersection
    5: (900.0, 900.0),    # NE intersection
}

RSU_IDS = sorted(RSU_POSITIONS)

# Coverage radius in metres. Wide enough that the five RSUs cover the grid.
RSU_RANGE_M = 500.0

# Grid extent, used for occupancy-grid signatures.
GRID_MIN_M = 0.0
GRID_MAX_M = 1200.0

# Occupancy grid resolution for environment_perception signatures: a cell edge
# of 100 m gives a 12x12 grid over the scenario.
OCCUPANCY_CELL_M = 100.0

# Radius defining a vehicle's local neighbourhood for sensor_processing.
NEIGHBOUR_RADIUS_M = 50.0

# Speed below which a vehicle counts as stopped (m/s). Used by hazard_detection
# and parking_search signatures.
STOPPED_SPEED_MS = 0.5


def distance(a: Tuple[float, float], b: Tuple[float, float]) -> float:
    """Euclidean distance in metres."""
    return math.hypot(a[0] - b[0], a[1] - b[1])


def nearest_rsu(x: float, y: float) -> int:
    """RSU id closest to a position.

    Must match the assignment used when generating the task trace, otherwise a
    cached result would be attributed to a different cell than the one it was
    actually produced in.
    """
    best_id, best_dist = RSU_IDS[0], float("inf")
    for rsu_id, position in RSU_POSITIONS.items():
        d = distance((x, y), position)
        if d < best_dist:
            best_id, best_dist = rsu_id, d
    return best_id


def in_range(x: float, y: float, rsu_id: int, radius_m: float = RSU_RANGE_M) -> bool:
    """True if a position falls inside an RSU's coverage radius."""
    return distance((x, y), RSU_POSITIONS[rsu_id]) <= radius_m


def occupancy_cell(x: float, y: float) -> Tuple[int, int]:
    """Discretise a position onto the coarse occupancy grid."""
    return (
        int((x - GRID_MIN_M) // OCCUPANCY_CELL_M),
        int((y - GRID_MIN_M) // OCCUPANCY_CELL_M),
    )


def vehicles_near(
    vehicles: Iterable[Dict[str, float]],
    position: Tuple[float, float],
    radius_m: float,
) -> list:
    """Vehicles within a radius of a position."""
    return [
        v for v in vehicles
        if distance((v["x"], v["y"]), position) <= radius_m
    ]


__all__ = [
    "GRID_MAX_M",
    "GRID_MIN_M",
    "NEIGHBOUR_RADIUS_M",
    "OCCUPANCY_CELL_M",
    "RSU_IDS",
    "RSU_POSITIONS",
    "RSU_RANGE_M",
    "STOPPED_SPEED_MS",
    "distance",
    "in_range",
    "nearest_rsu",
    "occupancy_cell",
    "vehicles_near",
]
