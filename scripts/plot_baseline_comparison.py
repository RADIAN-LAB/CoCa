#!/usr/bin/env python3
"""
Generate comparison plots for all baseline experiments.
"""

import json
import matplotlib.pyplot as plt
import numpy as np
from pathlib import Path

# Set style
plt.style.use('seaborn-v0_8-darkgrid')
plt.rcParams['font.size'] = 11
plt.rcParams['font.weight'] = 'bold'

# Load all results
results_dir = Path('experiments/results')

methods = {
    'FL+RL (Proposed)': 'fl_rl_improved_rerun.json',
    'FL+LFU': 'fl_lfu.json',
    'FL+LRU': 'fl_lru.json',
    'FL+Random': 'fl_random.json',
    'FL+FIFO': 'fl_fifo.json',
    'LRU (No FL)': 'lru_no_fl.json',
    'LFU (No FL)': 'lfu_no_fl.json',
    'Random (No FL)': 'random_no_fl.json',
    'No Cache': 'no_cache.json',
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
    total = data[name]['total_tasks']
    data[name]['hit_rate'] = (hits / total) * 100

# Create output directory
output_dir = Path('experiments/results/plots')
output_dir.mkdir(parents=True, exist_ok=True)

# ============================================================================
# Plot 1: Cache Hit Rate Comparison
# ============================================================================
fig, ax = plt.subplots(figsize=(12, 7))

methods_order = [
    'FL+RL (Proposed)',
    'FL+LFU',
    'FL+LRU', 
    'FL+Random',
    'FL+FIFO',
    'LRU (No FL)',
    'LFU (No FL)',
    'Random (No FL)',
    'No Cache'
]

hit_rates = [data[m]['hit_rate'] for m in methods_order if m in data]
method_labels = [m for m in methods_order if m in data]

# Color scheme: FL+RL in green, FL+Fixed in blue, No FL in orange
colors = []
for m in method_labels:
    if 'FL+RL' in m:
        colors.append('#2E7D32')  # Dark green
    elif 'FL+' in m:
        colors.append('#1976D2')  # Blue
    elif 'No FL' in m:
        colors.append('#F57C00')  # Orange
    else:
        colors.append('#757575')  # Gray

bars = ax.barh(method_labels, hit_rates, color=colors, edgecolor='black', linewidth=1.5)

# Add value labels
for i, (bar, rate) in enumerate(zip(bars, hit_rates)):
    ax.text(rate + 0.5, i, f'{rate:.2f}%', 
            va='center', fontweight='bold', fontsize=10)

ax.set_xlabel('Cache Hit Rate (%)', fontsize=14, fontweight='bold')
ax.set_title('Cache Hit Rate Comparison Across Different Approaches', 
             fontsize=16, fontweight='bold', pad=20)
ax.set_xlim(0, 105)
ax.grid(axis='x', alpha=0.3, linestyle='--')

# Add legend
from matplotlib.patches import Patch
legend_elements = [
    Patch(facecolor='#2E7D32', label='FL+RL (Proposed)'),
    Patch(facecolor='#1976D2', label='FL + Fixed Policy'),
    Patch(facecolor='#F57C00', label='No FL'),
    Patch(facecolor='#757575', label='No Cache Baseline')
]
ax.legend(handles=legend_elements, loc='lower right', fontsize=11)

plt.tight_layout()
plt.savefig(output_dir / 'hit_rate_comparison.pdf', dpi=300, bbox_inches='tight')
plt.savefig(output_dir / 'hit_rate_comparison.png', dpi=300, bbox_inches='tight')
print("✓ Saved hit_rate_comparison.pdf/png")
plt.close()

# ============================================================================
# Plot 2: Success Rate Comparison
# ============================================================================
fig, ax = plt.subplots(figsize=(12, 7))

success_rates = [data[m]['success_rate'] * 100 for m in methods_order if m in data]

bars = ax.barh(method_labels, success_rates, color=colors, edgecolor='black', linewidth=1.5)

for i, (bar, rate) in enumerate(zip(bars, success_rates)):
    ax.text(rate + 0.3, i, f'{rate:.2f}%', 
            va='center', fontweight='bold', fontsize=10)

ax.set_xlabel('Task Success Rate (%)', fontsize=14, fontweight='bold')
ax.set_title('Task Success Rate Comparison (Deadline Compliance)', 
             fontsize=16, fontweight='bold', pad=20)
ax.set_xlim(0, 90)
ax.grid(axis='x', alpha=0.3, linestyle='--')
ax.legend(handles=legend_elements, loc='lower right', fontsize=11)

plt.tight_layout()
plt.savefig(output_dir / 'success_rate_comparison.pdf', dpi=300, bbox_inches='tight')
plt.savefig(output_dir / 'success_rate_comparison.png', dpi=300, bbox_inches='tight')
print("✓ Saved success_rate_comparison.pdf/png")
plt.close()

# ============================================================================
# Plot 3: Average Completion Time Comparison
# ============================================================================
fig, ax = plt.subplots(figsize=(12, 7))

completion_times = [data[m]['average_completion'] for m in methods_order if m in data]

bars = ax.barh(method_labels, completion_times, color=colors, edgecolor='black', linewidth=1.5)

for i, (bar, time) in enumerate(zip(bars, completion_times)):
    ax.text(time + 0.1, i, f'{time:.2f} ms', 
            va='center', fontweight='bold', fontsize=10)

ax.set_xlabel('Average Completion Time (ms)', fontsize=14, fontweight='bold')
ax.set_title('Average Task Completion Time Comparison', 
             fontsize=16, fontweight='bold', pad=20)
ax.set_xlim(0, max(completion_times) * 1.15)
ax.grid(axis='x', alpha=0.3, linestyle='--')
ax.legend(handles=legend_elements, loc='lower right', fontsize=11)

plt.tight_layout()
plt.savefig(output_dir / 'completion_time_comparison.pdf', dpi=300, bbox_inches='tight')
plt.savefig(output_dir / 'completion_time_comparison.png', dpi=300, bbox_inches='tight')
print("✓ Saved completion_time_comparison.pdf/png")
plt.close()

# ============================================================================
# Plot 4: Multi-Metric Comparison (Grouped Bar Chart)
# ============================================================================
fig, ax = plt.subplots(figsize=(14, 8))

# Select key methods for cleaner visualization
key_methods = [
    'FL+RL (Proposed)',
    'FL+LFU',
    'FL+LRU',
    'LRU (No FL)',
    'No Cache'
]

x = np.arange(len(key_methods))
width = 0.25

# Normalize metrics to 0-100 scale for comparison
hit_rates_key = [data[m]['hit_rate'] for m in key_methods if m in data]
success_rates_key = [data[m]['success_rate'] * 100 for m in key_methods if m in data]
# Invert completion time (lower is better) and scale to 0-100
max_time = max([data[m]['average_completion'] for m in key_methods if m in data])
completion_scores = [(1 - data[m]['average_completion']/max_time) * 100 
                     for m in key_methods if m in data]

bars1 = ax.bar(x - width, hit_rates_key, width, label='Hit Rate (%)', 
               color='#2E7D32', edgecolor='black', linewidth=1.5)
bars2 = ax.bar(x, success_rates_key, width, label='Success Rate (%)', 
               color='#1976D2', edgecolor='black', linewidth=1.5)
bars3 = ax.bar(x + width, completion_scores, width, label='Speed Score (%)', 
               color='#F57C00', edgecolor='black', linewidth=1.5)

ax.set_xlabel('Method', fontsize=14, fontweight='bold')
ax.set_ylabel('Performance Score (%)', fontsize=14, fontweight='bold')
ax.set_title('Multi-Metric Performance Comparison', fontsize=16, fontweight='bold', pad=20)
ax.set_xticks(x)
ax.set_xticklabels([m for m in key_methods if m in data], rotation=15, ha='right')
ax.legend(fontsize=12, loc='lower left')
ax.grid(axis='y', alpha=0.3, linestyle='--')
ax.set_ylim(0, 105)

plt.tight_layout()
plt.savefig(output_dir / 'multi_metric_comparison.pdf', dpi=300, bbox_inches='tight')
plt.savefig(output_dir / 'multi_metric_comparison.png', dpi=300, bbox_inches='tight')
print("✓ Saved multi_metric_comparison.pdf/png")
plt.close()

# ============================================================================
# Plot 5: FL Impact Analysis
# ============================================================================
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 6))

# Compare FL vs No FL for same policies
policies = ['LRU', 'LFU', 'Random']
fl_rates = []
no_fl_rates = []

for policy in policies:
    fl_key = f'FL+{policy}'
    no_fl_key = f'{policy} (No FL)'
    if fl_key in data and no_fl_key in data:
        fl_rates.append(data[fl_key]['hit_rate'])
        no_fl_rates.append(data[no_fl_key]['hit_rate'])

x = np.arange(len(policies))
width = 0.35

bars1 = ax1.bar(x - width/2, fl_rates, width, label='With FL', 
                color='#1976D2', edgecolor='black', linewidth=1.5)
bars2 = ax1.bar(x + width/2, no_fl_rates, width, label='Without FL', 
                color='#F57C00', edgecolor='black', linewidth=1.5)

ax1.set_xlabel('Eviction Policy', fontsize=12, fontweight='bold')
ax1.set_ylabel('Cache Hit Rate (%)', fontsize=12, fontweight='bold')
ax1.set_title('Impact of FL Pre-placement', fontsize=14, fontweight='bold')
ax1.set_xticks(x)
ax1.set_xticklabels(policies)
ax1.legend(fontsize=11)
ax1.grid(axis='y', alpha=0.3, linestyle='--')

# Add value labels
for bars in [bars1, bars2]:
    for bar in bars:
        height = bar.get_height()
        ax1.text(bar.get_x() + bar.get_width()/2., height + 0.5,
                f'{height:.1f}%', ha='center', va='bottom', fontweight='bold', fontsize=9)

# RL Impact: FL+Fixed vs FL+RL
fixed_policies = ['FL+LFU', 'FL+LRU', 'FL+Random', 'FL+FIFO']
fixed_rates = [data[m]['hit_rate'] for m in fixed_policies if m in data]
fl_rl_rate = data['FL+RL (Proposed)']['hit_rate'] if 'FL+RL (Proposed)' in data else 0

ax2.bar(range(len(fixed_policies)), fixed_rates, color='#1976D2', 
        edgecolor='black', linewidth=1.5, label='FL + Fixed Policy')
ax2.axhline(y=fl_rl_rate, color='#2E7D32', linestyle='--', linewidth=3, 
            label=f'FL+RL: {fl_rl_rate:.2f}%')

ax2.set_xlabel('Fixed Policy', fontsize=12, fontweight='bold')
ax2.set_ylabel('Cache Hit Rate (%)', fontsize=12, fontweight='bold')
ax2.set_title('Impact of RL Adaptive Eviction', fontsize=14, fontweight='bold')
ax2.set_xticks(range(len(fixed_policies)))
ax2.set_xticklabels([p.replace('FL+', '') for p in fixed_policies])
ax2.legend(fontsize=11)
ax2.grid(axis='y', alpha=0.3, linestyle='--')

# Add value labels
for i, rate in enumerate(fixed_rates):
    ax2.text(i, rate + 0.5, f'{rate:.1f}%', ha='center', va='bottom', 
             fontweight='bold', fontsize=9)

plt.tight_layout()
plt.savefig(output_dir / 'fl_rl_impact_analysis.pdf', dpi=300, bbox_inches='tight')
plt.savefig(output_dir / 'fl_rl_impact_analysis.png', dpi=300, bbox_inches='tight')
print("✓ Saved fl_rl_impact_analysis.pdf/png")
plt.close()

# ============================================================================
# Summary Statistics
# ============================================================================
print("\n" + "="*70)
print("BASELINE COMPARISON SUMMARY")
print("="*70)

print(f"\n{'Method':<25} {'Hit Rate':<12} {'Success':<12} {'Avg Time':<12}")
print("-"*70)
for method in methods_order:
    if method in data:
        hit_rate = data[method]['hit_rate']
        success = data[method]['success_rate'] * 100
        avg_time = data[method]['average_completion']
        print(f"{method:<25} {hit_rate:>10.2f}%  {success:>10.2f}%  {avg_time:>10.2f} ms")

print("\n" + "="*70)
print("KEY FINDINGS:")
print("="*70)

if 'FL+RL (Proposed)' in data and 'FL+LFU' in data:
    fl_rl_rate = data['FL+RL (Proposed)']['hit_rate']
    fl_lfu_rate = data['FL+LFU']['hit_rate']
    improvement = fl_rl_rate - fl_lfu_rate
    print(f"✓ FL+RL vs FL+LFU: +{improvement:.2f} percentage points")

if 'FL+LFU' in data and 'LFU (No FL)' in data:
    fl_rate = data['FL+LFU']['hit_rate']
    no_fl_rate = data['LFU (No FL)']['hit_rate']
    diff = fl_rate - no_fl_rate
    print(f"✓ FL+LFU vs LFU (No FL): {diff:+.2f} percentage points")

print("\n✓ All plots saved to experiments/results/plots/")
