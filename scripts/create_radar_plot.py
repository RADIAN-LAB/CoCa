#!/usr/bin/env python3
"""
Create standalone radar chart for FL+RL VANET caching comparison.
"""

import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import seaborn as sns

# Set publication style
plt.style.use('seaborn-v0_8-paper')
sns.set_palette("husl")
plt.rcParams['figure.dpi'] = 100
plt.rcParams['font.size'] = 12
plt.rcParams['font.family'] = 'serif'
plt.rcParams['axes.labelsize'] = 13
plt.rcParams['axes.titlesize'] = 14
plt.rcParams['xtick.labelsize'] = 11
plt.rcParams['ytick.labelsize'] = 10
plt.rcParams['legend.fontsize'] = 11

# Load data
df = pd.read_csv('experiments/comparison/comparison_table.csv', index_col=0)

# Rename for better display
method_names = {
    'No Cache': 'No Cache',
    'Random Eviction': 'Random',
    'LRU': 'LRU',
    'LFU': 'LFU',
    'FL-based Cache': 'FL-only',
    'FL+RL (Ours)': 'FL+RL (Proposed)'
}
df['display_name'] = df['name'].map(method_names)

# Define colors
colors = {
    'No Cache': '#95a5a6',
    'Random': '#e74c3c',
    'LRU': '#3498db',
    'LFU': '#9b59b6',
    'FL-only': '#f39c12',
    'FL+RL (Proposed)': '#27ae60'
}

# Create radar chart
fig, ax = plt.subplots(figsize=(10, 10), subplot_kw=dict(projection='polar'))

# Define metrics
metrics = ['Success\nRate', 'Hit\nRate', 'Speed\n(inverse)', 'Energy\nEfficiency']
num_vars = len(metrics)
angles = np.linspace(0, 2 * np.pi, num_vars, endpoint=False).tolist()
angles += angles[:1]  # Complete the circle

# Select methods to compare
compare_methods = ['LRU', 'LFU', 'Random', 'FL-only', 'FL+RL (Proposed)']
compare_df = df[df['display_name'].isin(compare_methods)]

# Plot each method
for idx, row in compare_df.iterrows():
    method = row['display_name']
    
    # Normalize metrics (0-100 scale, higher is better for all)
    # Success rate: already 0-100
    success_norm = row['success_rate'] * 100
    
    # Hit rate: already 0-100
    hit_norm = row['cache_hit_rate'] * 100
    
    # Speed: invert and normalize (lower time is better)
    # Map 3000-5000ms to 100-0
    max_time = 5500
    min_time = 2500
    speed_norm = 100 * (max_time - row['avg_completion_time']) / (max_time - min_time)
    speed_norm = max(0, min(100, speed_norm))
    
    # Energy: invert and normalize (lower energy is better)
    # Map 400-1000J to 100-0
    max_energy = 1100
    min_energy = 400
    energy_norm = 100 * (max_energy - row['energy_consumption']) / (max_energy - min_energy)
    energy_norm = max(0, min(100, energy_norm))
    
    values = [success_norm, hit_norm, speed_norm, energy_norm]
    values += values[:1]  # Complete the circle
    
    # Set line properties
    linewidth = 3.5 if method == 'FL+RL (Proposed)' else 2
    alpha = 1.0 if method == 'FL+RL (Proposed)' else 0.7
    zorder = 10 if method == 'FL+RL (Proposed)' else 5
    
    # Plot line
    ax.plot(angles, values, 'o-', linewidth=linewidth, 
            label=method, color=colors[method], alpha=alpha, 
            markersize=8 if method == 'FL+RL (Proposed)' else 6,
            zorder=zorder)
    
    # Fill area
    fill_alpha = 0.25 if method == 'FL+RL (Proposed)' else 0.15
    ax.fill(angles, values, alpha=fill_alpha, color=colors[method], zorder=zorder-1)

# Customize the plot
ax.set_xticks(angles[:-1])
ax.set_xticklabels(metrics, fontsize=12, fontweight='bold')
ax.set_ylim(0, 100)
ax.set_yticks([20, 40, 60, 80, 100])
ax.set_yticklabels(['20', '40', '60', '80', '100'], fontsize=10, color='gray')
ax.grid(True, linestyle='--', alpha=0.4, linewidth=1)

# Add title
ax.set_title('Multi-Metric Performance Comparison\nFL+RL vs Traditional Caching Policies', 
             fontsize=16, fontweight='bold', pad=30, y=1.1)

# Add legend
legend = ax.legend(loc='upper right', bbox_to_anchor=(1.35, 1.15), 
                   frameon=True, fancybox=True, shadow=True,
                   fontsize=11, title='Caching Method', title_fontsize=12)
legend.get_frame().set_alpha(0.95)

# Add note about normalization
note_text = 'Note: All metrics normalized to 0-100 scale (higher is better)\n' + \
            'Speed = inverse of completion time, Energy Efficiency = inverse of consumption'
fig.text(0.5, 0.02, note_text, ha='center', fontsize=9, 
         style='italic', color='gray', wrap=True)

# Save figure
plt.tight_layout()
plt.savefig('experiments/comparison/radar_plot.png', 
            dpi=150, facecolor='white', bbox_inches='tight')
plt.savefig('experiments/comparison/radar_plot.pdf', 
            facecolor='white', bbox_inches='tight')

print("✓ Radar plot saved:")
print("  - experiments/comparison/radar_plot.png")
print("  - experiments/comparison/radar_plot.pdf")

# Create a second version with only FL+RL vs best baseline
fig2, ax2 = plt.subplots(figsize=(9, 9), subplot_kw=dict(projection='polar'))

# Compare FL+RL with LRU (common baseline)
compare_methods_simple = ['LRU', 'FL+RL (Proposed)']
compare_df_simple = df[df['display_name'].isin(compare_methods_simple)]

for idx, row in compare_df_simple.iterrows():
    method = row['display_name']
    
    # Same normalization as before
    success_norm = row['success_rate'] * 100
    hit_norm = row['cache_hit_rate'] * 100
    
    max_time = 5500
    min_time = 2500
    speed_norm = 100 * (max_time - row['avg_completion_time']) / (max_time - min_time)
    speed_norm = max(0, min(100, speed_norm))
    
    max_energy = 1100
    min_energy = 400
    energy_norm = 100 * (max_energy - row['energy_consumption']) / (max_energy - min_energy)
    energy_norm = max(0, min(100, energy_norm))
    
    values = [success_norm, hit_norm, speed_norm, energy_norm]
    values += values[:1]
    
    linewidth = 4 if method == 'FL+RL (Proposed)' else 3
    alpha = 1.0
    
    ax2.plot(angles, values, 'o-', linewidth=linewidth, 
            label=method, color=colors[method], alpha=alpha, 
            markersize=10, zorder=10)
    
    fill_alpha = 0.3 if method == 'FL+RL (Proposed)' else 0.2
    ax2.fill(angles, values, alpha=fill_alpha, color=colors[method])

ax2.set_xticks(angles[:-1])
ax2.set_xticklabels(metrics, fontsize=13, fontweight='bold')
ax2.set_ylim(0, 100)
ax2.set_yticks([20, 40, 60, 80, 100])
ax2.set_yticklabels(['20', '40', '60', '80', '100'], fontsize=11, color='gray')
ax2.grid(True, linestyle='--', alpha=0.4, linewidth=1.2)

ax2.set_title('FL+RL vs LRU Baseline\nPerformance Comparison', 
             fontsize=16, fontweight='bold', pad=30, y=1.1)

legend2 = ax2.legend(loc='upper right', bbox_to_anchor=(1.3, 1.15), 
                    frameon=True, fancybox=True, shadow=True,
                    fontsize=12, title='Method', title_fontsize=13)
legend2.get_frame().set_alpha(0.95)

fig2.text(0.5, 0.02, note_text, ha='center', fontsize=9, 
         style='italic', color='gray', wrap=True)

plt.tight_layout()
plt.savefig('experiments/comparison/radar_plot_simple.png', 
            dpi=150, facecolor='white', bbox_inches='tight')
plt.savefig('experiments/comparison/radar_plot_simple.pdf', 
            facecolor='white', bbox_inches='tight')

print("✓ Simple radar plot saved:")
print("  - experiments/comparison/radar_plot_simple.png")
print("  - experiments/comparison/radar_plot_simple.pdf")

plt.close('all')

print("\n" + "="*70)
print("RADAR PLOTS CREATED SUCCESSFULLY!")
print("="*70)
print("\nTwo versions created:")
print("  1. radar_plot.* - All methods comparison")
print("  2. radar_plot_simple.* - FL+RL vs LRU only (cleaner for papers)")
