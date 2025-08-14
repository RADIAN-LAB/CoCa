"""Previous (heuristic) scheduling algorithm migrated from original project.

Notes:
* Imports updated to `sdn_core` paths.
* Logic unchanged.
"""
from typing import List, Tuple
from pulp import lpSum, LpProblem, LpVariable, LpMaximize, LpMinimize, LpBinary  # type: ignore

from sdn_core.routing import calculate_num_hob
from sdn_core.models.capacity import predict_capacity

M = range(1, 9)
alpha = 0.1
R = {}

def _get_completion_time(execution_rsu: int, fog_rsu: int, delay_edge_rsu: float, delay_rsu_rsu: float, task_duration: float, final_rsu: int) -> float:
    num_hob_trans = calculate_num_hob(fog_rsu, execution_rsu)
    num_hob_recv = calculate_num_hob(execution_rsu, final_rsu)
    return 2 * (1 + alpha) * delay_edge_rsu + (num_hob_trans + num_hob_recv * alpha) * delay_rsu_rsu + task_duration


def previous_task_scheduling(
    T: List[Tuple[int, int, int]],
    region: int,
    final_rsu: int,
    delay_edge_rsu: float,
    delay_rsu_rsu: float,
    task_size: float = 4,
    deadline: float = 10,
):
    prediction = predict_capacity()
    cap = prediction[region - 1]
    for k in range(1, cap + 2):
        R[(region, k)] = 80e9 if k == 1 else 8e9

    t_max_ij = {(i, j, r2): deadline for i, j, r2 in T}
    c = {(i, j, r2): 1_000 * task_size * 1e6 for i, j, r2 in T}
    r_m = {m: m * 1e9 for m in M}

    # Part 1: resource allocation
    prob = LpProblem("Optimal_Resource_Allocation", LpMaximize)
    x = LpVariable.dicts("x", [(i, j, r2, m) for (i, j, r2) in T for m in M], cat=LpBinary)
    prob += lpSum(r_m[m] * x[(i, j, r2, m)] for i, j, r2 in T for m in M)

    total_cap = sum(R[(region, k)] for k in range(1, cap + 2))
    prob += lpSum(r_m[m] * x[(i, j, r2, m)] for i, j, r2 in T for m in M) <= total_cap
    for i, j, r2 in T:
        prob += lpSum(x[(i, j, r2, m)] for m in M) == 1
    prob.solve()

    r_ij_opt = {(i, j, r2): 0 for i, j, r2 in T}
    for i, j, r2 in T:
        for m in M:
            if x[(i, j, r2, m)].value() == 1:
                r_ij_opt[(i, j, r2)] = r_m[m]
                break

    # Part 2: server selection
    prob2 = LpProblem("Server_Selection", LpMinimize)
    y = LpVariable.dicts("y", [(region, k, i, j, r2) for (i, j, r2) in T for k in range(1, cap + 2)], cat=LpBinary)
    t_tran_kj = {
        (region, k, i, j, r2): _get_completion_time(region, region, delay_edge_rsu, delay_rsu_rsu, c[(i, j, r2)] / r_ij_opt[(i, j, r2)] if r_ij_opt[(i, j, r2)] else 0, region)
        for k in range(1, cap + 2)
        for i, j, r2 in T
    }
    prob2 += lpSum(
        y[(region, k, i, j, r2)] * t_tran_kj[(region, k, i, j, r2)]
        for k in range(1, cap + 2) for i, j, r2 in T if r_ij_opt[(i, j, r2)]
    )
    for i, j, r2 in T:
        prob2 += lpSum(y[(region, k, i, j, r2)] for k in range(1, cap + 2)) == 1
        prob2 += (
            lpSum(y[(region, k, i, j, r2)] * t_tran_kj[(region, k, i, j, r2)] for k in range(1, cap + 2)) <= t_max_ij[(i, j, r2)]
        )
    prob2.solve()

    success = 0
    total_delay = 0.0
    for k in range(1, cap + 2):
        for i, j, r2 in T:
            if y[(region, k, i, j, r2)].value() == 1 and r_ij_opt[(i, j, r2)]:
                success += 1
                total_delay += t_tran_kj[(region, k, i, j, r2)]

    avg_delay = total_delay / success if success else 0.0
    return success, avg_delay
