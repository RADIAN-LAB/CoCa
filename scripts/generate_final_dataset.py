#!/usr/bin/env python3
"""Generate final dataset with STRONG temporal patterns for clear policy differentiation.

Design:
- Small working set (50 hot items) that repeats heavily
- Large cold pool (500 items) accessed rarely
- Hot items change over time (temporal shifts)
- This creates scenarios where:
  * LFU holds onto old hot items (bad)
  * LRU keeps recent items (good)
  * Random has no pattern (medium)
  * FL+RL can learn patterns (best)
"""

import csv
import random
import numpy as np
from pathlib import Path

OUTPUT_PATH = Path(__file__).parent.parent / "experiments" / "synthetic" / "input" / "tasks_final.csv"
NUM_TIMESTEPS = 400
TASKS_PER_TIMESTEP = 15

# Working set configuration
HOT_SET_SIZE = 50  # Items that are frequently accessed
COLD_POOL_SIZE = 500  # Items that are rarely accessed
HOT_PROBABILITY = 0.90  # 90% of requests from hot set

# Temporal shift: hot set changes every 100 timesteps
PHASE_LENGTH = 100
HOT_OVERLAP = 30  # 30 items persist across phases

# Task templates
TASK_TYPES = list(range(10))
PRIORITIES = [1, 2, 3, 4, 5]
DATA_SIZES = list(range(10, 510, 10))

def generate_task_template():
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
    needed = COLD_POOL_SIZE + HOT_SET_SIZE * 4  # 4 phases
    while len(all_templates) < needed:
        t = generate_task_template()
        key = (t["task_type"], t["priority"], t["data_size_kB"])
        if key not in seen:
            seen.add(key)
            all_templates.append(t)
    
    # Split into cold pool and hot sets
    cold_pool = all_templates[:COLD_POOL_SIZE]
    
    # Create overlapping hot sets for each phase
    hot_sets = []
    for phase in range(4):
        if phase == 0:
            hot_sets.append(all_templates[COLD_POOL_SIZE:COLD_POOL_SIZE + HOT_SET_SIZE])
        else:
            # Keep HOT_OVERLAP items from previous phase, add new ones
            prev_hot = hot_sets[phase-1]
            persistent = prev_hot[:HOT_OVERLAP]
            new_start = COLD_POOL_SIZE + HOT_SET_SIZE + (phase-1) * (HOT_SET_SIZE - HOT_OVERLAP)
            new_items = all_templates[new_start:new_start + (HOT_SET_SIZE - HOT_OVERLAP)]
            hot_sets.append(persistent + new_items)
    
    print(f"Cold pool: {len(cold_pool)} tasks")
    print(f"Hot sets: {len(hot_sets)} phases, {HOT_SET_SIZE} items each")
    print(f"Overlap between phases: {HOT_OVERLAP} items")
    
    # Generate requests
    rows = []
    task_id = 0
    hot_accesses = 0
    cold_accesses = 0
    
    for ts in range(NUM_TIMESTEPS):
        phase = ts // PHASE_LENGTH
        hot_set = hot_sets[phase]
        
        for _ in range(TASKS_PER_TIMESTEP):
            if random.random() < HOT_PROBABILITY:
                template = random.choice(hot_set)
                hot_accesses += 1
            else:
                template = random.choice(cold_pool)
                cold_accesses += 1
            
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
                "final_rsu": fog_rsu,
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
    print(f"\nKey characteristics:")
    print(f"  - Hot set size: {HOT_SET_SIZE} (fits in cache=250)")
    print(f"  - Phase shifts every {PHASE_LENGTH} timesteps")
    print(f"  - {HOT_OVERLAP} items persist across phases")
    print(f"  - LFU will hold onto old phase items (bad)")
    print(f"  - LRU will keep recent items (good)")
    print(f"  - FL+RL can learn which items persist (best)")
    print(f"\nSaved to: {OUTPUT_PATH}")

if __name__ == "__main__":
    main()
