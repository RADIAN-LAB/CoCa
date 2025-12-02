#!/usr/bin/env python3
"""
Generate publication-quality technical plots for FL-RL-TRC evaluation.
"""

import json
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from pathlib import Path

# Set publication-quality style
plt.rcParams.update({
    'font.size': 12,
    'font.family': 'serif',
    'font.serif': ['Times New Roman'],
    'axes.labelsize': 14,
    'axes.titlesize': 16,
    'xtick.labelsize': 11,
    'ytick.labelsize': 11,
    'legend.fontsize': 11,
    'figure.titlesize': 18,
    'lines.linewidth': 2.5,
    'axes.linewidth': 1.5,
    'grid.linewidth': 0.8,
    'grid.alpha': 0.3,
})

# Create output directory
output_dir = Path('experiments/results/publication_plots')
output_dir.mkdir(parents=True, exist_ok=True)

# Load results
results_dir = Path('experiments/results')

def load_result(filename):
    filepath = results_dir / filename
    if filepath.exists():
        with open(filepath) as f:
            data = json.load(f)
            data['hit_rate'] = (data['cache_hits'] / data['total_tasks']) * 100
            data['success_rate_pct'] = data['success_rate'] * 100
            return data
    return None

# Load all experimental results
results = {
    'FL+RL': load_result('fl_rl_complete_training.json'),
    'FL+LFU': load_result('fl_lfu_new.json'),
    'FL+LRU': load_result('fl_lru_new.json'),
    'LFU (No FL)': load_result('lfu_no_fl_new.json'),
}

# Remove None values
results = {k: v for k, v in results.items() if v is not None}

print("Loaded results:")
for name, data in results.items():
    print(f"  {name}: {data['hit_rate']:.2f}% hit rate")

# ============================================================================
# Plot 1: Cache Hit Rate Comparison (Bar Chart)
# ============================================================================
fig, ax = plt.subplots(figsize=(10, 6))

methods = list(results.keys())
hit_rates = [results[m]['hit_rate'] for m in methods]

colors = ['#2E7D32', '#1976D2', '#1976D2', '#F57C00']
bars = ax.bar(methods, hit_rates, color=colors, edgecolor='black', linewidth=2, alpha=0.85)

# Add value labels on bars
for bar, rate in zip(bars, hit_rates):
    height = bar.get_height()
    ax.text(bar.get_x() + bar.get_width()/2., height + 0.5,
            f'{rate:.2f}%', ha='center', va='bottom', fontweight='bold', fontsize=12)

ax.set_ylabel('Cache Hit Rate (%)', fontweight='bold')
ax.set_title('Cache Hit Rate Performance Comparison', fontweight='bold', pad=15)
ax.set_ylim(0, 105)
ax.grid(axis='y', linestyle='--', alpha=0.4)
ax.set_axisbelow(True)

# Add horizontal line at 90%
ax.axhline(y=90, color='red', linestyle=':', linewidth=2, alpha=0.6, label='90% Target')
ax.legend(loc='lower right')

plt.tight_layout()
plt.savefig(output_dir / 'fig1_hit_rate_comparison.pdf', dpi=300, bbox_inches='tight')
plt.savefig(output_dir / 'fig1_hit_rate_comparison.png', dpi=300, bbox_inches='tight')
print("✓ Saved fig1_hit_rate_comparison")
plt.close()

# ============================================================================
# Plot 2: FL Training Convergence Curve
# ============================================================================
fl_log = pd.read_csv('experiments/logs/fl_training.csv')
fl_log['hit_rate'] = (fl_log['cache_hits'] / (fl_log['cache_hits'] + fl_log['cache_misses'])) * 100

fig, ax = plt.subplots(figsize=(10, 6))

# Plot hit rate with smoothing
ax.plot(fl_log['timestamp'], fl_log['hit_rate'], 
        color='#1976D2', linewidth=2.5, label='Cache Hit Rate', alpha=0.8)

# Add moving average trend
window = 20
fl_log['hit_rate_ma'] = fl_log['hit_rate'].rolling(window=window, center=True).mean()
ax.plot(fl_log['timestamp'], fl_log['hit_rate_ma'], 
        color='#D32F2F', linewidth=3, linestyle='--', label=f'{window}-Step Moving Average')

ax.set_xlabel('Training Timestep', fontweight='bold')
ax.set_ylabel('Cache Hit Rate (%)', fontweight='bold')
ax.set_title('FL Advisor Training Convergence', fontweight='bold', pad=15)
ax.grid(True, linestyle='--', alpha=0.4)
ax.legend(loc='lower right', framealpha=0.95)
ax.set_ylim(0, 105)

# Annotate key points
initial_rate = fl_log['hit_rate'].iloc[10]
final_rate = fl_log['hit_rate'].iloc[-1]

ax.annotate(f'Initial: {initial_rate:.1f}%', 
            xy=(10, initial_rate), xytext=(40, initial_rate - 15),
            fontsize=11, fontweight='bold',
            bbox=dict(boxstyle='round,pad=0.5', facecolor='yellow', alpha=0.7, edgecolor='black'),
            arrowprops=dict(arrowstyle='->', lw=2, color='black'))

ax.annotate(f'Converged: {final_rate:.1f}%', 
            xy=(199, final_rate), xytext=(150, final_rate + 5),
            fontsize=11, fontweight='bold',
            bbox=dict(boxstyle='round,pad=0.5', facecolor='lightgreen', alpha=0.7, edgecolor='black'),
            arrowprops=dict(arrowstyle='->', lw=2, color='black'))

plt.tight_layout()
plt.savefig(output_dir / 'fig2_fl_training_convergence.pdf', dpi=300, bbox_inches='tight')
plt.savefig(output_dir / 'fig2_fl_training_convergence.png', dpi=300, bbox_inches='tight')
print("✓ Saved fig2_fl_training_convergence")
plt.close()

# ============================================================================
# Plot 3: Multi-Metric Radar Chart
# ============================================================================
from math import pi

fig, ax = plt.subplots(figsize=(10, 10), subplot_kw=dict(projection='polar'))

categories = ['Hit Rate', 'Success Rate', 'Speed\n(Inverse Time)', 'Efficiency']
N = len(categories)

# Normalize metrics to 0-100 scale
def normalize_metrics(data):
    max_time = max([results[m]['average_completion'] for m in results])
    return [
        data['hit_rate'],
        data['success_rate_pct'],
        (1 - data['average_completion']/max_time) * 100,
        data['hit_rate'] * 0.7 + data['success_rate_pct'] * 0.3  # Combined efficiency
    ]

angles = [n / float(N) * 2 * pi for n in range(N)]
angles += angles[:1]

# Plot each method
colors_radar = ['#2E7D32', '#1976D2', '#1976D2', '#F57C00']
for (name, data), color in zip(results.items(), colors_radar):
    values = normalize_metrics(data)
    values += values[:1]
    ax.plot(angles, values, 'o-', linewidth=2.5, label=name, color=color, markersize=8)
    ax.fill(angles, values, alpha=0.15, color=color)

ax.set_xticks(angles[:-1])
ax.set_xticklabels(categories, fontsize=12, fontweight='bold')
ax.set_ylim(0, 100)
ax.set_yticks([20, 40, 60, 80, 100])
ax.set_yticklabels(['20%', '40%', '60%', '80%', '100%'], fontsize=10)
ax.grid(True, linestyle='--', alpha=0.5)
ax.set_title('Multi-Metric Performance Comparison', fontweight='bold', pad=20, fontsize=16)
ax.legend(loc='upper right', bbox_to_anchor=(1.3, 1.1), fontsize=11)

plt.tight_layout()
plt.savefig(output_dir / 'fig3_radar_chart.pdf', dpi=300, bbox_inches='tight')
plt.savefig(output_dir / 'fig3_radar_chart.png', dpi=300, bbox_inches='tight')
print("✓ Saved fig3_radar_chart")
plt.close()

# ============================================================================
# Plot 4: Performance Improvement Analysis
# ============================================================================
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 6))

# Left: Hit Rate Improvement
baseline_hit = results['FL+LFU']['hit_rate']
improvements = {name: data['hit_rate'] - baseline_hit for name, data in results.items()}

colors_imp = ['#2E7D32' if v > 0 else '#D32F2F' for v in improvements.values()]
bars1 = ax1.barh(list(improvements.keys()), list(improvements.values()), 
                 color=colors_imp, edgecolor='black', linewidth=2, alpha=0.85)

for bar, val in zip(bars1, improvements.values()):
    x_pos = val + (0.3 if val > 0 else -0.3)
    ax1.text(x_pos, bar.get_y() + bar.get_height()/2, 
             f'{val:+.2f}pp', ha='left' if val > 0 else 'right', 
             va='center', fontweight='bold', fontsize=11)

ax1.axvline(x=0, color='black', linestyle='-', linewidth=2)
ax1.set_xlabel('Hit Rate Improvement (percentage points)', fontweight='bold')
ax1.set_title('Hit Rate vs FL+LFU Baseline', fontweight='bold')
ax1.grid(axis='x', linestyle='--', alpha=0.4)

# Right: Success Rate Comparison
success_rates = [data['success_rate_pct'] for data in results.values()]
bars2 = ax2.bar(results.keys(), success_rates, 
                color=['#2E7D32', '#1976D2', '#1976D2', '#F57C00'],
                edgecolor='black', linewidth=2, alpha=0.85)

for bar, rate in zip(bars2, success_rates):
    ax2.text(bar.get_x() + bar.get_width()/2., bar.get_height() + 0.3,
             f'{rate:.2f}%', ha='center', va='bottom', fontweight='bold', fontsize=11)

ax2.set_ylabel('Task Success Rate (%)', fontweight='bold')
ax2.set_title('Task Success Rate Comparison', fontweight='bold')
ax2.set_ylim(0, 90)
ax2.grid(axis='y', linestyle='--', alpha=0.4)

plt.tight_layout()
plt.savefig(output_dir / 'fig4_improvement_analysis.pdf', dpi=300, bbox_inches='tight')
plt.savefig(output_dir / 'fig4_improvement_analysis.png', dpi=300, bbox_inches='tight')
print("✓ Saved fig4_improvement_analysis")
plt.close()

print("\n" + "="*70)
print("PUBLICATION PLOTS GENERATED SUCCESSFULLY")
print("="*70)
print(f"\nAll plots saved to: {output_dir}/")
print("\nGenerated files:")
print("  - fig1_hit_rate_comparison.pdf/png")
print("  - fig2_fl_training_convergence.pdf/png")
print("  - fig3_radar_chart.pdf/png")
print("  - fig4_improvement_analysis.pdf/png")
