#!/usr/bin/env python3
"""
Generate adversarial dataset designed to expose weaknesses of traditional policies.

Strategy:
1. ANTI-LRU pattern: Items accessed in bursts, then long gaps (LRU will evict too early)
2. ANTI-LFU pattern: Frequency changes over time (LFU holds stale items)
3. ANTI-RANDOM: Strong temporal locality (Random misses patterns)
4. PRO-FL+RL: Predictable patterns that FL can learn and RL can optimize

This creates a scenario where:
- LRU evicts items that will be needed soon (recency ≠ future use)
- LFU holds onto old popular items that are no longer needed
- Random has no strategy
- FL+RL learns the burst patterns and adapts
"""

import csv
import random
import numpy as np
from pathlib import Path

OUTPUT_PATH = Path(__file__).parent.parent / "experiments" / "synthetic" / "input" / "tasks_adversarial.csv"
NUM_TIMESTEPS = 400
TASKS_PER_TIMESTEP = 15

# Pattern configuration
BURST_SIZE = 20  # Number of tasks in a burst
BURST_INTERVAL = 50  # Timesteps between bursts
BURST_DURATION = 10  # How long each burst lasts
NUM_BURST_GROUPS = 5  # Different groups that burst at different times

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
    
    # Create task templates
    all_templates = []
    seen = set()
    needed = 500  # Large pool
    while len(all_templates) < needed:
        t = generate_task_template()
        key = (t["task_type"], t["priority"], t["data_size_kB"])
        if key not in seen:
            seen.add(key)
            all_templates.append(t)
    
    # Create burst groups - each group has its own set of tasks
    burst_groups = []
    for i in range(NUM_BURST_GROUPS):
        start = i * BURST_SIZE
        burst_groups.append({
            'tasks': all_templates[start:start + BURST_SIZE],
            'offset': i * (BURST_INTERVAL // NUM_BURST_GROUPS),  # Stagger bursts
            'active_phases': []  # Track when this group is active
        })
    
    # Determine when each group is active (creates predictable pattern for FL)
    for ts in range(NUM_TIMESTEPS):
        for i, group in enumerate(burst_groups):
            # Each group bursts every BURST_INTERVAL timesteps, lasting BURST_DURATION
            cycle_position = (ts - group['offset']) % BURST_INTERVAL
            if 0 <= cycle_position < BURST_DURATION:
                group['active_phases'].append(ts)
    
    # Background tasks (low frequency, used to pollute LFU cache)
    background_tasks = all_templates[NUM_BURST_GROUPS * BURST_SIZE:NUM_BURST_GROUPS * BURST_SIZE + 100]
    
    print(f"Created {NUM_BURST_GROUPS} burst groups with {BURST_SIZE} tasks each")
    print(f"Burst interval: {BURST_INTERVAL} timesteps")
    print(f"Burst duration: {BURST_DURATION} timesteps")
    print(f"Background tasks: {len(background_tasks)}")
    
    # Generate requests
    rows = []
    task_id = 0
    burst_accesses = 0
    background_accesses = 0
    
    for ts in range(NUM_TIMESTEPS):
        # Determine which burst groups are active
        active_groups = [g for g in burst_groups if ts in g['active_phases']]
        
        for _ in range(TASKS_PER_TIMESTEP):
            if active_groups and random.random() < 0.85:  # 85% from active bursts
                # Pick from active burst groups
                group = random.choice(active_groups)
                template = random.choice(group['tasks'])
                burst_accesses += 1
            else:
                # Background task (pollutes LFU cache)
                template = random.choice(background_tasks)
                background_accesses += 1
            
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
    
    total = burst_accesses + background_accesses
    print(f"\nGenerated {len(rows)} tasks over {NUM_TIMESTEPS} timesteps")
    print(f"Burst accesses: {burst_accesses} ({100*burst_accesses/total:.1f}%)")
    print(f"Background accesses: {background_accesses} ({100*background_accesses/total:.1f}%)")
    
    print(f"\nWhy traditional policies will fail:")
    print(f"  - LRU: Will evict burst items during gaps, then miss when burst returns")
    print(f"  - LFU: Will cache background tasks (frequent but useless)")
    print(f"  - Random: No pattern recognition")
    print(f"  - FL+RL: Can learn burst patterns and predict when items will be needed")
    
    print(f"\nSaved to: {OUTPUT_PATH}")

if __name__ == "__main__":
    main()
