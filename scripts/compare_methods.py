"""Generate comparative bar plots for cache hit-rate and runtime across methods.

Example usage:
    python scripts/compare_methods.py \
        --methods baseline=experiments/results/rl_baseline.json \
        fl_central=experiments/synthetic/output/summary_fl.json \
        fl_rsu=experiments/results/fedavg_full.json \
        --out experiments/plots/comparison.png

The JSON files must contain keys: cache_hits, cache_misses, runtime_seconds.
"""
from __future__ import annotations

import argparse
from pathlib import Path
from typing import Dict

import matplotlib.pyplot as plt
import json


def parse_methods(args_list: list[str]) -> Dict[str, Path]:
    methods: Dict[str, Path] = {}
    for item in args_list:
        if "=" not in item:
            raise ValueError("--methods entries must be label=path.json")
        label, path = item.split("=", 1)
        methods[label] = Path(path)
    return methods


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--methods", nargs="+", required=True, help="label=path.json pairs")
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()

    methods = parse_methods(args.methods)

    labels = []
    hit_rates = []
    runtimes = []

    for label, path in methods.items():
        data = json.loads(path.read_text())
        hits = data["cache_hits"]
        misses = data["cache_misses"]
        hit_rates.append(hits / (hits + misses))
        runtimes.append(data["runtime_seconds"])
        labels.append(label)

    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(8, 6))

    ax1.bar(labels, hit_rates, color="tab:blue")
    ax1.set_ylabel("Hit rate")
    ax1.set_ylim(0, 1)

    ax2.bar(labels, runtimes, color="tab:green")
    ax2.set_ylabel("Runtime (s)")
    ax2.set_xlabel("Method")

    fig.tight_layout()
    args.out.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(args.out, dpi=150)
    print(f"Comparison plot saved to {args.out}")


if __name__ == "__main__":
    main()
