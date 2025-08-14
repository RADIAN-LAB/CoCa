"""Generate a synthetic VANET scheduling trace for benchmarking.

Outputs:
    experiments/synthetic/input/tasks.csv
Columns:
    timestamp: integer time slot (s)
    node_id: vehicle id
    task_id: unique task identifier
    fog_rsu: RSU id where task originates
    final_rsu: RSU id where result needed
"""
from __future__ import annotations

import random
import math
import csv
import os
from pathlib import Path

NUM_TIMESTEPS = 200         # seconds
VEHICLES = range(1, 51)     # 50 cars
RSUS = range(1, 6)          # 5 RSUs/regions
TASK_PROB = 0.3             # probability a vehicle generates a task per timestep
random.seed(42)

out_dir = Path(__file__).resolve().parents[1] / "experiments" / "synthetic" / "input"
out_dir.mkdir(parents=True, exist_ok=True)

csv_path = out_dir / "tasks.csv"

with csv_path.open("w", newline="") as fh:
    writer = csv.writer(fh)
    writer.writerow([
        "timestamp",
        "node_id",
        "task_id",
        "task_type",
        "priority",
        "data_size_kB",
        "origin_rsu",
        "destination_rsu",
        "fog_rsu",
        "final_rsu",
        "veh_speed_kmh",
        "veh_dir_deg",
        "rsu_load",
        "pop_decay",
    ])
    task_counter = 1
    first_seen = {}
    LAMBDA = float(os.environ.get('DECAY_LAMBDA', '0.05'))  # decay rate

    for t in range(NUM_TIMESTEPS):
        for node in VEHICLES:
            if random.random() < TASK_PROB:
                fog = random.choice(list(RSUS))
                final = random.choice(list(RSUS))
                task_type = random.randint(0, 3)  # four types
                priority = random.randint(0, 3)
                data_kb = random.choice([100, 250, 500, 750, 1000])
                origin = fog
                dest = final
                # synthetic mobility & load
                speed = random.uniform(0, 120)
                direction = random.uniform(0, 359)
                rsu_load = random.random()
                key = (task_type, priority, data_kb)
                if key not in first_seen:
                    first_seen[key] = t
                pop_decay = math.exp(-LAMBDA * (t - first_seen[key]))
                writer.writerow([
                    t,
                    node,
                    task_counter,
                    task_type,
                    priority,
                    data_kb,
                    origin,
                    dest,
                    fog,
                    final,
                    round(speed,2),
                    round(direction,1),
                    round(rsu_load,3),
                    round(pop_decay,3),
                ])
                task_counter += 1
print(f"Generated {csv_path} with synthetic tasks.")
