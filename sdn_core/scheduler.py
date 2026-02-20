"""Core task-scheduling logic previously in SDN/models/scheduling.py.

Refactored:
* Updated imports to the new package layout (`sdn_core.routing`, `sdn_core.models.capacity`).
* Encapsulated constants inside the module for clarity.
* Fixed a bug: `random.rand()` ➜ `random.random()`.
* Added type hints and docstrings for easier maintenance.
"""
from typing import List, Tuple, Dict
import random
from pulp import LpProblem, LpVariable, lpSum, LpMaximize, LpMinimize, LpBinary  # type: ignore

from sdn_core.routing import calculate_num_hob
from sdn_core.models.capacity import predict_capacity
from sdn_core.timing import should_use_cache, calculate_cache_completion_time, estimate_computation_time
from sdn_core.trajectory import predict_vehicle_destination_rsu
from sdn_core.deadline_calculator import calculate_dynamic_deadline
import random
from cache import distributed_manager as dm_module  # Import module to get updated singleton
from cache.manager import make_task_key

# -----------------------------
# Constants & Parameters
# -----------------------------
M = range(1, 9)                    # Resource levels (GHz)
Ri = range(1, 6)                   # Regions
alpha: float = 0.1                 # Task-size reduction ratio
beta: float = 0.1                  # Ratio of cars not connected to any RSU
number_of_hob = [1, 2, 3]  # possible hop counts for vehicle-to-RSU

# -----------------------------
# Helper Functions
# -----------------------------

def _get_completion_time_mobility_aware(execution_rsu: int,
                                       fog_rsu: int,
                                       delay_edge_rsu: float,
                                       delay_rsu_rsu: float,
                                       delay_car_car: float,
                                       task_duration: float,
                                       final_rsu: int) -> float:
    """Mobility-aware completion time calculation from original SDN scheduler.
    
    Considers vehicle connectivity and dynamic hop counts for realistic VANET modeling.
    """
    # Vehicle connectivity model - some vehicles not connected to RSU
    not_connected_to_rsu = random.random() < beta
    number_of_hob_to_rsu = random.choice(number_of_hob)
    
    # Calculate hops between RSUs
    num_hob_trans = calculate_num_hob(fog_rsu, execution_rsu)
    num_hob_recv = calculate_num_hob(execution_rsu, final_rsu)
    
    # Mobility-aware completion time with V2V delays when not connected
    return (
        2 * (1 + alpha) * delay_edge_rsu
        + (num_hob_trans + num_hob_recv * alpha) * delay_rsu_rsu
        + task_duration
        + (2 * (1 + alpha) * delay_car_car * number_of_hob_to_rsu if not_connected_to_rsu else 0)
    )

def _get_completion_time(execution_rsu: int,
                         fog_rsu: int,
                         delay_edge_rsu: float,
                         delay_rsu_rsu: float,
                         delay_car_car: float,
                         task_duration: float,
                         final_rsu: int) -> float:
    """Compute completion time of a task following the original analytical model."""
    return _get_completion_time_mobility_aware(
        execution_rsu, fog_rsu, delay_edge_rsu, delay_rsu_rsu, 
        delay_car_car, task_duration, final_rsu
    )

# -----------------------------
# Main Scheduling Entry Point
# -----------------------------

def task_scheduling(
    T: List[Tuple[int, int, int, int]],
    delay_edge_rsu: float,
    delay_rsu_rsu: float,
    delay_car_car: float,
    task_size: float = 4,
    deadline: float = 10,
    enable_trajectory_prediction: bool = False,
    vehicle_attributes: dict = None,
) -> Tuple[int, float]:
    """Optimise resource allocation & server selection for tasks with intelligent caching.

    Args:
        T: List of tuples (node_id, task_id, fog_rsu, final_rsu).
        delay_edge_rsu: Delay from edge to RSU.
        delay_rsu_rsu: RSU-to-RSU delay per hop.
        delay_car_car: V2V delay.
        task_size: Size (MB) of each task (simplified uniform size).
        deadline: Hard deadline (ms) for each task.
        enable_trajectory_prediction: Whether to use ML-based trajectory prediction.
        vehicle_attributes: Dict with vehicle mobility data (position, speed, time).

    Returns:
        A tuple (success_count, average_completion_time_ms).
    """

    # Per-task results and timing decisions
    task_results = {}
    remaining_tasks = []
    timing_decisions = []
    
    # Optionally update tasks with predicted destination RSU for proactive caching
    trajectory_updated_tasks = []
    for node_id, task_id, fog_rsu, final_rsu in T:
        if enable_trajectory_prediction and vehicle_attributes and node_id in vehicle_attributes:
            va = vehicle_attributes[node_id]
            predicted_rsu = predict_vehicle_destination_rsu(
                va['x'], va['y'], fog_rsu,
                va['time'], va['speed'], va['time'] + 5  # rough 5-sec horizon
            )
            trajectory_updated_tasks.append((node_id, task_id, fog_rsu, predicted_rsu))
        else:
            trajectory_updated_tasks.append((node_id, task_id, fog_rsu, final_rsu))
    
    # Generate cache keys AFTER trajectory prediction updates
    for task in trajectory_updated_tasks:
        node_id, task_id, fog_rsu, final_rsu = task  # Use trajectory-updated task
        
        # Create enhanced cache key with task attributes for better categorization
        # Include task type and priority for finer-grained cache reuse
        # Extract task attributes from synthetic trace if available
        task_type = 0  # Default
        
        if vehicle_attributes and node_id in vehicle_attributes:
            task_attrs = vehicle_attributes[node_id]
            task_type = task_attrs.get('task_type', 0)
        
        # Unified cache key: task_type|priority|data_size_kB
        priority = task_attrs.get('priority', 0) if vehicle_attributes and node_id in vehicle_attributes else 0
        data_size = task_attrs.get('data_size', 0) if vehicle_attributes and node_id in vehicle_attributes else 0
        task_key = make_task_key(task_type, priority, data_size)
        
        # Calculate dynamic deadline based on task type and priority
        # If priority is 0 (no attributes), use default deadline
        task_deadline = calculate_dynamic_deadline(task_type, priority) if priority > 0 else deadline
        
        # Check distributed cache with trajectory-aware lookup (skip if cache disabled)
        if dm_module.distributed_cache_manager.ENABLE_CACHE_LOOKUP:
            cached = dm_module.distributed_cache_manager.lookup(task_key, fog_rsu)
        else:
            cached = None
        
        # Skip trajectory-aware cache lookup since we disabled trajectory prediction
        
        # Make deadline-aware decision with dynamic deadline
        use_cache, timing_info = should_use_cache(task, cached, task_deadline)
        timing_decisions.append((task, use_cache, timing_info))
        
        if use_cache and cached is not None:
            # Use cached result with actual timing (fast cache path)
            completion_time = timing_info["cache_time"]
            success = 1 if completion_time <= task_deadline else 0
            task_results[task] = (success, completion_time)
            # Store result in cache for future use (only if auto-caching is enabled)
            if dm_module.distributed_cache_manager.ENABLE_AUTO_CACHE:
                dm_module.distributed_cache_manager.store(task_key, (success, completion_time), fog_rsu, admission_threshold=1)
                # Proactively replicate to predicted destination RSU if different
                if final_rsu != fog_rsu:
                    dm_module.distributed_cache_manager.store(task_key, (success, completion_time), final_rsu, admission_threshold=1, replicate=False)
        else:
            # Need fresh computation
            remaining_tasks.append(task)
    
    # If all tasks were cached, return cached results with their actual completion times
    if not remaining_tasks:
        total_success = sum(success for success, _ in task_results.values())
        total_completion = sum(comp * success for success, comp in task_results.values() if success)
        avg_completion = total_completion / total_success if total_success else 0.0
        return total_success, avg_completion
        
    # Only process non-cached tasks
    T = remaining_tasks

    prediction: List[int] = predict_capacity()

    # Build server capacity map R[(region, server_id)]
    R: Dict[Tuple[int, int], float] = {}
    total_cap = 0.0
    for r in Ri:
        for k in range(1, prediction[r - 1] + 2):
            # Physical server has larger capacity than virtual servers
            R[(r, k)] = 80e9 if k == 1 else 8e9
            total_cap += R[(r, k)]

    # Pre-compute dictionaries used in LP formulation
    t_max_ij = {(i, j, r2): deadline for i, j, r2, _ in T}
    c = {(i, j, r2): 1000 * task_size for i, j, r2, _ in T}  # processing cycles required
    r_m = {m: m * 1e9 for m in M}                             # GHz levels as cycles/s

    # ---------------- Part 1: Resource Allocation ----------------
    prob = LpProblem("Optimal_Resource_Allocation", LpMaximize)

    x = LpVariable.dicts("x", [(i, j, r2, m) for (i, j, r2, _) in T for m in M], cat=LpBinary)

    # Objective: maximise allocated resources (equivalent to minimising duration)
    prob += lpSum(r_m[m] * x[(i, j, r2, m)] for i, j, r2, _ in T for m in M)

    # Total capacity constraint
    prob += lpSum(r_m[m] * x[(i, j, r2, m)] for i, j, r2, _ in T for m in M) <= total_cap

    # Each task gets exactly one resource level
    for i, j, r2, _ in T:
        prob += lpSum(x[(i, j, r2, m)] for m in M) == 1

    prob.solve()

    # Extract chosen resource for each task
    r_ij_opt: Dict[Tuple[int, int, int], float] = {(i, j, r2): 0 for i, j, r2, _ in T}
    for i, j, r2, _ in T:
        for m in M:
            if x[(i, j, r2, m)].value() == 1:
                r_ij_opt[(i, j, r2)] = r_m[m]
                break

    # ---------------- Part 2: Server Selection ----------------
    prob2 = LpProblem("Server_Selection", LpMinimize)

    y = LpVariable.dicts(
        "y",
        [
            (r, k, i, j, r2)
            for (i, j, r2, _) in T
            for r in Ri
            for k in range(1, prediction[r - 1] + 2)
        ],
        cat=LpBinary,
    )

    # Pre-compute completion times
    t_tran_kj: Dict[Tuple[int, int, int, int, int], float] = {}
    for r in Ri:
        for k in range(1, prediction[r - 1] + 2):
            for i, j, r2, final_rsu in T:
                duration = c[(i, j, r2)] / r_ij_opt[(i, j, r2)] if r_ij_opt[(i, j, r2)] else 0
                t_tran_kj[(r, k, i, j, r2)] = _get_completion_time(
                    execution_rsu=r2,
                    fog_rsu=r,
                    delay_edge_rsu=delay_edge_rsu,
                    delay_rsu_rsu=delay_rsu_rsu,
                    delay_car_car=delay_car_car,
                    task_duration=duration,
                    final_rsu=final_rsu,
                )

    # Objective: minimise total completion time
    prob2 += lpSum(
        y[(r, k, i, j, r2)] * t_tran_kj[(r, k, i, j, r2)]
        for (r, k, i, j, r2) in y
        if r_ij_opt[(i, j, r2)]
    )

    # Each task assigned to exactly one server
    for i, j, r2, _ in T:
        prob2 += lpSum(y[(r, k, i, j, r2)] for r in Ri for k in range(1, prediction[r - 1] + 2)) == 1

    # Deadline constraints
    for i, j, r2, _ in T:
        prob2 += (
            lpSum(y[(r, k, i, j, r2)] * t_tran_kj[(r, k, i, j, r2)] for r in Ri for k in range(1, prediction[r - 1] + 2))
            <= t_max_ij[(i, j, r2)]
        )

    prob2.solve()

    # Compute results
    success_count = 0
    total_completion = 0.0
    for r in Ri:
        for k in range(1, prediction[r - 1] + 2):
            for i, j, r2, _ in T:
                if y[(r, k, i, j, r2)].value() == 1 and r_ij_opt[(i, j, r2)]:
                    success_count += 1
                    total_completion += t_tran_kj[(r, k, i, j, r2)]

    # Calculate average LP allocation time for newly scheduled tasks
    avg_lp_completion = total_completion / success_count if success_count else 0.0
    
    # Store individual task results in distributed cache with realistic computation overhead
    computed_success = 0
    computed_completion = 0.0
    for task in remaining_tasks:
        node_id, task_id, fog_rsu, final_rsu = task
        
        # Unified cache key: task_type|priority|data_size_kB (matches lookup)
        task_type = 0  # Default
        
        if vehicle_attributes and node_id in vehicle_attributes:
            task_attrs = vehicle_attributes[node_id]
            task_type = task_attrs.get('task_type', 0)
        
        priority = task_attrs.get('priority', 0) if vehicle_attributes and node_id in vehicle_attributes else 0
        data_size = task_attrs.get('data_size', 0) if vehicle_attributes and node_id in vehicle_attributes else 0
        task_key = make_task_key(task_type, priority, data_size)
        
        # Calculate dynamic deadline for this task
        task_deadline = calculate_dynamic_deadline(task_type, priority) if priority > 0 else deadline
        
        # Add realistic computation overhead from timing model
        # Uncached tasks incur: LP allocation time + edge computation time
        compute_overhead = estimate_computation_time(task, task_type, priority, data_size if data_size else 500)
        task_completion = avg_lp_completion + compute_overhead
        
        # Determine success based on dynamic deadline
        task_success = 1 if task_completion <= task_deadline else 0
        computed_success += task_success
        computed_completion += task_completion * task_success
        
        # Store result in the RSU that processed the task (only if auto-caching is enabled)
        if dm_module.distributed_cache_manager.ENABLE_AUTO_CACHE:
            result = (task_success, task_completion)
            dm_module.distributed_cache_manager.store(task_key, result, fog_rsu)
    
    # Combine cached and fresh computation results for final average
    cached_success = sum(success for success, _ in task_results.values())
    cached_completion = sum(comp * success for success, comp in task_results.values() if success)
    
    total_success = computed_success + cached_success
    total_completion_time = computed_completion + cached_completion
    final_avg = total_completion_time / total_success if total_success else 0.0
    
    return total_success, final_avg

__all__ = ["task_scheduling"]
