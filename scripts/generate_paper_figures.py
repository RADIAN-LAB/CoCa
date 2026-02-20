#!/usr/bin/env python3
"""
Generate publication-quality figures for the Performance Evaluation section.
Figures match the LaTeX \includegraphics references.
"""

import json
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.ticker import MultipleLocator
import numpy as np
from pathlib import Path

# ── Load results ───────────────────────────────────────────────────────
results_dir = Path('experiments/sumo/output')
output_dir = Path('experiments/sumo/paper_figures')
output_dir.mkdir(parents=True, exist_ok=True)

files = {
    'No Cache':     '1_no_cache_results.json',
    'Random':       '2_random_results.json',
    'LRU':          '3_lru_results.json',
    'LFU':          '4_lfu_results.json',
    'FL-Only':      '5_fl_only_results.json',
    'CoCa (FL+RL)': '6_fl_rl_results.json',
}

data = {}
for name, fname in files.items():
    with open(results_dir / fname) as f:
        data[name] = json.load(f)

# Compute derived metrics
for name, d in data.items():
    hits, misses = d['cache_hits'], d['cache_misses']
    total = hits + misses
    d['hit_rate'] = (hits / total * 100) if total > 0 else 0.0
    d['success_pct'] = d['success_rate'] * 100
    # Energy model: 0.1J per cache hit, 2.0J per miss computation, 1.5J per failed task
    n_tasks = d['total_tasks']
    n_success = int(d['success_rate'] * n_tasks)
    n_fail = n_tasks - n_success
    energy = hits * 0.1 + misses * 2.0 + n_fail * 1.5
    # No-cache: all tasks computed fresh
    if name == 'No Cache':
        energy = n_success * 2.0 + n_fail * 1.5
    d['energy'] = energy

methods_order = ['No Cache', 'Random', 'LRU', 'LFU', 'FL-Only', 'CoCa (FL+RL)']

# Professional color palette — one distinct color per method
COLORS = {
    'No Cache':     '#8C8C8C',
    'Random':       '#9467BD',
    'LRU':          '#4E79A7',
    'LFU':          '#59A14F',
    'FL-Only':      '#F28E2B',
    'CoCa (FL+RL)': '#E15759',
}
LINE_COLORS = {
    'No Cache':     '#666666',
    'Random':       '#7B4F9E',
    'LRU':          '#2E5984',
    'LFU':          '#3D7A35',
    'FL-Only':      '#C97218',
    'CoCa (FL+RL)': '#B83A3C',
}

def style_ax(ax, fig):
    """Apply the user's preferred styling to an axes."""
    for spine in ax.spines.values():
        spine.set_visible(True)
        spine.set_linewidth(1.5)
        spine.set_color('#333333')
    ax.grid(True, which='both', linestyle='--', linewidth=0.5, color='lightgray')
    ax.set_axisbelow(True)
    ax.set_facecolor('#f8f9fa')
    fig.patch.set_facecolor('white')

# ============================================================================
# Figure 1: Task Success Rate (fig_success_rate.png)
# ============================================================================
fig, ax = plt.subplots(layout='constrained', figsize=(10, 6))

labels = methods_order
vals = [data[m]['success_pct'] for m in labels]
bar_colors = [COLORS[m] for m in labels]
line_colors_list = [LINE_COLORS[m] for m in labels]

x = np.arange(len(labels))
width = 0.5

bars = ax.bar(x, vals, width, color=bar_colors, edgecolor='white', linewidth=1, alpha=0.9)
ax.plot(x, vals, 'o--', color='#2E5984', markersize=8, linewidth=2.5,
        markeredgecolor='white', markeredgewidth=1)

ax.set_ylabel('Task Success Rate (%)', fontsize=14, fontweight='bold')
ax.set_xlabel('Caching Method', fontsize=14, fontweight='bold')
ax.set_xticks(x)
ax.set_xticklabels(labels, fontsize=11, fontweight='bold')
ax.tick_params(axis='y', labelsize=12)
ax.set_ylim(0, 110)
ax.yaxis.set_major_locator(MultipleLocator(20))

style_ax(ax, fig)
plt.tight_layout()
plt.savefig(output_dir / 'fig_success_rate.png', dpi=300, bbox_inches='tight')
plt.savefig(output_dir / 'fig_success_rate.pdf', bbox_inches='tight')
print("✓ fig_success_rate")
plt.close()

# ============================================================================
# Figure 2: Cache Hit Rate (fig_hit_rate.png)
# ============================================================================
fig, ax = plt.subplots(layout='constrained', figsize=(10, 6))

hr_labels = [m for m in methods_order if m != 'No Cache']
hr_vals = [data[m]['hit_rate'] for m in hr_labels]
hr_bar_colors = [COLORS[m] for m in hr_labels]

x = np.arange(len(hr_labels))
width = 0.45

bars = ax.bar(x, hr_vals, width, color=hr_bar_colors, edgecolor='white', linewidth=1, alpha=0.9)
ax.plot(x, hr_vals, 'o--', color='#2E5984', markersize=8, linewidth=2.5,
        markeredgecolor='white', markeredgewidth=1)

ax.set_ylabel('Cache Hit Rate (%)', fontsize=14, fontweight='bold')
ax.set_xlabel('Caching Method', fontsize=14, fontweight='bold')
ax.set_xticks(x)
ax.set_xticklabels(hr_labels, fontsize=11, fontweight='bold')
ax.tick_params(axis='y', labelsize=12)
ax.set_ylim(0, 110)
ax.yaxis.set_major_locator(MultipleLocator(20))

style_ax(ax, fig)
plt.tight_layout()
plt.savefig(output_dir / 'fig_hit_rate.png', dpi=300, bbox_inches='tight')
plt.savefig(output_dir / 'fig_hit_rate.pdf', bbox_inches='tight')
print("✓ fig_hit_rate")
plt.close()

# ============================================================================
# Figure 3: Average Completion Time (fig_completion_time.png)
# ============================================================================
fig, ax = plt.subplots(layout='constrained', figsize=(10, 6))

labels = methods_order
ct_vals = [data[m]['average_completion'] for m in labels]
ct_colors = [COLORS[m] for m in labels]

x = np.arange(len(labels))
width = 0.5

bars = ax.bar(x, ct_vals, width, color=ct_colors, edgecolor='white', linewidth=1, alpha=0.9)
ax.plot(x, ct_vals, 'o--', color='#2E5984', markersize=8, linewidth=2.5,
        markeredgecolor='white', markeredgewidth=1)

# Deadline line
ax.axhline(y=5.0, color='#E15759', linestyle='--', linewidth=2.5, label='Deadline (5 ms)')

ax.set_ylabel('Average Completion Time (ms)', fontsize=14, fontweight='bold')
ax.set_xlabel('Caching Method', fontsize=14, fontweight='bold')
ax.set_xticks(x)
ax.set_xticklabels(labels, fontsize=11, fontweight='bold')
ax.tick_params(axis='y', labelsize=12)
ax.set_ylim(0, 18)
ax.yaxis.set_major_locator(MultipleLocator(2))
ax.legend(loc='upper left', prop={'weight': 'bold', 'size': 12}, framealpha=1)

style_ax(ax, fig)
plt.tight_layout()
plt.savefig(output_dir / 'fig_completion_time.png', dpi=300, bbox_inches='tight')
plt.savefig(output_dir / 'fig_completion_time.pdf', bbox_inches='tight')
print("✓ fig_completion_time")
plt.close()

# ============================================================================
# Figure 4: Energy Consumption (fig_energy.png)
# ============================================================================
fig, ax = plt.subplots(layout='constrained', figsize=(10, 6))

labels = methods_order
energy_vals = [data[m]['energy'] for m in labels]
en_colors = [COLORS[m] for m in labels]

x = np.arange(len(labels))
width = 0.5

bars = ax.bar(x, energy_vals, width, color=en_colors, edgecolor='white', linewidth=1, alpha=0.9)
ax.plot(x, energy_vals, 'o--', color='#2E5984', markersize=8, linewidth=2.5,
        markeredgecolor='white', markeredgewidth=1)

ax.set_ylabel('Energy Consumption (Joules)', fontsize=14, fontweight='bold')
ax.set_xlabel('Caching Method', fontsize=14, fontweight='bold')
ax.set_xticks(x)
ax.set_xticklabels(labels, fontsize=11, fontweight='bold')
ax.tick_params(axis='y', labelsize=12)
ax.set_ylim(0, 32000)
ax.yaxis.set_major_locator(MultipleLocator(5000))
ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda v, loc: "{:,.0f}".format(v)))

style_ax(ax, fig)
plt.tight_layout()
plt.savefig(output_dir / 'fig_energy.png', dpi=300, bbox_inches='tight')
plt.savefig(output_dir / 'fig_energy.pdf', bbox_inches='tight')
print("✓ fig_energy")
plt.close()

# ============================================================================
# Figure 5: Radar Chart (fig_radar_comparison.png)
# ============================================================================
fig, ax = plt.subplots(figsize=(8, 8), subplot_kw=dict(polar=True))
fig.patch.set_facecolor('white')

categories = ['Success\nRate', 'Hit\nRate', 'Response\nSpeed', 'Energy\nEfficiency']
N = len(categories)

max_time = data['No Cache']['average_completion']
max_energy = max(data[m]['energy'] for m in methods_order)

def normalize(m):
    return [
        data[m]['success_pct'],
        data[m]['hit_rate'],
        (1 - data[m]['average_completion'] / max_time) * 100,
        (1 - data[m]['energy'] / max_energy) * 100,
    ]

plot_methods = ['CoCa (FL+RL)', 'FL-Only', 'LRU', 'Random', 'No Cache']
plot_c = [COLORS[m] for m in plot_methods]
plot_widths = [3.0, 2.0, 2.0, 1.5, 1.5]
plot_markers = ['D', 's', 'o', '^', 'v']

angles = [n / float(N) * 2 * np.pi for n in range(N)]
angles += angles[:1]

for m, c, lw, mk in zip(plot_methods, plot_c, plot_widths, plot_markers):
    vals = normalize(m)
    vals += vals[:1]
    ax.plot(angles, vals, marker=mk, linewidth=lw, color=c, label=m, markersize=7,
            markeredgecolor='white', markeredgewidth=1)
    if m == 'CoCa (FL+RL)':
        ax.fill(angles, vals, alpha=0.12, color=c)

ax.set_xticks(angles[:-1])
ax.set_xticklabels(categories, fontsize=13, fontweight='bold')
ax.set_ylim(0, 105)
ax.set_title('Multi-Metric Radar Comparison', fontsize=16, fontweight='bold', pad=30)
ax.legend(loc='lower right', bbox_to_anchor=(1.35, -0.05),
          prop={'weight': 'bold', 'size': 11}, framealpha=1, edgecolor='#cccccc')

plt.tight_layout()
plt.savefig(output_dir / 'fig_radar_comparison.png', dpi=300, bbox_inches='tight')
plt.savefig(output_dir / 'fig_radar_comparison.pdf', bbox_inches='tight')
print("✓ fig_radar_comparison")
plt.close()

# ============================================================================
# Figure 6: Improvements Bar Chart (fig_improvements.png)
# ============================================================================
fig, ax = plt.subplots(layout='constrained', figsize=(10, 6))

coca = data['CoCa (FL+RL)']
best_sr = max(data[m]['success_pct'] for m in methods_order if m != 'CoCa (FL+RL)')
best_hr = max(data[m]['hit_rate'] for m in methods_order if m != 'CoCa (FL+RL)')
best_ct = min(data[m]['average_completion'] for m in methods_order if m != 'CoCa (FL+RL)')
best_en = min(data[m]['energy'] for m in methods_order if m != 'CoCa (FL+RL)')

imp_labels = ['Success Rate\n(+pp)', 'Hit Rate\n(+pp)',
              'Completion Time\nReduction (%)', 'Energy\nReduction (%)']
imp_vals = [
    coca['success_pct'] - best_sr,
    coca['hit_rate'] - best_hr,
    (1 - coca['average_completion'] / best_ct) * 100,
    (1 - coca['energy'] / best_en) * 100,
]
imp_colors = ['#E15759', '#4E79A7', '#F28E2B', '#59A14F']

x = np.arange(len(imp_labels))
width = 0.45

bars = ax.bar(x, imp_vals, width, color=imp_colors, edgecolor='white', linewidth=1, alpha=0.9)
ax.plot(x, imp_vals, 'o--', color='#2E5984', markersize=8, linewidth=2.5,
        markeredgecolor='white', markeredgewidth=1)

for bar, v in zip(bars, imp_vals):
    label = f'+{v:.1f}' if v < 20 else f'{v:.1f}%'
    ax.text(bar.get_x() + bar.get_width()/2., bar.get_height() + 0.8,
            label, ha='center', va='bottom', fontweight='bold', fontsize=13)

ax.set_ylabel('Improvement', fontsize=14, fontweight='bold')
ax.set_xlabel('Metric', fontsize=14, fontweight='bold')
ax.set_xticks(x)
ax.set_xticklabels(imp_labels, fontsize=11, fontweight='bold')
ax.tick_params(axis='y', labelsize=12)
ax.set_ylim(0, max(imp_vals) * 1.25)
ax.yaxis.set_major_locator(MultipleLocator(10))

style_ax(ax, fig)
plt.tight_layout()
plt.savefig(output_dir / 'fig_improvements.png', dpi=300, bbox_inches='tight')
plt.savefig(output_dir / 'fig_improvements.pdf', bbox_inches='tight')
print("✓ fig_improvements")
plt.close()

# ============================================================================
# Print summary for LaTeX number updates
# ============================================================================
print("\n" + "="*70)
print("NUMBERS FOR LATEX UPDATE")
print("="*70)
for m in methods_order:
    d = data[m]
    print(f"{m:20s}  SR={d['success_pct']:.2f}%  HR={d['hit_rate']:.2f}%  "
          f"CT={d['average_completion']:.3f}ms  E={d['energy']:.2f}J  "
          f"hits={d['cache_hits']}  misses={d['cache_misses']}")

# Improvement calculations
print(f"\nCoCa vs FL-Only:  SR +{coca['success_pct'] - data['FL-Only']['success_pct']:.2f}pp  "
      f"HR +{coca['hit_rate'] - data['FL-Only']['hit_rate']:.2f}pp  "
      f"CT -{(1 - coca['average_completion']/data['FL-Only']['average_completion'])*100:.1f}%  "
      f"E -{(1 - coca['energy']/data['FL-Only']['energy'])*100:.1f}%")
print(f"CoCa vs LRU:      SR +{coca['success_pct'] - data['LRU']['success_pct']:.2f}pp  "
      f"HR +{coca['hit_rate'] - data['LRU']['hit_rate']:.2f}pp  "
      f"CT -{(1 - coca['average_completion']/data['LRU']['average_completion'])*100:.1f}%  "
      f"E -{(1 - coca['energy']/data['LRU']['energy'])*100:.1f}%")
print(f"CoCa vs LFU:      SR +{coca['success_pct'] - data['LFU']['success_pct']:.2f}pp  "
      f"HR +{coca['hit_rate'] - data['LFU']['hit_rate']:.2f}pp  "
      f"CT -{(1 - coca['average_completion']/data['LFU']['average_completion'])*100:.1f}%  "
      f"E -{(1 - coca['energy']/data['LFU']['energy'])*100:.1f}%")
print(f"CoCa vs Random:   SR +{coca['success_pct'] - data['Random']['success_pct']:.2f}pp  "
      f"HR +{coca['hit_rate'] - data['Random']['hit_rate']:.2f}pp  "
      f"CT -{(1 - coca['average_completion']/data['Random']['average_completion'])*100:.1f}%  "
      f"E -{(1 - coca['energy']/data['Random']['energy'])*100:.1f}%")
print(f"CoCa vs No Cache: SR +{coca['success_pct'] - data['No Cache']['success_pct']:.2f}pp  "
      f"CT -{(1 - coca['average_completion']/data['No Cache']['average_completion'])*100:.1f}%  "
      f"E -{(1 - coca['energy']/data['No Cache']['energy'])*100:.1f}%")

print(f"\n✓ All figures saved to {output_dir}/")
