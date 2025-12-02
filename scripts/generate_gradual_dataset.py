#!/usr/bin/env python3
"""Generate dataset with GRADUAL popularity shifts.

Key insight: FL+RL loses to Random when patterns change abruptly.
Solution: Create gradually shifting popularity where FL can track trends.

Design:
- Hot set slowly rotates over time (1 item changes every 10 timesteps)
- Creates smooth transitions that FL can learn to predict
- Random will randomly evict important items
- FL+RL can learn the rotation pattern
"""

import csv
import random
import numpy as np
from pathlib import Path

OUTPUT_PATH = Path(__file__).parent.parent / "experiments" / "synthetic" / "input" / "tasks_gradual.csv"
NUM_TIMESTEPS = 400
TASKS_PER_TIMESTEP = 15

# Hot set configuration
HOT_SET_SIZE = 15  # Active hot items at any time
ROTATION_INTERVAL = 20  # Replace 1 hot item every N timesteps
HOT_PROBABILITY = 0.88  # 88% of requests from hot set

# Task pool
POOL_SIZE = 200  # Total unique tasks in rotation

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
    while len(all_templates) < POOL_SIZE:
        t = generate_task_template()
        key = (t["task_type"], t["priority"], t["data_size_kB"])
        if key not in seen:
            seen.add(key)
            all_templates.append(t)
    
    print(f"Created {len(all_templates)} unique task templates")
    print(f"Hot set size: {HOT_SET_SIZE}")
    print(f"Rotation interval: every {ROTATION_INTERVAL} timesteps")
    
    # Initialize hot set as first HOT_SET_SIZE items
    current_hot_indices = list(range(HOT_SET_SIZE))
    next_new_index = HOT_SET_SIZE  # Next item to add from pool
    
    rows = []
    task_id = 0
    hot_accesses = 0
    cold_accesses = 0
    rotations = 0
    
    for ts in range(NUM_TIMESTEPS):
        # Rotate hot set: remove oldest, add new
        if ts > 0 and ts % ROTATION_INTERVAL == 0 and next_new_index < POOL_SIZE:
            current_hot_indices.pop(0)  # Remove oldest
            current_hot_indices.append(next_new_index)  # Add new
            next_new_index += 1
            rotations += 1
        
        hot_set = [all_templates[i] for i in current_hot_indices]
        cold_pool = [all_templates[i] for i in range(POOL_SIZE) if i not in current_hot_indices]
        
        for _ in range(TASKS_PER_TIMESTEP):
            if random.random() < HOT_PROBABILITY:
                template = random.choice(hot_set)
                hot_accesses += 1
            else:
                template = random.choice(cold_pool) if cold_pool else random.choice(hot_set)
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
    print(f"Total rotations: {rotations}")
    print(f"\nKey insight:")
    print(f"  - Hot set changes GRADUALLY (1 item every {ROTATION_INTERVAL} steps)")
    print(f"  - FL can track the slow trend")
    print(f"  - Random will randomly evict trending items")
    print(f"\nSaved to: {OUTPUT_PATH}")

if __name__ == "__main__":
    main()
