"""Random server selection baseline migrated from original project.

Refactor notes:
* Imports updated to new package paths.
* No functional logic changed.
"""
from typing import List, Tuple
import random
from pulp import lpSum, LpProblem, LpVariable, LpMaximize, LpBinary  # type: ignore

from sdn_core.routing import calculate_num_hob
from sdn_core.models.capacity import predict_capacity

# -------------------- Constants --------------------
M = range(1, 5)        # limited resource levels in this heuristic
Ri = range(1, 6)       # number of regions
alpha = 0.1

# Pre-allocated dict outside function to avoid recreating each call
R = {}

def _get_completion_time(execution_rsu: int,
                         fog_rsu: int,
                         delay_edge_rsu: float,
                         delay_rsu_rsu: float,
                         task_duration: float,
                         final_rsu: int) -> float:
    num_hob_trans = calculate_num_hob(fog_rsu, execution_rsu)
    num_hob_recv = calculate_num_hob(execution_rsu, final_rsu)
    return 2 * (1 + alpha) * delay_edge_rsu + (num_hob_trans + num_hob_recv * alpha) * delay_rsu_rsu + task_duration


def random_selection(
    T: List[Tuple[int, int, int]],
    region: int,
    delay_edge_rsu: float,
    delay_rsu_rsu: float,
    task_size: float = 4,
    deadline: float = 10,
):
    """Selects a random server for each task subject to deadline constraint."""
    prediction = predict_capacity()

    # Build capacity map for servers in *region*
    for k in range(1, prediction[region - 1] + 2):
        R[(region, k)] = 80e9 if k == 1 else 8e9

    c = {(i, j, r2): 1_000 * task_size * 1e6 for i, j, r2 in T}  # cycles required

    reserve = {}
    for i, j, r2 in T:
        attempts = 0
        while attempts < 200:
            k = random.randint(1, prediction[r2 - 1] + 1)
            delay = _get_completion_time(region, region, delay_edge_rsu, delay_rsu_rsu, c[(i, j, r2)] / R[(region, k)], region)
            if (r2, k) not in reserve and delay <= deadline:
                reserve[(r2, k)] = (i, j, r2)
                break
            attempts += 1

    total_delay = 0.0
    max_delay = 0.0
    for (r2, k), (i, j, _) in reserve.items():
        d = _get_completion_time(region, region, delay_edge_rsu, delay_rsu_rsu, c[(i, j, r2)] / R[(region, k)], region)
        total_delay += d
        max_delay = max(max_delay, d)

    return len(reserve), total_delay / len(reserve) if reserve else 0.0, max_delay
