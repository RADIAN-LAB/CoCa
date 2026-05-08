"""Convert SUMO FCD trace to task CSV compatible with run_experiment.py.

RSU Placement:
  10 RSUs placed at intersections of the 5x5 grid (1200m x 1200m area).
  Each RSU covers a 300m radius. Vehicles are assigned to the nearest RSU.

Task Generation:
  Each vehicle generates a task at every timestep it is active.
  Task types are derived from vehicle speed/position patterns to simulate
  realistic VANET workloads (navigation, media streaming, safety alerts, etc.).

Output CSV columns match the synthetic format:
  timestamp, node_id, task_id, task_type, priority, data_size_kB,
  origin_rsu, destination_rsu, fog_rsu, final_rsu,
  veh_speed_kmh, veh_dir_deg, rsu_load, pop_decay, pos_x, pos_y
"""
from __future__ import annotations

import argparse
import csv
import math
import random
import xml.etree.ElementTree as ET
from pathlib import Path
from collections import defaultdict

_SEED = int(__import__("os").environ.get("TASK_GEN_SEED", "42"))
random.seed(_SEED)

# ---------------------------------------------------------------------------
# RSU placement on the 5x5 grid network
# Grid nodes are at (i*300, j*300) for i,j in [0..4]
# We place 10 RSUs at strategic intersections for good coverage
# ---------------------------------------------------------------------------
RSU_POSITIONS = {
    1:  (300, 300),    # SW intersection
    2:  (900, 300),    # SE intersection
    3:  (600, 600),    # Center intersection
    4:  (300, 900),    # NW intersection
    5:  (900, 900),    # NE intersection
}

RSU_RANGE = 500.0  # meters — coverage radius (larger to cover 5-RSU layout)

# Task type definitions (simulate diverse VANET workloads)
# 0: Navigation/routing, 1: Safety alert, 2: Media streaming,
# 3: Sensor data processing, 4: Cooperative perception,
# 5: Traffic info, 6: Parking search, 7: Emergency, 8: Infotainment, 9: V2X msg
NUM_TASK_TYPES = 10

# Discrete data size buckets per task type (kB)
# Using fixed buckets (S/M/L) instead of continuous random values
# so that cache keys are reusable across similar requests.
TASK_SIZE_BUCKETS = {
    0: [64, 128, 192, 256, 384],       # Navigation
    1: [16, 32, 48, 64, 96],           # Safety alert (small, urgent)
    2: [512, 768, 1024, 1280, 1536],   # Media streaming (large)
    3: [128, 256, 384, 512, 768],      # Sensor data
    4: [256, 384, 512, 768, 1024],     # Cooperative perception
    5: [32, 64, 96, 128, 192],         # Traffic info
    6: [32, 64, 96, 128, 192],         # Parking search
    7: [16, 24, 32, 48, 64],           # Emergency (small, critical)
    8: [512, 768, 1024, 1280, 1536],   # Infotainment
    9: [64, 128, 192, 256, 384],       # V2X message
}

# Priority weights per task type (higher = more urgent)
TASK_PRIORITY_WEIGHTS = {
    0: [0.2, 0.5, 0.3],   # Navigation: mostly medium
    1: [0.05, 0.15, 0.8],  # Safety: mostly high
    2: [0.6, 0.3, 0.1],   # Media: mostly low
    3: [0.3, 0.5, 0.2],   # Sensor: medium
    4: [0.1, 0.3, 0.6],   # Cooperative: high
    5: [0.4, 0.4, 0.2],   # Traffic: low-medium
    6: [0.5, 0.4, 0.1],   # Parking: low
    7: [0.0, 0.1, 0.9],   # Emergency: critical
    8: [0.7, 0.2, 0.1],   # Infotainment: low
    9: [0.2, 0.4, 0.4],   # V2X: medium-high
}


def distance(p1, p2):
    return math.sqrt((p1[0] - p2[0])**2 + (p1[1] - p2[1])**2)


def nearest_rsu(x, y):
    """Return the RSU ID closest to the given position."""
    best_id, best_dist = 1, float("inf")
    for rid, (rx, ry) in RSU_POSITIONS.items():
        d = distance((x, y), (rx, ry))
        if d < best_dist:
            best_id, best_dist = rid, d
    return best_id


def assign_task_type(speed_ms, x, y, ts):
    """Assign task type based on vehicle context.
    
    - High speed → navigation/safety tasks
    - Stopped/slow → parking/infotainment
    - Position-based hotspots for media/cooperative tasks
    """
    speed_kmh = speed_ms * 3.6
    
    if speed_kmh > 80:
        # Highway-like speed: safety + navigation
        return random.choices([0, 1, 4, 9], weights=[0.3, 0.3, 0.2, 0.2])[0]
    elif speed_kmh > 40:
        # Normal urban driving
        return random.choices(range(NUM_TASK_TYPES), 
                            weights=[0.15, 0.1, 0.1, 0.15, 0.1, 0.15, 0.05, 0.02, 0.08, 0.1])[0]
    elif speed_kmh > 5:
        # Slow traffic / congestion
        return random.choices([0, 2, 5, 6, 8, 3], weights=[0.1, 0.2, 0.15, 0.15, 0.25, 0.15])[0]
    else:
        # Stopped (intersection, parking)
        return random.choices([2, 6, 8, 5, 3], weights=[0.2, 0.3, 0.3, 0.1, 0.1])[0]


def generate_priority(task_type):
    """Generate priority 1-3 based on task type distribution."""
    weights = TASK_PRIORITY_WEIGHTS[task_type]
    return random.choices([1, 2, 3], weights=weights)[0]


def generate_data_size(task_type):
    """Generate data size in kB from discrete buckets for the task type."""
    return random.choice(TASK_SIZE_BUCKETS[task_type])


def compute_pop_decay(ts, max_ts):
    """Popularity decay factor — newer tasks are more popular."""
    return max(0.1, 1.0 - (ts / max_ts) * 0.5)


def main():
    parser = argparse.ArgumentParser(description="Convert SUMO FCD trace to task CSV")
    parser.add_argument("--fcd", required=True, type=Path, help="SUMO FCD XML file")
    parser.add_argument("--output", required=True, type=Path, help="Output CSV file")
    parser.add_argument("--task-prob", type=float, default=0.7,
                        help="Probability that a vehicle generates a task per timestep (default: 0.7)")
    parser.add_argument("--num-rsus", type=int, default=10,
                        help="Number of RSUs to use (default: 10)")
    args = parser.parse_args()

    print(f"Parsing SUMO FCD trace: {args.fcd}")
    tree = ET.parse(args.fcd)
    root = tree.getroot()

    timesteps = root.findall("timestep")
    max_ts = len(timesteps)
    print(f"  Found {max_ts} timesteps")

    # Count total vehicles
    all_veh_ids = set()
    for ts_elem in timesteps:
        for veh in ts_elem.findall("vehicle"):
            all_veh_ids.add(veh.get("id"))
    print(f"  Total unique vehicles: {len(all_veh_ids)}")

    # RSU load tracking
    rsu_task_count = defaultdict(int)
    task_id_counter = 0
    rows = []

    for ts_elem in timesteps:
        ts = int(float(ts_elem.get("time")))
        vehicles = ts_elem.findall("vehicle")
        
        if not vehicles:
            continue

        # Reset per-timestep RSU load
        ts_rsu_load = defaultdict(int)

        for veh in vehicles:
            # Probabilistic task generation
            if random.random() > args.task_prob:
                continue

            veh_id_str = veh.get("id")
            # Extract numeric node_id from "veh_123"
            node_id = int(veh_id_str.split("_")[1])
            x = float(veh.get("x"))
            y = float(veh.get("y"))
            speed = float(veh.get("speed"))  # m/s
            angle = float(veh.get("angle"))
            
            speed_kmh = round(speed * 3.6, 1)

            # Assign RSUs
            origin_rsu = nearest_rsu(x, y)
            
            # Destination RSU: simulate that vehicle is heading somewhere
            # Use angle to estimate future position
            future_x = x + math.cos(math.radians(90 - angle)) * 300
            future_y = y + math.sin(math.radians(90 - angle)) * 300
            dest_rsu = nearest_rsu(future_x, future_y)
            
            fog_rsu = origin_rsu  # Process at nearest RSU
            final_rsu = dest_rsu

            # Generate task
            task_type = assign_task_type(speed, x, y, ts)
            priority = generate_priority(task_type)
            data_size = generate_data_size(task_type)
            pop_decay = round(compute_pop_decay(ts, max_ts), 3)

            ts_rsu_load[fog_rsu] += 1
            task_id_counter += 1

            rows.append({
                "timestamp": ts,
                "node_id": node_id,
                "task_id": task_id_counter,
                "task_type": task_type,
                "priority": priority,
                "data_size_kB": data_size,
                "origin_rsu": origin_rsu,
                "destination_rsu": dest_rsu,
                "fog_rsu": fog_rsu,
                "final_rsu": final_rsu,
                "veh_speed_kmh": speed_kmh,
                "veh_dir_deg": round(angle, 1),
                "rsu_load": 0.0,  # Will be filled below
                "pop_decay": pop_decay,
                "pos_x": round(x, 1),
                "pos_y": round(y, 1),
            })

        # Update RSU load for this timestep's tasks
        total_capacity = 50  # tasks per RSU per timestep
        for row in rows:
            if row["timestamp"] == ts:
                load = ts_rsu_load[row["fog_rsu"]] / total_capacity
                row["rsu_load"] = round(min(load, 1.0), 3)

    # Write CSV
    args.output.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = [
        "timestamp", "node_id", "task_id", "task_type", "priority",
        "data_size_kB", "origin_rsu", "destination_rsu", "fog_rsu", "final_rsu",
        "veh_speed_kmh", "veh_dir_deg", "rsu_load", "pop_decay", "pos_x", "pos_y"
    ]
    
    with open(args.output, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    # Print statistics
    print(f"\n--- SUMO Trace Conversion Summary ---")
    print(f"  Output: {args.output}")
    print(f"  Total tasks: {len(rows)}")
    print(f"  Timesteps with tasks: {len(set(r['timestamp'] for r in rows))}")
    print(f"  Unique vehicles: {len(set(r['node_id'] for r in rows))}")
    print(f"  RSUs used: {len(set(r['fog_rsu'] for r in rows))}")
    
    # Task type distribution
    type_counts = defaultdict(int)
    for r in rows:
        type_counts[r["task_type"]] += 1
    type_names = ["Navigation", "Safety", "Media", "Sensor", "CoopPerception",
                  "Traffic", "Parking", "Emergency", "Infotainment", "V2X"]
    print(f"\n  Task type distribution:")
    for t in range(NUM_TASK_TYPES):
        pct = type_counts[t] / len(rows) * 100
        print(f"    {t} ({type_names[t]}): {type_counts[t]} ({pct:.1f}%)")
    
    # RSU load distribution
    rsu_counts = defaultdict(int)
    for r in rows:
        rsu_counts[r["fog_rsu"]] += 1
    print(f"\n  RSU task distribution:")
    for rid in sorted(rsu_counts.keys()):
        print(f"    RSU {rid}: {rsu_counts[rid]} tasks")
    
    # Speed distribution
    speeds = [r["veh_speed_kmh"] for r in rows]
    print(f"\n  Speed stats: min={min(speeds):.1f}, max={max(speeds):.1f}, "
          f"avg={sum(speeds)/len(speeds):.1f} km/h")


if __name__ == "__main__":
    main()
