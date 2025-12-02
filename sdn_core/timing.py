"""Timing models for deadline-aware cache decisions in VANET scheduling.

This module provides functions to calculate various timing components:
- Cache access time across RSUs
- Fresh computation time estimation
- Network delivery delays
- Deadline feasibility checks
"""
from typing import Tuple
import random

# Timing constants (in milliseconds) - matches scheduler parameters
CACHE_ACCESS_BASE_TIME = 4.0      # Base cache lookup time (faster cache path)
RSU_TO_RSU_DELAY = 0.3            # Inter-RSU communication delay (reduced)
VEHICLE_TO_RSU_DELAY = 1.0        # Vehicle to RSU access delay (matches delay_edge_rsu)
COMPUTATION_BASE_TIME = 10.0      # Base computation time per task (realistic for VANET edge)
NETWORK_JITTER_FACTOR = 0.05      # Lower variation to reduce random deadline misses
ALPHA = 0.1                       # Task-size reduction ratio (matches scheduler)

def calculate_cache_access_time(vehicle_node: int, cache_rsu: int, 
                               data_size_kb: int = 500, enable_forwarding: bool = True) -> float:
    """Calculate time to access cache from vehicle through RSU.
    
    Args:
        vehicle_node: ID of requesting vehicle
        cache_rsu: RSU where cache is located
        data_size_kb: Size of cached data in KB
        enable_forwarding: Whether inter-RSU forwarding is enabled
        
    Returns:
        Cache access time in milliseconds
    """
    # Base time: vehicle -> RSU -> cache lookup
    base_time = VEHICLE_TO_RSU_DELAY + CACHE_ACCESS_BASE_TIME
    
    # Data transfer time using scheduler's model: alpha * task_size * transmission_delay
    # Result size = alpha * input_size, transmission uses delay_edge_rsu
    result_size_factor = ALPHA * (data_size_kb / 1000.0)  # Convert KB to MB
    data_transfer_time = result_size_factor * VEHICLE_TO_RSU_DELAY
    base_time += data_transfer_time
    
    # Add jitter for realistic network conditions
    jitter = random.uniform(-NETWORK_JITTER_FACTOR, NETWORK_JITTER_FACTOR)
    access_time = base_time * (1 + jitter)
    
    # If forwarding enabled, add potential inter-RSU delay
    if enable_forwarding:
        # Probability of needing to forward to another RSU (reduced)
        forward_probability = 0.15
        if random.random() < forward_probability:
            access_time += RSU_TO_RSU_DELAY
    
    return max(access_time, 1.0)  # Minimum 1ms

def calculate_delivery_time(source_rsu: int, destination_rsu: int, data_size_kb: int = 500) -> float:
    """Calculate time to deliver cached result to destination.
    
    Args:
        source_rsu: RSU where result is cached
        destination_rsu: Target RSU for delivery
        data_size_kb: Size of data to deliver in KB
        
    Returns:
        Delivery time in milliseconds
    """
    if source_rsu == destination_rsu:
        # Local delivery with scheduler's transmission model
        result_size_factor = ALPHA * (data_size_kb / 1000.0)
        return CACHE_ACCESS_BASE_TIME + (result_size_factor * RSU_TO_RSU_DELAY)
    
    # Inter-RSU delivery with distance factor
    distance_factor = abs(source_rsu - destination_rsu)
    delivery_time = RSU_TO_RSU_DELAY * distance_factor
    
    # Add data transfer time using scheduler's model: alpha * task_size * delay_rsu_rsu
    result_size_factor = ALPHA * (data_size_kb / 1000.0)
    data_transfer_time = result_size_factor * RSU_TO_RSU_DELAY * distance_factor
    delivery_time += data_transfer_time
    
    # Add network jitter
    jitter = random.uniform(-NETWORK_JITTER_FACTOR, NETWORK_JITTER_FACTOR)
    return delivery_time * (1 + jitter)

def estimate_computation_time(task: Tuple[int, int, int, int], 
                            task_type: int = 0, priority: int = 1, 
                            data_size_kb: int = 500) -> float:
    """Estimate fresh computation time for a task.
    
    Args:
        task: Task tuple (node_id, task_id, fog_rsu, final_rsu)
        task_type: Task type affecting computation complexity
        priority: Task priority (higher = more resources)
        data_size_kb: Task data size in KB
        
    Returns:
        Estimated computation time in milliseconds
    """
    node_id, task_id, fog_rsu, final_rsu = task
    
    # Base computation time varies by task type
    type_multipliers = {0: 1.0, 1: 1.5, 2: 2.0, 3: 0.8}
    type_factor = type_multipliers.get(task_type, 1.0)
    
    # Priority affects resource allocation (higher priority = faster)
    priority_factor = 1.0 / (priority + 1)
    
    # Data size affects processing time
    size_factor = 1.0 + (data_size_kb / 1000.0) * 0.5
    
    # RSU load factor (simplified)
    load_factor = 1.0 + random.uniform(0.0, 0.5)
    
    computation_time = (COMPUTATION_BASE_TIME * type_factor * 
                       priority_factor * size_factor * load_factor)
    
    # Add processing jitter
    jitter = random.uniform(-NETWORK_JITTER_FACTOR, NETWORK_JITTER_FACTOR)
    return computation_time * (1 + jitter)

def should_use_cache(task: Tuple[int, int, int, int], cached_result: any,
                    deadline: float, task_attributes: dict = None) -> Tuple[bool, dict]:
    """Determine if cache should be used based on deadline and timing constraints.
    
    Args:
        task: Task tuple (node_id, task_id, fog_rsu, final_rsu)
        cached_result: Available cached result (None if no cache)
        deadline: Hard deadline in milliseconds
        task_attributes: Optional task attributes (type, priority, size)
        
    Returns:
        Tuple of (should_use_cache, timing_info)
    """
    if cached_result is None:
        return False, {"reason": "no_cache", "cache_time": 0, "compute_time": 0}
    
    node_id, task_id, fog_rsu, final_rsu = task
    
    # Extract task attributes
    if task_attributes:
        task_type = task_attributes.get("task_type", 0)
        priority = task_attributes.get("priority", 1)
        data_size = task_attributes.get("data_size_kB", 500)
    else:
        task_type, priority, data_size = 0, 1, 500
    
    # Calculate cache retrieval time (include data size)
    cache_access_time = calculate_cache_access_time(node_id, fog_rsu, data_size)
    cache_delivery_time = calculate_delivery_time(fog_rsu, final_rsu, data_size)
    total_cache_time = cache_access_time + cache_delivery_time
    
    # Calculate fresh computation time
    fresh_computation_time = estimate_computation_time(task, task_type, priority, data_size)
    fresh_delivery_time = calculate_delivery_time(fog_rsu, final_rsu)
    total_fresh_time = fresh_computation_time + fresh_delivery_time
    
    # Timing analysis
    timing_info = {
        "cache_time": total_cache_time,
        "compute_time": total_fresh_time,
        "deadline": deadline,
        "cache_meets_deadline": total_cache_time <= deadline,
        "compute_meets_deadline": total_fresh_time <= deadline,
        "cache_is_faster": total_cache_time < total_fresh_time,
    }
    
    # Decision logic
    cache_meets_deadline = total_cache_time <= deadline
    compute_meets_deadline = total_fresh_time <= deadline
    cache_is_faster = total_cache_time < total_fresh_time
    
    # Use cache if it meets deadline and is beneficial
    if cache_meets_deadline and cache_is_faster:
        timing_info["reason"] = "cache_optimal"
        return True, timing_info
    elif cache_meets_deadline and not compute_meets_deadline:
        timing_info["reason"] = "cache_only_feasible"
        return True, timing_info
    elif not cache_meets_deadline and compute_meets_deadline:
        timing_info["reason"] = "cache_too_slow"
        return False, timing_info
    elif not cache_meets_deadline and not compute_meets_deadline:
        # Neither meets deadline - choose faster option
        timing_info["reason"] = "both_miss_deadline_choose_faster"
        return cache_is_faster, timing_info
    else:
        # Both meet deadline but computation is faster
        timing_info["reason"] = "compute_faster"
        return False, timing_info

def get_timing_statistics(decisions: list) -> dict:
    """Analyze timing decisions for performance insights.
    
    Args:
        decisions: List of (task, decision, timing_info) tuples
        
    Returns:
        Dictionary with timing statistics
    """
    if not decisions:
        return {}
    
    cache_used = sum(1 for _, decision, _ in decisions if decision)
    total_decisions = len(decisions)
    
    cache_times = [info["cache_time"] for _, _, info in decisions]
    compute_times = [info["compute_time"] for _, _, info in decisions]
    
    reasons = [info["reason"] for _, _, info in decisions]
    reason_counts = {reason: reasons.count(reason) for reason in set(reasons)}
    
    return {
        "total_decisions": total_decisions,
        "cache_usage_rate": cache_used / total_decisions,
        "avg_cache_time": sum(cache_times) / len(cache_times),
        "avg_compute_time": sum(compute_times) / len(compute_times),
        "decision_reasons": reason_counts,
        "deadline_miss_rate": sum(1 for _, _, info in decisions 
                                 if not info.get("cache_meets_deadline", True) and 
                                    not info.get("compute_meets_deadline", True)) / total_decisions
    }

def calculate_cache_completion_time(task: Tuple[int, int, int, int], 
                                   delay_edge_rsu: float = 1.0, 
                                   delay_rsu_rsu: float = 0.5, 
                                   delay_car_car: float = 0.1) -> float:
    """Calculate cache completion time using scheduler's completion time model.
    
    This function uses the same timing model as the scheduler's _get_completion_time
    to ensure consistency between cache decisions and actual scheduling.
    
    Args:
        task: Task tuple (node_id, task_id, fog_rsu, final_rsu)
        delay_edge_rsu: Vehicle to RSU delay (ms)
        delay_rsu_rsu: RSU to RSU delay (ms)
        delay_car_car: Vehicle to vehicle delay (ms)
        
    Returns:
        Cache completion time in milliseconds
    """
    node_id, task_id, fog_rsu, final_rsu = task
    
    # Use scheduler's completion time model for cache retrieval
    # Assumes cache retrieval is faster than computation (base 5ms vs 50ms+)
    cache_retrieval_duration = 5.0  # Base cache lookup time
    
    # Apply scheduler's completion time formula for cache delivery
    # This ensures consistency with scheduler's timing calculations
    
    # Random factors for realism (matching scheduler model)
    import random
    beta = 0.1  # ratio of cars not connected to RSU
    number_of_hob = [1, 2, 3]
    alpha = 0.1  # task size reduction ratio
    
    not_connected_to_rsu = random.random() < beta
    number_of_hob_to_rsu = random.choice(number_of_hob)
    
    # Calculate hops (simplified - assume fog_rsu is execution RSU for cache)
    num_hob_trans = abs(fog_rsu - fog_rsu)  # 0 hops for local cache
    num_hob_recv = abs(fog_rsu - final_rsu)  # hops to deliver result
    
    # Scheduler's completion time model adapted for cache
    cache_completion_time = (
        2 * (1 + alpha) * delay_edge_rsu +  # Vehicle communication
        (num_hob_trans + num_hob_recv * alpha) * delay_rsu_rsu +  # RSU hops
        cache_retrieval_duration +  # Cache lookup time
        (2 * (1 + alpha) * delay_car_car * number_of_hob_to_rsu if not_connected_to_rsu else 0)  # V2V delays
    )
    
    return max(cache_completion_time, 1.0)  # Minimum 1ms

__all__ = [
    "calculate_cache_access_time",
    "calculate_delivery_time", 
    "estimate_computation_time",
    "calculate_cache_completion_time",
    "should_use_cache",
    "get_timing_statistics"
]
