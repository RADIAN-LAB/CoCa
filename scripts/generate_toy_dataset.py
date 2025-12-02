#!/usr/bin/env python3
"""Generate a toy VANET trace with aggressively shifting hotspots.

This dataset is intentionally stylized so that:
  * Only a tiny subset of tasks is popular at any given phase.
  * The hot subset changes every ~100 timesteps (4 phases total).
  * A small global-hot group persists across all phases.

These characteristics create a scenario where proactive + adaptive caching
(FL+RL) can learn to track the moving hotspots, while static evictions (Random,
LRU, LFU) either keep stale items or evict too aggressively, resulting in a
large quantitative gap.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
from pathlib import Path

np.random.seed(7)

# ---------------------------------------------------------------------------
# Dataset parameters (tuned for large separations between policies)
# ---------------------------------------------------------------------------
NUM_TIMESTEPS = 400
TASKS_PER_TIMESTEP = 15  # ≈6000 tasks total
UNIQUE_TASKS = 1200      # Gives ~42% coverage with 500 total cache slots
GLOBAL_HOT = 12          # Always-popular templates
PHASE_COUNT = 4
PHASE_HOT = 40           # Hot templates per phase

print("=" * 70)
print("GENERATING TOY VANET DATASET WITH STRONG PHASED POPULARITY")
print("=" * 70)
print(f"Timesteps: {NUM_TIMESTEPS}")
print(f"Tasks per timestep (avg): {TASKS_PER_TIMESTEP}")
print(f"Total unique templates: {UNIQUE_TASKS}")
print(f"Global hot templates: {GLOBAL_HOT}")
print(f"Phases: {PHASE_COUNT} (hot set size={PHASE_HOT})")
print()

# ---------------------------------------------------------------------------
# Build task templates (task_type, priority, size)
# ---------------------------------------------------------------------------
data_sizes = [5, 10, 20, 50, 75, 100, 150, 200, 300, 400, 500, 750, 1000, 1500]
task_templates = []
for _ in range(UNIQUE_TASKS):
    task_templates.append(
        {
            "task_type": np.random.randint(0, 10),
            "priority": np.random.randint(1, 6),
            "data_size_kB": np.random.choice(data_sizes),
        }
    )

template_indices = np.arange(UNIQUE_TASKS)

# Global hot templates stay relevant throughout
global_hot = np.random.choice(template_indices, size=GLOBAL_HOT, replace=False)

phase_len = NUM_TIMESTEPS // PHASE_COUNT
phase_hot_indices: list[np.ndarray] = []
phase_cold_indices: list[np.ndarray] = []

mask_global = np.ones(UNIQUE_TASKS, dtype=bool)
mask_global[global_hot] = False

for _ in range(PHASE_COUNT):
    phase_hot = np.random.choice(template_indices[mask_global], size=PHASE_HOT, replace=False)
    phase_hot_indices.append(phase_hot)

    # Build cold pool for this phase (everything not in global+phase hot)
    mask = np.ones(UNIQUE_TASKS, dtype=bool)
    mask[global_hot] = False
    mask[phase_hot] = False
    phase_cold_indices.append(template_indices[mask])

# ---------------------------------------------------------------------------
# Generate task arrivals with strong phase-specific locality
# ---------------------------------------------------------------------------
tasks = []
task_id = 0

for ts in range(NUM_TIMESTEPS):
    num_tasks = np.random.poisson(TASKS_PER_TIMESTEP)
    num_tasks = max(8, min(20, num_tasks))

    phase_id = min(ts // phase_len, PHASE_COUNT - 1)
    hot = phase_hot_indices[phase_id]
    cold_pool = phase_cold_indices[phase_id]

    num_phase = max(4, int(num_tasks * 0.6))
    num_global = max(2, int(num_tasks * 0.25))
    num_cold = max(1, num_tasks - num_phase - num_global)

    selected = np.concatenate(
        [
            np.random.choice(hot, size=num_phase, replace=True),
            np.random.choice(global_hot, size=num_global, replace=True),
            np.random.choice(cold_pool, size=num_cold, replace=True),
        ]
    )

    for idx in selected:
        tpl = task_templates[idx]
        tasks.append(
            {
                "timestamp": ts,
                "timestep": ts,
                "task_id": task_id,
                "node_id": np.random.randint(100, 200),
                "task_type": tpl["task_type"],
                "priority": tpl["priority"],
                "data_size_kB": tpl["data_size_kB"],
                "origin_rsu": np.random.randint(1, 6),
                "destination_rsu": np.random.randint(1, 6),
                "fog_rsu": np.random.randint(1, 6),
                "final_rsu": np.random.randint(1, 6),
                "veh_speed_kmh": np.random.uniform(15, 90),
                "rsu_load": np.random.uniform(0.2, 0.9),
                "pop_decay": np.random.uniform(0.4, 1.0),
            }
        )
        task_id += 1

# ---------------------------------------------------------------------------
# Stats & export
# ---------------------------------------------------------------------------
df = pd.DataFrame(tasks)
unique_task_keys = df.groupby(["task_type", "priority", "data_size_kB"]).size()
actual_unique = len(unique_task_keys)
actual_repetition = len(df) / actual_unique
cache_coverage = (500 / actual_unique) * 100  # 5 RSUs x 100 entries

print("=" * 70)
print("DATASET STATISTICS")
print("=" * 70)
print(f"Total tasks: {len(df)}")
print(f"Effective unique templates: {actual_unique}")
print(f"Average repetition: {actual_repetition:.2f}x")
print(f"Cache coverage (500 slots): {cache_coverage:.1f}%")
print()

print("Frequency distribution (count -> number of templates):")
freq_counts = unique_task_keys.value_counts().value_counts().sort_index()
for freq, count in freq_counts.items():
    print(f"  {count:4d} templates appear {freq:2d} times")

print()
print("Top 10 most frequent templates:")
for (tt, pr, ds), count in unique_task_keys.nlargest(10).items():
    print(f"  Type={tt}, Priority={pr}, Size={ds}KB: {count} occurrences")

output_path = Path("experiments/synthetic/input/tasks_toy.csv")
output_path.parent.mkdir(parents=True, exist_ok=True)
df.to_csv(output_path, index=False)

print()
print("=" * 70)
print(f"✅ Toy dataset saved to: {output_path}")
print("=" * 70)
print("Expected behavior: FL+RL should learn to track per-phase hotspots,"
      " producing a noticeably larger hit-rate gap versus Random/LRU/LFU.")
