#!/usr/bin/env python3
"""
Generate comparison plots for SUMO trace experiment results.
"""

import json
import matplotlib.pyplot as plt
import numpy as np
from pathlib import Path
from matplotlib.patches import Patch

# Set style
plt.style.use('seaborn-v0_8-darkgrid')
plt.rcParams['font.size'] = 11
plt.rcParams['font.weight'] = 'bold'

# Load all results
results_dir = Path('experiments/sumo/output')

methods = {
    'No Cache':       '1_no_cache_results.json',
    'Random':         '2_random_results.json',
    'LRU':            '3_lru_results.json',
    'LFU':            '4_lfu_results.json',
    'FL-Only':        '5_fl_only_results.json',
    'CoCa (FL+RL)':   '6_fl_rl_results.json',
}

data = {}
for name, filename in methods.items():
    filepath = results_dir / filename
    if filepath.exists():
        with open(filepath) as f:
            data[name] = json.load(f)
    else:
        print(f"Warning: {filename} not found")

# Calculate hit rates
for name in data:
    hits = data[name]['cache_hits']
    misses = data[name]['cache_misses']
    total = hits + misses
    data[name]['hit_rate'] = (hits / total * 100) if total > 0 else 0.0

# Create output directory
output_dir = Path('experiments/sumo/plots')
output_dir.mkdir(parents=True, exist_ok=True)

# Method display order (worst to best)
methods_order = ['No Cache', 'Random', 'LRU', 'LFU', 'FL-Only', 'CoCa (FL+RL)']

# Color scheme
color_map = {
    'CoCa (FL+RL)': '#2E7D32',   # Dark green (proposed)
    'FL-Only':      '#66BB6A',   # Light green
    'LRU':          '#1976D2',   # Blue
    'LFU':          '#42A5F5',   # Light blue
    'Random':       '#F57C00',   # Orange
    'No Cache':     '#757575',   # Gray
}

legend_elements = [
    Patch(facecolor='#2E7D32', edgecolor='black', label='CoCa (FL+RL) — Proposed'),
    Patch(facecolor='#66BB6A', edgecolor='black', label='FL-Only'),
    Patch(facecolor='#1976D2', edgecolor='black', label='LRU / LFU'),
    Patch(facecolor='#F57C00', edgecolor='black', label='Random'),
    Patch(facecolor='#757575', edgecolor='black', label='No Cache'),
]

# ============================================================================
# Plot 1: Success Rate Comparison (Horizontal Bar)
# ============================================================================
fig, ax = plt.subplots(figsize=(12, 6))

labels = [m for m in methods_order if m in data]
success_rates = [data[m]['success_rate'] * 100 for m in labels]
colors = [color_map[m] for m in labels]

bars = ax.barh(labels, success_rates, color=colors, edgecolor='black', linewidth=1.5)

for i, (bar, rate) in enumerate(zip(bars, success_rates)):
    ax.text(rate + 0.5, i, f'{rate:.1f}%', va='center', fontweight='bold', fontsize=11)

ax.set_xlabel('Task Success Rate (%)', fontsize=14, fontweight='bold')
ax.set_title('Task Success Rate — SUMO Trace (16,472 tasks, 5ms deadline)',
             fontsize=15, fontweight='bold', pad=20)
ax.set_xlim(0, 110)
ax.grid(axis='x', alpha=0.3, linestyle='--')
ax.legend(handles=legend_elements, loc='lower right', fontsize=10)

plt.tight_layout()
plt.savefig(output_dir / 'success_rate_comparison.pdf', dpi=300, bbox_inches='tight')
plt.savefig(output_dir / 'success_rate_comparison.png', dpi=300, bbox_inches='tight')
print("✓ Saved success_rate_comparison.pdf/png")
plt.close()

# ============================================================================
# Plot 2: Cache Hit Rate Comparison (Horizontal Bar)
# ============================================================================
fig, ax = plt.subplots(figsize=(12, 6))

# Exclude No Cache for hit rate plot
hr_labels = [m for m in methods_order if m in data and m != 'No Cache']
hit_rates = [data[m]['hit_rate'] for m in hr_labels]
hr_colors = [color_map[m] for m in hr_labels]

bars = ax.barh(hr_labels, hit_rates, color=hr_colors, edgecolor='black', linewidth=1.5)

for i, (bar, rate) in enumerate(zip(bars, hit_rates)):
    ax.text(rate + 0.5, i, f'{rate:.1f}%', va='center', fontweight='bold', fontsize=11)

ax.set_xlabel('Cache Hit Rate (%)', fontsize=14, fontweight='bold')
ax.set_title('Cache Hit Rate — SUMO Trace (100 slots/RSU, 145 unique keys)',
             fontsize=15, fontweight='bold', pad=20)
ax.set_xlim(0, 110)
ax.grid(axis='x', alpha=0.3, linestyle='--')
ax.legend(handles=legend_elements[:-1], loc='lower right', fontsize=10)

plt.tight_layout()
plt.savefig(output_dir / 'hit_rate_comparison.pdf', dpi=300, bbox_inches='tight')
plt.savefig(output_dir / 'hit_rate_comparison.png', dpi=300, bbox_inches='tight')
print("✓ Saved hit_rate_comparison.pdf/png")
plt.close()

# ============================================================================
# Plot 3: Average Completion Time (Horizontal Bar)
# ============================================================================
fig, ax = plt.subplots(figsize=(12, 6))

completion_times = [data[m]['average_completion'] for m in labels]

bars = ax.barh(labels, completion_times, color=colors, edgecolor='black', linewidth=1.5)

for i, (bar, t) in enumerate(zip(bars, completion_times)):
    ax.text(t + 0.15, i, f'{t:.2f} ms', va='center', fontweight='bold', fontsize=11)

# Draw deadline line
ax.axvline(x=5.0, color='red', linestyle='--', linewidth=2, label='Deadline (5ms)')

ax.set_xlabel('Average Completion Time (ms)', fontsize=14, fontweight='bold')
ax.set_title('Average Task Completion Time — SUMO Trace',
             fontsize=15, fontweight='bold', pad=20)
ax.set_xlim(0, max(completion_times) * 1.15)
ax.grid(axis='x', alpha=0.3, linestyle='--')
ax.legend(handles=legend_elements + [plt.Line2D([0], [0], color='red', linestyle='--', linewidth=2, label='Deadline (5ms)')],
          loc='lower right', fontsize=10)

plt.tight_layout()
plt.savefig(output_dir / 'completion_time_comparison.pdf', dpi=300, bbox_inches='tight')
plt.savefig(output_dir / 'completion_time_comparison.png', dpi=300, bbox_inches='tight')
print("✓ Saved completion_time_comparison.pdf/png")
plt.close()

# ============================================================================
# Plot 4: Multi-Metric Grouped Bar Chart
# ============================================================================
fig, ax = plt.subplots(figsize=(14, 7))

key_methods = ['No Cache', 'Random', 'LRU', 'LFU', 'FL-Only', 'CoCa (FL+RL)']
key_labels = [m for m in key_methods if m in data]

x = np.arange(len(key_labels))
width = 0.25

hit_rates_key = [data[m]['hit_rate'] for m in key_labels]
success_rates_key = [data[m]['success_rate'] * 100 for m in key_labels]
# Invert completion time (lower is better) and scale to 0-100
max_time = max([data[m]['average_completion'] for m in key_labels])
speed_scores = [(1 - data[m]['average_completion'] / max_time) * 100 for m in key_labels]

bars1 = ax.bar(x - width, success_rates_key, width, label='Success Rate (%)',
               color='#2E7D32', edgecolor='black', linewidth=1.2)
bars2 = ax.bar(x, hit_rates_key, width, label='Cache Hit Rate (%)',
               color='#1976D2', edgecolor='black', linewidth=1.2)
bars3 = ax.bar(x + width, speed_scores, width, label='Speed Score (%)',
               color='#F57C00', edgecolor='black', linewidth=1.2)

# Add value labels on bars
for bars, vals in [(bars1, success_rates_key), (bars2, hit_rates_key), (bars3, speed_scores)]:
    for bar, val in zip(bars, vals):
        if val > 0:
            ax.text(bar.get_x() + bar.get_width()/2., bar.get_height() + 1,
                    f'{val:.0f}', ha='center', va='bottom', fontweight='bold', fontsize=8)

ax.set_xlabel('Method', fontsize=14, fontweight='bold')
ax.set_ylabel('Performance Score (%)', fontsize=14, fontweight='bold')
ax.set_title('Multi-Metric Performance Comparison — SUMO Trace',
             fontsize=15, fontweight='bold', pad=20)
ax.set_xticks(x)
ax.set_xticklabels(key_labels, rotation=15, ha='right', fontsize=11)
ax.legend(fontsize=12, loc='upper left')
ax.grid(axis='y', alpha=0.3, linestyle='--')
ax.set_ylim(0, 115)

plt.tight_layout()
plt.savefig(output_dir / 'multi_metric_comparison.pdf', dpi=300, bbox_inches='tight')
plt.savefig(output_dir / 'multi_metric_comparison.png', dpi=300, bbox_inches='tight')
print("✓ Saved multi_metric_comparison.pdf/png")
plt.close()

# ============================================================================
# Plot 5: Cache Misses Comparison (Vertical Bar)
# ============================================================================
fig, ax = plt.subplots(figsize=(10, 6))

miss_labels = [m for m in methods_order if m in data and m != 'No Cache']
misses = [data[m]['cache_misses'] for m in miss_labels]
miss_colors = [color_map[m] for m in miss_labels]

bars = ax.bar(miss_labels, misses, color=miss_colors, edgecolor='black', linewidth=1.5)

for bar, val in zip(bars, misses):
    ax.text(bar.get_x() + bar.get_width()/2., bar.get_height() + 50,
            f'{val:,}', ha='center', va='bottom', fontweight='bold', fontsize=11)

ax.set_ylabel('Cache Misses', fontsize=14, fontweight='bold')
ax.set_title('Cache Misses — SUMO Trace (lower is better)',
             fontsize=15, fontweight='bold', pad=20)
ax.grid(axis='y', alpha=0.3, linestyle='--')

plt.tight_layout()
plt.savefig(output_dir / 'cache_misses_comparison.pdf', dpi=300, bbox_inches='tight')
plt.savefig(output_dir / 'cache_misses_comparison.png', dpi=300, bbox_inches='tight')
print("✓ Saved cache_misses_comparison.pdf/png")
plt.close()

# ============================================================================
# Plot 6: CoCa Improvement Summary (Radar/Spider Chart)
# ============================================================================
fig, ax = plt.subplots(figsize=(8, 8), subplot_kw=dict(polar=True))

categories = ['Success\nRate', 'Hit\nRate', 'Speed\nScore', 'Miss\nReduction', 'Runtime\nEfficiency']
N = len(categories)

# Normalize all metrics to 0-100 for radar chart
best_baseline = 'LRU'  # best traditional baseline
coca = 'CoCa (FL+RL)'

if best_baseline in data and coca in data:
    # Success rate (already %)
    bl_success = data[best_baseline]['success_rate'] * 100
    coca_success = data[coca]['success_rate'] * 100

    # Hit rate (already %)
    bl_hit = data[best_baseline]['hit_rate']
    coca_hit = data[coca]['hit_rate']

    # Speed score (inverse of completion time, normalized)
    bl_speed = (1 - data[best_baseline]['average_completion'] / 14.31) * 100
    coca_speed = (1 - data[coca]['average_completion'] / 14.31) * 100

    # Miss reduction (fewer misses = better, normalized)
    max_misses = 3456  # Random has most
    bl_miss_red = (1 - data[best_baseline]['cache_misses'] / max_misses) * 100
    coca_miss_red = (1 - data[coca]['cache_misses'] / max_misses) * 100

    # Runtime efficiency (faster = better)
    max_runtime = data['No Cache']['runtime_seconds']
    bl_runtime_eff = (1 - data[best_baseline]['runtime_seconds'] / max_runtime) * 100
    coca_runtime_eff = (1 - data[coca]['runtime_seconds'] / max_runtime) * 100

    bl_values = [bl_success, bl_hit, bl_speed, bl_miss_red, bl_runtime_eff]
    coca_values = [coca_success, coca_hit, coca_speed, coca_miss_red, coca_runtime_eff]

    # Close the polygon
    angles = [n / float(N) * 2 * np.pi for n in range(N)]
    bl_values += bl_values[:1]
    coca_values += coca_values[:1]
    angles += angles[:1]

    ax.plot(angles, coca_values, 'o-', linewidth=2.5, color='#2E7D32', label='CoCa (FL+RL)')
    ax.fill(angles, coca_values, alpha=0.25, color='#2E7D32')
    ax.plot(angles, bl_values, 'o-', linewidth=2.5, color='#1976D2', label=f'Best Baseline ({best_baseline})')
    ax.fill(angles, bl_values, alpha=0.15, color='#1976D2')

    ax.set_xticks(angles[:-1])
    ax.set_xticklabels(categories, fontsize=11, fontweight='bold')
    ax.set_ylim(0, 105)
    ax.set_title('CoCa vs Best Baseline — Radar Comparison',
                 fontsize=15, fontweight='bold', pad=30)
    ax.legend(loc='lower right', fontsize=11, bbox_to_anchor=(1.15, -0.05))

plt.tight_layout()
plt.savefig(output_dir / 'radar_comparison.pdf', dpi=300, bbox_inches='tight')
plt.savefig(output_dir / 'radar_comparison.png', dpi=300, bbox_inches='tight')
print("✓ Saved radar_comparison.pdf/png")
plt.close()

# ============================================================================
# Summary
# ============================================================================
print("\n" + "="*70)
print("SUMO EXPERIMENT RESULTS SUMMARY")
print("="*70)

print(f"\n{'Method':<20} {'Success':<12} {'Hit Rate':<12} {'Avg Time':<12} {'Misses':<10}")
print("-"*70)
for method in methods_order:
    if method in data:
        success = data[method]['success_rate'] * 100
        hit_rate = data[method]['hit_rate']
        avg_time = data[method]['average_completion']
        misses = data[method]['cache_misses']
        print(f"{method:<20} {success:>9.1f}%  {hit_rate:>9.1f}%  {avg_time:>9.2f} ms  {misses:>8,}")

print(f"\n✓ All 6 plots saved to {output_dir}/")
