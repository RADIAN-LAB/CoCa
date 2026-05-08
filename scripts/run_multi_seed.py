#!/usr/bin/env python3
"""
Run experiments with 30 different random seeds for statistical significance.

Pipeline per seed:
  1. Generate task CSV from SUMO FCD trace with seed-specific randomness
  2. Run all 6 methods on that CSV
  3. Collect results

Output:
  experiments/multi_seed/seed_<N>/<method>_results.json   (per-run)
  experiments/multi_seed/aggregated_results.json           (mean ± std)
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
NUM_SEEDS = 30
SEEDS = list(range(1, NUM_SEEDS + 1))  # seeds 1..30

FCD_TRACE = ROOT / "experiments" / "sumo" / "output" / "fcd_trace.xml"
RL_MODEL  = ROOT / "experiments" / "models" / "final_rl_trained.pt"

METHODS = {
    "1_no_cache": {
        "name": "No Cache",
        "exp_args": ["--evict_policy", "none", "--no_fl"],
    },
    "2_random": {
        "name": "Random",
        "exp_args": ["--evict_policy", "random", "--no_fl"],
    },
    "3_lru": {
        "name": "LRU",
        "exp_args": ["--evict_policy", "lru", "--no_fl"],
    },
    "4_lfu": {
        "name": "LFU",
        "exp_args": ["--evict_policy", "lfu", "--no_fl"],
    },
    "5_fl_only": {
        "name": "FL-Only",
        "exp_args": ["--evict_policy", "lfu"],  # FL enabled + fixed LFU eviction
    },
    "6_fl_rl": {
        "name": "CoCa (FL+RL)",
        "exp_args": ["--load_rl", str(RL_MODEL)],  # FL + RL
    },
}

OUTPUT_BASE = ROOT / "experiments" / "multi_seed"


def generate_trace(seed: int, output_csv: Path) -> bool:
    """Generate task CSV from SUMO FCD with a specific random seed."""
    cmd = [
        sys.executable,
        str(ROOT / "experiments" / "sumo" / "sumo_to_tasks.py"),
        "--fcd", str(FCD_TRACE),
        "--output", str(output_csv),
    ]
    env = {**__import__("os").environ, "PYTHONPATH": str(ROOT)}
    
    # Patch: we inject the seed by modifying the script's random.seed call
    # Instead, we use a wrapper approach: set env var and patch sumo_to_tasks
    env["TASK_GEN_SEED"] = str(seed)
    
    result = subprocess.run(cmd, capture_output=True, text=True, env=env)
    if result.returncode != 0:
        print(f"  [ERROR] trace generation failed for seed {seed}: {result.stderr[:200]}")
        return False
    return True


def run_single_experiment(trace_csv: Path, method_id: str, output_json: Path) -> bool:
    """Run one method on one trace."""
    cfg = METHODS[method_id]
    cmd = [
        sys.executable,
        str(ROOT / "scripts" / "run_experiment.py"),
        "--trace", str(trace_csv),
        "--output", str(output_json),
    ] + cfg["exp_args"]

    env = {**__import__("os").environ, "PYTHONPATH": str(ROOT)}
    result = subprocess.run(cmd, capture_output=True, text=True, env=env)
    if result.returncode != 0:
        print(f"  [ERROR] {method_id} failed: {result.stderr[:200]}")
        return False
    return True


def calculate_energy(res: dict) -> float:
    """Same energy model as run_comprehensive_comparison.py."""
    hits = res["cache_hits"]
    misses = res["cache_misses"]
    total = res["total_tasks"]
    sr = res["success_rate"]

    energy_hits = hits * 0.1
    energy_successful_misses = (misses * sr) * 2.0
    energy_failures = (total * (1 - sr)) * 1.5
    return energy_hits + energy_successful_misses + energy_failures


def aggregate_results(base_dir: Path, seeds: list[int]) -> dict:
    """Read all per-seed results and compute mean ± std."""
    import numpy as np

    all_data: dict[str, list[dict]] = {mid: [] for mid in METHODS}

    for seed in seeds:
        seed_dir = base_dir / f"seed_{seed:02d}"
        for mid in METHODS:
            fpath = seed_dir / f"{mid}_results.json"
            if not fpath.exists():
                continue
            with open(fpath) as f:
                res = json.load(f)
            total = res["total_tasks"]
            hits = res["cache_hits"]
            misses = res["cache_misses"]
            hit_rate = 100.0 * hits / total if total > 0 else 0.0
            energy = calculate_energy(res)

            all_data[mid].append({
                "seed": seed,
                "success_rate": res["success_rate"] * 100,
                "hit_rate": hit_rate,
                "avg_completion": res["average_completion"],
                "energy": energy,
                "total_tasks": total,
                "cache_hits": hits,
                "cache_misses": misses,
                "runtime": res["runtime_seconds"],
            })

    summary = {}
    for mid, runs in all_data.items():
        if not runs:
            continue
        n = len(runs)
        metrics = {}
        for key in ["success_rate", "hit_rate", "avg_completion", "energy",
                     "total_tasks", "cache_hits", "cache_misses", "runtime"]:
            vals = np.array([r[key] for r in runs])
            metrics[key] = {
                "mean": float(np.mean(vals)),
                "std": float(np.std(vals, ddof=1)) if n > 1 else 0.0,
                "min": float(np.min(vals)),
                "max": float(np.max(vals)),
                "n": n,
            }
        summary[mid] = {
            "name": METHODS[mid]["name"],
            "metrics": metrics,
            "raw": runs,
        }

    return summary


def main():
    parser = argparse.ArgumentParser(description="Run multi-seed experiments")
    parser.add_argument("--seeds", type=int, default=NUM_SEEDS,
                        help=f"Number of seeds to run (default: {NUM_SEEDS})")
    parser.add_argument("--aggregate-only", action="store_true",
                        help="Skip running experiments, just aggregate existing results")
    args = parser.parse_args()

    seeds = list(range(1, args.seeds + 1))
    OUTPUT_BASE.mkdir(parents=True, exist_ok=True)

    if not args.aggregate_only:
        total_runs = len(seeds) * len(METHODS)
        completed = 0
        t0 = time.time()

        for seed in seeds:
            seed_dir = OUTPUT_BASE / f"seed_{seed:02d}"
            seed_dir.mkdir(parents=True, exist_ok=True)

            trace_csv = seed_dir / "tasks.csv"

            # Step 1: Generate trace with this seed
            print(f"\n{'='*60}")
            print(f"SEED {seed}/{len(seeds)}")
            print(f"{'='*60}")
            
            if not trace_csv.exists():
                print(f"  Generating trace with seed={seed}...")
                if not generate_trace(seed, trace_csv):
                    print(f"  Skipping seed {seed}")
                    continue
            else:
                print(f"  Trace already exists: {trace_csv}")

            # Step 2: Run all methods
            for mid in METHODS:
                out_json = seed_dir / f"{mid}_results.json"
                if out_json.exists():
                    print(f"  {mid}: already done, skipping")
                    completed += 1
                    continue

                print(f"  Running {mid}...")
                ok = run_single_experiment(trace_csv, mid, out_json)
                completed += 1
                elapsed = time.time() - t0
                eta = elapsed / completed * (total_runs - completed) if completed > 0 else 0
                print(f"  [{completed}/{total_runs}] elapsed={elapsed:.0f}s, ETA={eta:.0f}s")

    # Step 3: Aggregate
    print(f"\n{'='*60}")
    print("AGGREGATING RESULTS")
    print(f"{'='*60}")

    summary = aggregate_results(OUTPUT_BASE, seeds)

    agg_file = OUTPUT_BASE / "aggregated_results.json"
    with open(agg_file, "w") as f:
        json.dump(summary, f, indent=2, default=str)
    print(f"Aggregated results saved to: {agg_file}")

    # Print summary table
    print(f"\n{'Method':<20} {'Success Rate':>20} {'Hit Rate':>20} {'Completion (ms)':>20} {'Energy (J)':>20} {'N':>5}")
    print("-" * 110)
    for mid, data in summary.items():
        m = data["metrics"]
        sr = m["success_rate"]
        hr = m["hit_rate"]
        ct = m["avg_completion"]
        en = m["energy"]
        print(f"{data['name']:<20} "
              f"{sr['mean']:>8.2f} ± {sr['std']:>5.2f}   "
              f"{hr['mean']:>8.2f} ± {hr['std']:>5.2f}   "
              f"{ct['mean']:>8.4f} ± {ct['std']:>6.4f}   "
              f"{en['mean']:>10.1f} ± {en['std']:>7.1f}   "
              f"{sr['n']:>3d}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
