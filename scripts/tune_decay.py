#!/usr/bin/env python3
"""Tune decay parameter λ and compare performance."""

import os
import subprocess
import json
from pathlib import Path

# Test different decay rates
DECAY_VALUES = [0.01, 0.02, 0.05, 0.1, 0.2]
ROOT = Path(__file__).resolve().parents[1]

results = {}

for decay in DECAY_VALUES:
    print(f"\n=== Testing λ = {decay} ===")
    
    # Set environment variable and regenerate trace
    env = os.environ.copy()
    env['DECAY_LAMBDA'] = str(decay)
    
    # Generate trace with this decay rate
    subprocess.run([
        "python3", "scripts/generate_synthetic_trace.py"
    ], cwd=ROOT, env=env, check=True)
    
    # Run experiment
    output_file = ROOT / f"experiments/synthetic/output/summary_decay_{decay}.json"
    subprocess.run([
        "python3", "scripts/run_experiment.py",
        "--trace", "experiments/synthetic/input/tasks.csv",
        "--output", str(output_file)
    ], cwd=ROOT, check=True)
    
    # Load and store results
    with output_file.open() as f:
        data = json.load(f)
        results[decay] = {
            'hits': data['cache_hits'],
            'misses': data['cache_misses'],
            'hit_rate': data['cache_hits'] / (data['cache_hits'] + data['cache_misses']),
            'runtime': data['runtime_seconds'],
            'success_rate': data['success_rate']
        }
    
    print(f"λ={decay}: {results[decay]['hits']} hits, {results[decay]['hit_rate']:.3f} hit rate, {results[decay]['runtime']:.1f}s")

# Find best decay parameter
best_decay = max(results.keys(), key=lambda k: results[k]['hit_rate'])
print(f"\n=== SUMMARY ===")
print(f"Best decay parameter: λ = {best_decay}")
print(f"Best hit rate: {results[best_decay]['hit_rate']:.3f}")

# Save detailed results
summary_file = ROOT / "experiments/synthetic/output/decay_tuning_summary.json"
with summary_file.open("w") as f:
    json.dump({
        'best_decay': best_decay,
        'results': results
    }, f, indent=2)

print(f"Detailed results saved to: {summary_file}")
