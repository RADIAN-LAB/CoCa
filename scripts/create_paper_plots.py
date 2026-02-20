#!/usr/bin/env python3
"""
Create clean, publication-ready plots for paper submission.
Each plot is saved separately for easy inclusion in papers.
"""

import json
import matplotlib.pyplot as plt
import numpy as np
import seaborn as sns

# Set publication style - clean without titles
plt.style.use('seaborn-v0_8-paper')
plt.rcParams['figure.dpi'] = 100
plt.rcParams['font.size'] = 16
plt.rcParams['font.weight'] = 'bold'
plt.rcParams['font.family'] = 'sans-serif'
plt.rcParams['axes.labelsize'] = 18
plt.rcParams['axes.labelweight'] = 'bold'
plt.rcParams['axes.titlesize'] = 0  # No titles
plt.rcParams['xtick.labelsize'] = 14
plt.rcParams['ytick.labelsize'] = 14
plt.rcParams['legend.fontsize'] = 14

# Load data from JSON files
data_files = [
    ('No Cache', '1_no_cache_results.json'),
    ('Random', '2_random_results.json'),
    ('LRU', '3_lru_results.json'),
    ('LFU', '4_lfu_results.json'),
    ('FL-only', '5_fl_only_results.json'),
    ('CoCa', '6_fl_rl_results.json')
]

methods_data = []
for name, filename in data_files:
    with open(f'experiments/comparison/{filename}') as f:
        result = json.load(f)
    
    # Calculate metrics
    success_rate = result['success_rate'] * 100
    hits = result['cache_hits']
    total = result['total_tasks']
    hit_rate = 100 * hits / total
    avg_time = result['average_completion']  # keep in seconds
    
    # Calculate energy
    misses = result['cache_misses']
    energy_hits = hits * 0.1
    successful_misses = misses * result['success_rate']
    energy_successful_misses = successful_misses * 2.0
    failed_tasks = total * (1 - result['success_rate'])
    energy_failures = failed_tasks * 1.5
    total_energy = energy_hits + energy_successful_misses + energy_failures
    
    methods_data.append({
        'name': name,
        'success_rate': success_rate,
        'hit_rate': hit_rate,
        'avg_completion_time': avg_time,
        'energy_consumption': total_energy
    })

# Define colors - professional palette
colors = {
    'No Cache': '#7f8c8d',
    'Random': '#e74c3c',
    'LRU': '#3498db',
    'LFU': '#9b59b6',
    'FL-only': '#f39c12',
    'CoCa': '#27ae60'
}

methods = [m['name'] for m in methods_data]
fl_rl_idx = methods.index('CoCa')

# ============================================================================
# PLOT 1: Bar Chart - All 4 Metrics in One Figure (2x2 grid)
# ============================================================================
fig1, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(14, 10))

# Success Rate
success_rates = [m['success_rate'] for m in methods_data]
bars1 = ax1.bar(range(len(methods)), success_rates, 
                color=[colors[m] for m in methods],
                edgecolor='black', linewidth=1.5, alpha=0.85)
bars1[fl_rl_idx].set_edgecolor('#155724')
bars1[fl_rl_idx].set_linewidth(3)
ax1.set_ylabel('Success Rate (%)', fontweight='bold', fontsize=18)
ax1.set_xticks(range(len(methods)))
ax1.set_xticklabels(methods, rotation=30, ha='right', fontweight='bold')
ax1.grid(True, which='both', linestyle='--', linewidth=0.5, alpha=0.7)
ax1.set_ylim([70, 95])
for i, (bar, val) in enumerate(zip(bars1, success_rates)):
    ax1.text(bar.get_x() + bar.get_width()/2., bar.get_height() + 0.8,
             f'{val:.1f}', ha='center', va='bottom', fontsize=11,
             fontweight='bold' if i == fl_rl_idx else 'normal')

# Hit Rate
hit_rates = [m['hit_rate'] for m in methods_data]
bars2 = ax2.bar(range(len(methods)), hit_rates,
                color=[colors[m] for m in methods],
                edgecolor='black', linewidth=1.5, alpha=0.85)
bars2[fl_rl_idx].set_edgecolor('#155724')
bars2[fl_rl_idx].set_linewidth(3)
ax2.set_ylabel('Cache Hit Rate (%)', fontweight='bold', fontsize=18)
ax2.set_xticks(range(len(methods)))
ax2.set_xticklabels(methods, rotation=30, ha='right', fontweight='bold')
ax2.grid(True, which='both', linestyle='--', linewidth=0.5, alpha=0.7)
ax2.set_ylim([80, 100])
for i, (bar, val) in enumerate(zip(bars2, hit_rates)):
    ax2.text(bar.get_x() + bar.get_width()/2., bar.get_height() + 0.5,
             f'{val:.1f}', ha='center', va='bottom', fontsize=11,
             fontweight='bold' if i == fl_rl_idx else 'normal')

# Completion Time
completion_times = [m['avg_completion_time'] for m in methods_data]
bars3 = ax3.bar(range(len(methods)), completion_times,
                color=[colors[m] for m in methods],
                edgecolor='black', linewidth=1.5, alpha=0.85)
bars3[fl_rl_idx].set_edgecolor('#155724')
bars3[fl_rl_idx].set_linewidth(3)
ax3.set_ylabel('Avg. Completion Time (s)', fontweight='bold', fontsize=18)
ax3.set_xticks(range(len(methods)))
ax3.set_xticklabels(methods, rotation=30, ha='right', fontweight='bold')
ax3.grid(True, which='both', linestyle='--', linewidth=0.5, alpha=0.7)
for i, (bar, val) in enumerate(zip(bars3, completion_times)):
    ax3.text(bar.get_x() + bar.get_width()/2., bar.get_height() + 0.15,
             f'{val:.2f}', ha='center', va='bottom', fontsize=11,
             fontweight='bold' if i == fl_rl_idx else 'normal')

# Energy Consumption
energy = [m['energy_consumption'] for m in methods_data]
bars4 = ax4.bar(range(len(methods)), energy,
                color=[colors[m] for m in methods],
                edgecolor='black', linewidth=1.5, alpha=0.85)
bars4[fl_rl_idx].set_edgecolor('#155724')
bars4[fl_rl_idx].set_linewidth(3)
ax4.set_ylabel('Energy Consumption (J)', fontweight='bold', fontsize=18)
ax4.set_xticks(range(len(methods)))
ax4.set_xticklabels(methods, rotation=30, ha='right', fontweight='bold')
ax4.grid(True, which='both', linestyle='--', linewidth=0.5, alpha=0.7)
for i, (bar, val) in enumerate(zip(bars4, energy)):
    ax4.text(bar.get_x() + bar.get_width()/2., bar.get_height() + 20,
             f'{val:.0f}', ha='center', va='bottom', fontsize=11,
             fontweight='bold' if i == fl_rl_idx else 'normal')

plt.tight_layout()
plt.savefig('experiments/comparison/fig_performance_comparison.pdf', bbox_inches='tight')
print("✓ Figure 1: Performance comparison (4 metrics)")
plt.close()

# ============================================================================
# SEPARATE PLOTS - Each Metric in Individual File
# ============================================================================

# Plot 1a: Success Rate Only
fig, ax = plt.subplots(figsize=(10, 6))
bars = ax.bar(range(len(methods)), success_rates, 
              color=[colors[m] for m in methods],
              edgecolor='black', linewidth=1.5, alpha=0.85)
bars[fl_rl_idx].set_edgecolor('#155724')
bars[fl_rl_idx].set_linewidth(3)
ax.set_ylabel('Success Rate (%)', fontweight='bold', fontsize=18)
ax.set_xticks(range(len(methods)))
ax.set_xticklabels(methods, rotation=30, ha='right', fontweight='bold')
ax.grid(True, which='both', linestyle='--', linewidth=0.5, alpha=0.7)
ax.set_ylim([70, 95])
for i, (bar, val) in enumerate(zip(bars, success_rates)):
    ax.text(bar.get_x() + bar.get_width()/2., bar.get_height() + 0.8,
             f'{val:.1f}', ha='center', va='bottom', fontsize=11,
             fontweight='bold' if i == fl_rl_idx else 'normal')
plt.tight_layout()
plt.savefig('experiments/comparison/fig_success_rate.pdf', bbox_inches='tight')
print("✓ Figure 1a: Success rate")
plt.close()

# Plot 1b: Hit Rate Only
fig, ax = plt.subplots(figsize=(10, 6))
bars = ax.bar(range(len(methods)), hit_rates,
              color=[colors[m] for m in methods],
              edgecolor='black', linewidth=1.5, alpha=0.85)
bars[fl_rl_idx].set_edgecolor('#155724')
bars[fl_rl_idx].set_linewidth(3)
ax.set_ylabel('Cache Hit Rate (%)', fontweight='bold', fontsize=18)
ax.set_xticks(range(len(methods)))
ax.set_xticklabels(methods, rotation=30, ha='right', fontweight='bold')
ax.grid(True, which='both', linestyle='--', linewidth=0.5, alpha=0.7)
ax.set_ylim([80, 100])
for i, (bar, val) in enumerate(zip(bars, hit_rates)):
    ax.text(bar.get_x() + bar.get_width()/2., bar.get_height() + 0.5,
             f'{val:.1f}', ha='center', va='bottom', fontsize=11,
             fontweight='bold' if i == fl_rl_idx else 'normal')
plt.tight_layout()
plt.savefig('experiments/comparison/fig_hit_rate.pdf', bbox_inches='tight')
print("✓ Figure 1b: Hit rate")
plt.close()

# Plot 1c: Completion Time Only
fig, ax = plt.subplots(figsize=(10, 6))
bars = ax.bar(range(len(methods)), completion_times,
              color=[colors[m] for m in methods],
              edgecolor='black', linewidth=1.5, alpha=0.85)
bars[fl_rl_idx].set_edgecolor('#155724')
bars[fl_rl_idx].set_linewidth(3)
ax.set_ylabel('Avg. Completion Time (s)', fontweight='bold', fontsize=18)
ax.set_xticks(range(len(methods)))
ax.set_xticklabels(methods, rotation=30, ha='right', fontweight='bold')
ax.grid(True, which='both', linestyle='--', linewidth=0.5, alpha=0.7)
for i, (bar, val) in enumerate(zip(bars, completion_times)):
    ax.text(bar.get_x() + bar.get_width()/2., bar.get_height() + 0.15,
             f'{val:.2f}', ha='center', va='bottom', fontsize=11,
             fontweight='bold' if i == fl_rl_idx else 'normal')
plt.tight_layout()
plt.savefig('experiments/comparison/fig_completion_time.pdf', bbox_inches='tight')
print("✓ Figure 1c: Completion time")
plt.close()

# Plot 1d: Energy Only
fig, ax = plt.subplots(figsize=(10, 6))
bars = ax.bar(range(len(methods)), energy,
              color=[colors[m] for m in methods],
              edgecolor='black', linewidth=1.5, alpha=0.85)
bars[fl_rl_idx].set_edgecolor('#155724')
bars[fl_rl_idx].set_linewidth(3)
ax.set_ylabel('Energy Consumption (J)', fontweight='bold', fontsize=18)
ax.set_xticks(range(len(methods)))
ax.set_xticklabels(methods, rotation=30, ha='right', fontweight='bold')
ax.grid(True, which='both', linestyle='--', linewidth=0.5, alpha=0.7)
for i, (bar, val) in enumerate(zip(bars, energy)):
    ax.text(bar.get_x() + bar.get_width()/2., bar.get_height() + 20,
             f'{val:.0f}', ha='center', va='bottom', fontsize=11,
             fontweight='bold' if i == fl_rl_idx else 'normal')
plt.tight_layout()
plt.savefig('experiments/comparison/fig_energy.pdf', bbox_inches='tight')
print("✓ Figure 1d: Energy consumption")
plt.close()

# ============================================================================
# PLOT 2: Radar Chart - FL+RL vs Baselines
# ============================================================================
fig2, ax = plt.subplots(figsize=(10, 10), subplot_kw=dict(projection='polar'))

metrics_labels = ['Success\nRate', 'Hit\nRate', 'Response\nSpeed', 'Energy\nEfficiency']
angles = np.linspace(0, 2 * np.pi, len(metrics_labels), endpoint=False).tolist()
angles += angles[:1]

# Compare CoCa with all methods including No Cache
compare_methods = ['No Cache', 'Random', 'LRU', 'LFU', 'FL-only', 'CoCa']
compare_data = [m for m in methods_data if m['name'] in compare_methods]

for method_dict in compare_data:
    method = method_dict['name']
    
    # Normalize metrics (0-100, higher is better)
    values = [
        method_dict['success_rate'],
        method_dict['hit_rate'],
        100 * (5500 - method_dict['avg_completion_time']) / (5500 - 2500),
        100 * (1100 - method_dict['energy_consumption']) / (1100 - 400)
    ]
    values = [max(0, min(100, v)) for v in values]
    values += values[:1]
    
    linewidth = 4 if method == 'CoCa' else 2.5
    alpha = 1.0 if method == 'CoCa' else 0.8
    markersize = 10 if method == 'CoCa' else 7
    
    ax.plot(angles, values, 'o-', linewidth=linewidth, 
            label=method, color=colors[method], alpha=alpha,
            markersize=markersize, zorder=10 if method == 'CoCa' else 5)
    
    fill_alpha = 0.25 if method == 'CoCa' else 0.15
    ax.fill(angles, values, alpha=fill_alpha, color=colors[method])

ax.set_xticks(angles[:-1])
ax.set_xticklabels(metrics_labels, fontsize=15)
ax.set_ylim(0, 100)
ax.set_yticks([20, 40, 60, 80, 100])
ax.set_yticklabels(['20', '40', '60', '80', '100'], fontsize=12, fontweight='bold')
ax.grid(True, linestyle='--', alpha=0.4, linewidth=1.5)
legend = ax.legend(loc='upper right', bbox_to_anchor=(1.3, 1.15), 
                   frameon=True, fancybox=True, shadow=True, fontsize=15)
legend.get_frame().set_alpha(0.95)

plt.tight_layout()
plt.savefig('experiments/comparison/fig_radar_comparison.pdf', bbox_inches='tight')
print("✓ Figure 2: Radar chart comparison")
plt.close()

# ============================================================================
# PLOT 3: Improvement Bar Chart (Horizontal)
# ============================================================================
fig3, ax = plt.subplots(figsize=(10, 6))

fl_rl_data = next(m for m in methods_data if m['name'] == 'CoCa')
baselines = [m for m in methods_data if m['name'] != 'CoCa']

best_sr = max(m['success_rate'] for m in baselines)
best_hit = max(m['hit_rate'] for m in baselines)
best_time = min(m['avg_completion_time'] for m in baselines)
best_energy = min(m['energy_consumption'] for m in baselines)

improvements = {
    'Success Rate': fl_rl_data['success_rate'] - best_sr,
    'Hit Rate': fl_rl_data['hit_rate'] - best_hit,
    'Speed\n(Time Reduction)': 100 * (best_time - fl_rl_data['avg_completion_time']) / best_time,
    'Energy\nEfficiency': 100 * (best_energy - fl_rl_data['energy_consumption']) / best_energy
}

metrics = list(improvements.keys())
values = list(improvements.values())

bars = ax.barh(metrics, values, color='#27ae60', edgecolor='#155724', 
               linewidth=2.5, alpha=0.85, height=0.6)

ax.set_xlabel('Improvement over Best Baseline (%)', fontweight='bold', fontsize=18)
ax.grid(True, which='both', linestyle='--', linewidth=0.5, alpha=0.7)
ax.axvline(x=0, color='black', linewidth=2)

# Add value labels
for bar, val in zip(bars, values):
    width = bar.get_width()
    ax.text(width + 1.5, bar.get_y() + bar.get_height()/2,
            f'+{val:.1f}%', ha='left', va='center', 
            fontweight='bold', fontsize=14, color='#155724')

plt.tight_layout()
plt.savefig('experiments/comparison/fig_improvements.pdf', bbox_inches='tight')
print("✓ Figure 3: Performance improvements")
plt.close()

# ============================================================================
# PLOT 4: Combined Success Rate & Hit Rate (Side by Side)
# ============================================================================
fig4, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 6))

# Success Rate
bars1 = ax1.bar(range(len(methods)), success_rates, 
                color=[colors[m] for m in methods],
                edgecolor='black', linewidth=1.5, alpha=0.85)
bars1[fl_rl_idx].set_edgecolor('#155724')
bars1[fl_rl_idx].set_linewidth(3)
ax1.set_ylabel('Success Rate (%)', fontweight='bold', fontsize=18)
ax1.set_xticks(range(len(methods)))
ax1.set_xticklabels(methods, rotation=30, ha='right', fontsize=14, fontweight='bold')
ax1.grid(True, which='both', linestyle='--', linewidth=0.5, alpha=0.7)
ax1.set_ylim([70, 95])
for i, (bar, val) in enumerate(zip(bars1, success_rates)):
    ax1.text(bar.get_x() + bar.get_width()/2., bar.get_height() + 0.8,
             f'{val:.1f}%', ha='center', va='bottom', fontsize=12,
             fontweight='bold' if i == fl_rl_idx else 'normal')

# Hit Rate
bars2 = ax2.bar(range(len(methods)), hit_rates,
                color=[colors[m] for m in methods],
                edgecolor='black', linewidth=1.5, alpha=0.85)
bars2[fl_rl_idx].set_edgecolor('#155724')
bars2[fl_rl_idx].set_linewidth(3)
ax2.set_ylabel('Cache Hit Rate (%)', fontweight='bold', fontsize=18)
ax2.set_xticks(range(len(methods)))
ax2.set_xticklabels(methods, rotation=30, ha='right', fontsize=14, fontweight='bold')
ax2.grid(True, which='both', linestyle='--', linewidth=0.5, alpha=0.7)
ax2.set_ylim([80, 100])
for i, (bar, val) in enumerate(zip(bars2, hit_rates)):
    ax2.text(bar.get_x() + bar.get_width()/2., bar.get_height() + 0.5,
             f'{val:.1f}%', ha='center', va='bottom', fontsize=12,
             fontweight='bold' if i == fl_rl_idx else 'normal')

plt.tight_layout()
plt.savefig('experiments/comparison/fig_success_hitrate.pdf', bbox_inches='tight')
print("✓ Figure 4: Success rate & hit rate comparison")
plt.close()

# ============================================================================
# PLOT 5: Combined Time & Energy (Side by Side)
# ============================================================================
fig5, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 6))

# Completion Time
bars1 = ax1.bar(range(len(methods)), completion_times,
                color=[colors[m] for m in methods],
                edgecolor='black', linewidth=1.5, alpha=0.85)
bars1[fl_rl_idx].set_edgecolor('#155724')
bars1[fl_rl_idx].set_linewidth(3)
ax1.set_ylabel('Avg. Completion Time (s)', fontweight='bold', fontsize=18)
ax1.set_xticks(range(len(methods)))
ax1.set_xticklabels(methods, rotation=30, ha='right', fontsize=14, fontweight='bold')
ax1.grid(True, which='both', linestyle='--', linewidth=0.5, alpha=0.7)
for i, (bar, val) in enumerate(zip(bars1, completion_times)):
    ax1.text(bar.get_x() + bar.get_width()/2., bar.get_height() + 0.15,
             f'{val:.2f}', ha='center', va='bottom', fontsize=12,
             fontweight='bold' if i == fl_rl_idx else 'normal')

# Energy
bars2 = ax2.bar(range(len(methods)), energy,
                color=[colors[m] for m in methods],
                edgecolor='black', linewidth=1.5, alpha=0.85)
bars2[fl_rl_idx].set_edgecolor('#155724')
bars2[fl_rl_idx].set_linewidth(3)
ax2.set_ylabel('Energy Consumption (J)', fontweight='bold', fontsize=18)
ax2.set_xticks(range(len(methods)))
ax2.set_xticklabels(methods, rotation=30, ha='right', fontsize=14, fontweight='bold')
ax2.grid(True, which='both', linestyle='--', linewidth=0.5, alpha=0.7)
for i, (bar, val) in enumerate(zip(bars2, energy)):
    ax2.text(bar.get_x() + bar.get_width()/2., bar.get_height() + 20,
             f'{val:.0f}', ha='center', va='bottom', fontsize=12,
             fontweight='bold' if i == fl_rl_idx else 'normal')

plt.tight_layout()
plt.savefig('experiments/comparison/fig_time_energy.pdf', bbox_inches='tight')
print("✓ Figure 5: Time & energy comparison")
plt.close()

print("\n" + "="*80)
print("ALL PAPER-READY FIGURES CREATED!")
print("="*80)
print("\nGenerated figures:")
print("  1. fig_performance_comparison.* - All 4 metrics (2x2 grid)")
print("  2. fig_radar_comparison.* - Radar chart (CoCa vs baselines)")
print("  3. fig_improvements.* - Performance gains bar chart")
print("  4. fig_success_hitrate.* - Success & hit rate (side by side)")
print("  5. fig_time_energy.* - Time & energy (side by side)")
print("\nAll figures saved as PDF (vector format)")
print("="*80)
