"""Plot cache hit/miss and FL loss curves from experiment logs.

Usage:
    python scripts/plot_results.py \
        --log experiments/logs/fl_training.csv \
        --out experiments/plots/latest_benchmark.png

Creates a 2×1 figure with:
1. Cache hit rate over timesteps
2. FL loss (average across RSUs) over timesteps
"""
from __future__ import annotations

import argparse
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--log", type=Path, required=True, help="CSV log produced by run_experiment.py")
    parser.add_argument("--out", type=Path, required=True, help="Output PNG path")
    args = parser.parse_args()

    df = pd.read_csv(args.log)
    df["hit_rate"] = df["cache_hits"] / (df["cache_hits"] + df["cache_misses"])

    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(8, 6), sharex=True)

    ax1.plot(df["timestamp"], df["hit_rate"], label="Cache hit-rate", color="tab:blue")
    ax1.set_ylabel("Hit rate")
    ax1.set_ylim(0, 1)
    ax1.legend(loc="lower right")

    ax2.plot(df["timestamp"], df["fl_loss"], label="FL loss", color="tab:orange")
    ax2.set_ylabel("Loss")
    ax2.set_xlabel("Timestep")
    ax2.legend(loc="upper right")

    fig.tight_layout()
    args.out.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(args.out, dpi=150)
    print(f"Plot saved to {args.out}")


if __name__ == "__main__":
    main()
