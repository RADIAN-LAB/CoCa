#!/usr/bin/env python3
"""
Generate publication-quality bar plots with error bars from multi-seed results.

Reads: experiments/multi_seed/aggregated_results.json
Outputs: experiments/multi_seed/fig_*.png and fig_*.pdf
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.ticker import MultipleLocator

ROOT = Path(__file__).resolve().parents[1]
AGG_FILE = ROOT / "experiments" / "multi_seed" / "aggregated_results.json"
OUTPUT_DIR = ROOT / "experiments" / "multi_seed"

# ── Style ──────────────────────────────────────────────────────────────────
plt.rcParams.update({
    "figure.dpi": 100,
    "font.size": 13,
    "font.weight": "bold",
    "font.family": "sans-serif",
    "axes.labelsize": 14,
    "axes.labelweight": "bold",
    "xtick.labelsize": 11,
    "ytick.labelsize": 12,
    "legend.fontsize": 11,
})

METHODS_ORDER = [
    "1_no_cache", "2_random", "3_lru", "4_lfu", "5_fl_only", "6_fl_rl"
]

COLORS = {
    "1_no_cache": "#C0C0C0",
    "2_random":   "#E15759",
    "3_lru":      "#4E79A7",
    "4_lfu":      "#9B59B6",
    "5_fl_only":  "#F28E2B",
    "6_fl_rl":    "#59A14F",
}

DISPLAY_NAMES = {
    "1_no_cache": "No Cache",
    "2_random":   "Random",
    "3_lru":      "LRU",
    "4_lfu":      "LFU",
    "5_fl_only":  "FL-Only",
    "6_fl_rl":    "CoCa\n(FL+RL)",
}


def style_ax(ax):
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.grid(axis="y", linestyle="--", alpha=0.4)
    ax.set_axisbelow(True)


def make_bar_plot(ax, methods, means, stds, ylabel, ylim=None, y_major=None,
                  hline=None, hline_label=None, fmt_fn=None):
    """Generic bar chart with error bars."""
    x = np.arange(len(methods))
    width = 0.5
    colors = [COLORS[m] for m in methods]
    labels = [DISPLAY_NAMES[m] for m in methods]

    bars = ax.bar(x, means, width, yerr=stds, capsize=5, color=colors,
                  edgecolor="white", linewidth=1, alpha=0.9,
                  error_kw={"elinewidth": 1.5, "capthick": 1.5, "color": "#333"})

    # Trend line through bar tops
    ax.plot(x, means, "o--", color="#2E5984", markersize=7, linewidth=2,
            markeredgecolor="white", markeredgewidth=1, zorder=5)

    if hline is not None:
        ax.axhline(y=hline, color="#E15759", linestyle="--", linewidth=2.5,
                   label=hline_label)
        ax.legend(loc="upper left", prop={"weight": "bold", "size": 11},
                  framealpha=1)

    ax.set_ylabel(ylabel, fontsize=14, fontweight="bold")
    ax.set_xlabel("Caching Method", fontsize=14, fontweight="bold")
    ax.set_xticks(x)
    ax.set_xticklabels(labels, fontsize=11, fontweight="bold")
    if ylim:
        ax.set_ylim(ylim)
    if y_major:
        ax.yaxis.set_major_locator(MultipleLocator(y_major))

    # Value labels on bars
    if fmt_fn is None:
        fmt_fn = lambda v: f"{v:.1f}"
    for bar, val in zip(bars, means):
        ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.01 * (ylim[1] if ylim else max(means)),
                fmt_fn(val), ha="center", va="bottom", fontsize=10, fontweight="bold")

    style_ax(ax)


def main():
    if not AGG_FILE.exists():
        print(f"ERROR: {AGG_FILE} not found. Run run_multi_seed.py first.")
        return 1

    with open(AGG_FILE) as f:
        data = json.load(f)

    # Filter to available methods in order
    methods = [m for m in METHODS_ORDER if m in data]

    def get(mid, metric):
        return data[mid]["metrics"][metric]

    # ── Figure 1: Success Rate ──────────────────────────────────────────
    fig, ax = plt.subplots(figsize=(10, 6))
    means = [get(m, "success_rate")["mean"] for m in methods]
    stds  = [get(m, "success_rate")["std"] for m in methods]
    make_bar_plot(ax, methods, means, stds,
                  "Task Success Rate (%)", ylim=(0, 110), y_major=20)
    plt.tight_layout()
    plt.savefig(OUTPUT_DIR / "fig_success_rate.png", dpi=300, bbox_inches="tight")
    plt.savefig(OUTPUT_DIR / "fig_success_rate.pdf", bbox_inches="tight")
    print("✓ fig_success_rate")
    plt.close()

    # ── Figure 2: Hit Rate (skip No Cache) ──────────────────────────────
    hr_methods = [m for m in methods if m != "1_no_cache"]
    fig, ax = plt.subplots(figsize=(10, 6))
    means = [get(m, "hit_rate")["mean"] for m in hr_methods]
    stds  = [get(m, "hit_rate")["std"] for m in hr_methods]
    make_bar_plot(ax, hr_methods, means, stds,
                  "Cache Hit Rate (%)", ylim=(0, 110), y_major=20)
    plt.tight_layout()
    plt.savefig(OUTPUT_DIR / "fig_hit_rate.png", dpi=300, bbox_inches="tight")
    plt.savefig(OUTPUT_DIR / "fig_hit_rate.pdf", bbox_inches="tight")
    print("✓ fig_hit_rate")
    plt.close()

    # ── Figure 3: Completion Time ───────────────────────────────────────
    fig, ax = plt.subplots(figsize=(10, 6))
    means = [get(m, "avg_completion")["mean"] for m in methods]
    stds  = [get(m, "avg_completion")["std"] for m in methods]
    make_bar_plot(ax, methods, means, stds,
                  "Average Completion Time (ms)", ylim=(0, 18), y_major=2,
                  hline=5.0, hline_label="Deadline (5 ms)",
                  fmt_fn=lambda v: f"{v:.2f}")
    plt.tight_layout()
    plt.savefig(OUTPUT_DIR / "fig_completion_time.png", dpi=300, bbox_inches="tight")
    plt.savefig(OUTPUT_DIR / "fig_completion_time.pdf", bbox_inches="tight")
    print("✓ fig_completion_time")
    plt.close()

    # ── Figure 4: Energy Consumption ────────────────────────────────────
    fig, ax = plt.subplots(figsize=(10, 6))
    means = [get(m, "energy")["mean"] for m in methods]
    stds  = [get(m, "energy")["std"] for m in methods]
    make_bar_plot(ax, methods, means, stds,
                  "Energy Consumption (Joules)", ylim=(0, 32000), y_major=5000,
                  fmt_fn=lambda v: f"{v:,.0f}")
    ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda v, _: f"{v:,.0f}"))
    plt.tight_layout()
    plt.savefig(OUTPUT_DIR / "fig_energy.png", dpi=300, bbox_inches="tight")
    plt.savefig(OUTPUT_DIR / "fig_energy.pdf", bbox_inches="tight")
    print("✓ fig_energy")
    plt.close()

    # ── Print summary for paper ─────────────────────────────────────────
    print("\n" + "=" * 80)
    print("RESULTS FOR PAPER (mean ± std, 30 seeds)")
    print("=" * 80)
    print(f"{'Method':<18} {'Success Rate':>20} {'Hit Rate':>20} {'Completion (ms)':>22} {'Energy (J)':>22}")
    print("-" * 105)
    for m in methods:
        sr = get(m, "success_rate")
        hr = get(m, "hit_rate")
        ct = get(m, "avg_completion")
        en = get(m, "energy")
        print(f"{DISPLAY_NAMES[m].replace(chr(10),' '):<18} "
              f"{sr['mean']:>8.2f} ± {sr['std']:>5.2f}   "
              f"{hr['mean']:>8.2f} ± {hr['std']:>5.2f}   "
              f"{ct['mean']:>8.4f} ± {ct['std']:>6.4f}   "
              f"{en['mean']:>10.1f} ± {en['std']:>7.1f}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
