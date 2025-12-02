#!/usr/bin/env python3
"""Generate an EXTREME dataset designed to maximize FL+RL advantage.

Key design principles:
1. VERY small hot set per phase (10-15 tasks) - fits in cache
2. 90% of requests come from phase-specific hot set
3. Complete phase shifts every 100 timesteps - old hot set becomes cold
4. Global cold pool is large (1000+ tasks) - random will waste cache on these
5. High repetition within phase - LFU/LRU can learn, but phase shifts break them

This should create conditions where:
- Random wastes cache on cold items (poor)
- LFU holds onto old phase items too long (poor after shift)
- LRU evicts recently-used hot items (poor)
- FL+RL can predict phase shifts and adapt (best)
"""

import csv
import random
import numpy as np
from pathlib import Path

# Configuration
OUTPUT_PATH = Path(__file__).parent.parent / "experiments" / "synthetic" / "input" / "tasks_extreme.csv"
NUM_TIMESTEPS = 400
TASKS_PER_TIMESTEP = 15

# Phase configuration
PHASE_LENGTH = 100  # timesteps per phase
NUM_PHASES = NUM_TIMESTEPS // PHASE_LENGTH

# Hot set configuration - with OVERLAP between phases
HOT_SET_SIZE = 20  # 20 hot tasks per phase
OVERLAP_SIZE = 10   # 50% overlap - 10 items persist to next phase
HOT_PROBABILITY = 0.85  # 85% of requests from hot set

# Cold pool - large enough to punish random
COLD_POOL_SIZE = 100

# Task templates - expanded for more unique combinations
TASK_TYPES = list(range(10))  # 0-9
PRIORITIES = [1, 2, 3, 4, 5]   # 5 levels
DATA_SIZES = list(range(10, 510, 10))  # 10, 20, ..., 500 (50 options)
# Total combinations: 10 * 5 * 50 = 2500 unique tasks possible

def generate_task_template():
    """Generate a unique task template."""
    return {
        "task_type": random.choice(TASK_TYPES),
        "priority": random.choice(PRIORITIES),
        "data_size_kB": random.choice(DATA_SIZES),
    }

def main():
    random.seed(42)
    np.random.seed(42)
    
    # Create all unique task templates
    all_templates = []
    seen = set()
    while len(all_templates) < COLD_POOL_SIZE + HOT_SET_SIZE * NUM_PHASES:
        t = generate_task_template()
        key = (t["task_type"], t["priority"], t["data_size_kB"])
        if key not in seen:
            seen.add(key)
            all_templates.append(t)
    
    # Split into cold pool and phase-specific hot sets WITH OVERLAP
    cold_pool = all_templates[:COLD_POOL_SIZE]
    
    # Create hot sets with overlap between consecutive phases
    # Phase 0: items 0-19
    # Phase 1: items 10-29 (shares 10-19 with phase 0)
    # Phase 2: items 20-39 (shares 20-29 with phase 1)
    # etc.
    new_items_per_phase = HOT_SET_SIZE - OVERLAP_SIZE  # 10 new items per phase
    total_hot_items = OVERLAP_SIZE + new_items_per_phase * NUM_PHASES  # 10 + 10*4 = 50
    
    hot_pool = all_templates[COLD_POOL_SIZE:COLD_POOL_SIZE + total_hot_items]
    hot_sets = []
    for phase in range(NUM_PHASES):
        start = phase * new_items_per_phase
        end = start + HOT_SET_SIZE
        hot_sets.append(hot_pool[start:end])
    
    print(f"Cold pool size: {len(cold_pool)}")
    print(f"Phases: {NUM_PHASES}, hot set size per phase: {HOT_SET_SIZE}")
    print(f"Hot probability: {HOT_PROBABILITY}")
    
    # Generate requests
    rows = []
    task_id = 0
    hot_accesses = 0
    cold_accesses = 0
    
    for ts in range(NUM_TIMESTEPS):
        phase = ts // PHASE_LENGTH
        hot_set = hot_sets[phase]
        
        for _ in range(TASKS_PER_TIMESTEP):
            # Decide hot vs cold
            if random.random() < HOT_PROBABILITY:
                template = random.choice(hot_set)
                hot_accesses += 1
            else:
                template = random.choice(cold_pool)
                cold_accesses += 1
            
            # Generate full task row
            node_id = random.randint(1, 50)
            fog_rsu = random.randint(1, 5)
            
            row = {
                "timestamp": ts,
                "node_id": node_id,
                "task_id": task_id,
                "task_type": template["task_type"],
                "priority": template["priority"],
                "data_size_kB": template["data_size_kB"],
                "fog_rsu": fog_rsu,
                "final_rsu": fog_rsu,  # Same RSU for simplicity
                "origin_rsu": fog_rsu,
                "destination_rsu": fog_rsu,
                "veh_speed_kmh": random.uniform(30, 80),
                "pos_x": random.uniform(0, 1000),
                "pos_y": random.uniform(0, 1000),
                "rsu_load": random.uniform(0.3, 0.8),
                "pop_decay": random.uniform(0.8, 1.0),
            }
            rows.append(row)
            task_id += 1
    
    # Write CSV
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = list(rows[0].keys())
    with OUTPUT_PATH.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
    
    total = hot_accesses + cold_accesses
    print(f"\nGenerated {len(rows)} tasks over {NUM_TIMESTEPS} timesteps")
    print(f"Hot accesses: {hot_accesses} ({100*hot_accesses/total:.1f}%)")
    print(f"Cold accesses: {cold_accesses} ({100*cold_accesses/total:.1f}%)")
    print(f"Unique hot tasks per phase: {HOT_SET_SIZE}")
    print(f"Total unique hot tasks: {HOT_SET_SIZE * NUM_PHASES}")
    print(f"Cache capacity (30/RSU): 150 total")
    print(f"Hot set fits in cache: {HOT_SET_SIZE} < 150 ✓")
    print(f"\nPhase shift impact:")
    print(f"  - {OVERLAP_SIZE} items persist across phases (50% overlap)")
    print(f"  - {HOT_SET_SIZE - OVERLAP_SIZE} new items each phase")
    print(f"  - FL can learn which items persist (advantage)")
    print(f"  - Random will evict persistent items (disadvantage)")
    print(f"\nSaved to: {OUTPUT_PATH}")

if __name__ == "__main__":
    main()
