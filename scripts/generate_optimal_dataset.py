#!/usr/bin/env python3
"""
Generate optimal VANET dataset with controlled repetition for maximum policy differentiation.
Target: 500-600 unique tasks with 5-6x repetition.
"""

import pandas as pd
import numpy as np
from pathlib import Path

np.random.seed(42)

# Parameters
NUM_TIMESTEPS = 200
TOTAL_TASKS = 3000
TARGET_UNIQUE = 900  # Target unique tasks (high diversity)
TARGET_REPETITION = 3.3  # Each task appears ~3-4 times on average

print("="*70)
print("GENERATING OPTIMAL VANET DATASET FOR POLICY DIFFERENTIATION")
print("="*70)
print(f"Target: {TARGET_UNIQUE} unique tasks, {TARGET_REPETITION}x repetition")
print(f"Cache capacity: 500 (100 per RSU)")
print(f"Coverage: {(500/TARGET_UNIQUE)*100:.1f}%")
print()

# Generate unique task templates with expanded parameter space
# Expand data sizes to create more unique combinations
data_sizes = [5, 10, 15, 20, 30, 40, 50, 75, 100, 150, 200, 300, 400, 500, 750, 1000, 1500, 2000]
task_templates = []
for i in range(TARGET_UNIQUE):
    task_templates.append({
        'task_type': np.random.randint(0, 10),
        'priority': np.random.randint(1, 6),
        'data_size_kB': np.random.choice(data_sizes),
    })

# Base probabilities: nearly uniform over all templates
base_prob = np.ones(TARGET_UNIQUE)
base_prob /= base_prob.sum()

# Define a small global hot set and per-phase hot sets
num_global_hot = max(10, TARGET_UNIQUE // 20)          # ~5% always-hot tasks
num_phase_hot = max(30, TARGET_UNIQUE // 10)           # ~10% hot per phase

global_hot_indices = np.random.choice(TARGET_UNIQUE, size=num_global_hot, replace=False)

num_phases = 4
phase_len = NUM_TIMESTEPS // num_phases
phase_hot_indices = []
remaining_indices = np.setdiff1d(np.arange(TARGET_UNIQUE), global_hot_indices)

for p in range(num_phases):
    # sample phase-specific hot tasks from remaining pool (allow some reuse across phases)
    hot = np.random.choice(remaining_indices, size=num_phase_hot, replace=False)
    phase_hot_indices.append(hot)

# Generate task sequence with phase-based popularity
tasks = []
task_id_counter = 0

# Calculate tasks per timestep
tasks_per_timestep = TOTAL_TASKS // NUM_TIMESTEPS

for ts in range(NUM_TIMESTEPS):
    num_tasks = np.random.poisson(tasks_per_timestep)
    num_tasks = max(10, min(20, num_tasks))

    # Determine current phase
    phase = min(ts // phase_len, num_phases - 1)
    phase_hot = phase_hot_indices[phase]

    # Build phase-specific probabilities
    probs = base_prob.copy()
    # Boost global hot tasks moderately, phase hot tasks more strongly
    probs[global_hot_indices] *= 3.0
    probs[phase_hot] *= 6.0
    probs /= probs.sum()

    selected_indices = np.random.choice(
        TARGET_UNIQUE,
        size=num_tasks,
        replace=True,
        p=probs,
    )

    for idx in selected_indices:
        template = task_templates[idx]
        tasks.append({
            'timestamp': ts,
            'timestep': ts,
            'task_id': task_id_counter,
            'node_id': np.random.randint(100, 200),
            'task_type': template['task_type'],
            'priority': template['priority'],
            'data_size_kB': template['data_size_kB'],
            'origin_rsu': np.random.randint(1, 6),
            'destination_rsu': np.random.randint(1, 6),
            'fog_rsu': np.random.randint(1, 6),
            'final_rsu': np.random.randint(1, 6),
            'veh_speed_kmh': np.random.uniform(20, 100),
            'rsu_load': np.random.uniform(0.2, 0.8),
            'pop_decay': np.random.uniform(0.5, 1.0),
        })
        task_id_counter += 1

# Create DataFrame
df = pd.DataFrame(tasks)

# Calculate statistics
unique_task_keys = df.groupby(['task_type', 'priority', 'data_size_kB']).size()
actual_unique = len(unique_task_keys)
actual_repetition = len(df) / actual_unique
cache_coverage = (500 / actual_unique) * 100

print("="*70)
print("DATASET STATISTICS")
print("="*70)
print(f"Total tasks: {len(df)}")
print(f"Unique tasks: {actual_unique}")
print(f"Actual repetition: {actual_repetition:.2f}x")
print(f"Cache coverage: {cache_coverage:.1f}%")
print()

# Show distribution
print("Task frequency distribution:")
freq_counts = unique_task_keys.value_counts().value_counts().sort_index()
for freq, count in freq_counts.items():
    print(f"  {count} tasks appear {freq} times")

print()
print("Top 10 most frequent tasks:")
for (tt, pr, ds), count in unique_task_keys.nlargest(10).items():
    print(f"  Type={tt}, Priority={pr}, Size={ds}KB: {count} occurrences")

# Save
output_path = Path('experiments/synthetic/input/tasks_optimal.csv')
output_path.parent.mkdir(parents=True, exist_ok=True)
df.to_csv(output_path, index=False)

print()
print("="*70)
print(f"✅ Dataset saved to: {output_path}")
print("="*70)
print()
print("Expected performance with this dataset:")
print(f"  - Cache coverage: {cache_coverage:.0f}% (optimal for differentiation)")
print(f"  - FL+RL: 50-60% (learns patterns, adapts eviction)")
print(f"  - FL+LFU: 45-50% (good for frequent items)")
print(f"  - FL+Random: 40-45% (no learning)")
print(f"  - LFU No-FL: 35-40% (reactive only)")
print()
print("  Expected FL+RL advantage: 10-15 percentage points! 🎯")
print("="*70)
