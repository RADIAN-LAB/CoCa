#!/usr/bin/env python3
"""
Generate FL advisor convergence plot showing cache hit rate improvement over time.
Matches the style of fig_fl_training_curve.pdf
"""

import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
from pathlib import Path

# Set publication style
plt.style.use('seaborn-v0_8-paper')
plt.rcParams['figure.dpi'] = 100
plt.rcParams['font.size'] = 14
plt.rcParams['font.weight'] = 'normal'
plt.rcParams['font.family'] = 'sans-serif'
plt.rcParams['axes.labelsize'] = 16
plt.rcParams['axes.labelweight'] = 'bold'
plt.rcParams['axes.titlesize'] = 0  # No titles
plt.rcParams['xtick.labelsize'] = 12
plt.rcParams['ytick.labelsize'] = 12
plt.rcParams['legend.fontsize'] = 12

# Paths
ROOT = Path(__file__).parent.parent
log_path = ROOT / "experiments" / "logs" / "fl_training.csv"
output_dir = ROOT / "experiments" / "sumo" / "paper_figures"
output_dir.mkdir(parents=True, exist_ok=True)

# Read FL training log
df = pd.read_csv(log_path)

# Calculate cumulative hit rate at each timestep
df['cumulative_hit_rate'] = (df['cache_hits'] / (df['cache_hits'] + df['cache_misses'])) * 100

# Create figure
fig, ax = plt.subplots(figsize=(10, 6))

# Use smoothed trend line for cleaner visualization
window = 10
if len(df) >= window:
    smoothed = df['cumulative_hit_rate'].rolling(window=window, min_periods=1).mean()
    ax.plot(df['timestamp'], smoothed, 
            linewidth=3, color='#27ae60', 
            label='FL Training Convergence', alpha=0.9)

# Add confidence band to show learning stability
if len(df) >= window:
    std = df['cumulative_hit_rate'].rolling(window=window, min_periods=1).std()
    ax.fill_between(df['timestamp'], 
                     smoothed - std, 
                     smoothed + std,
                     alpha=0.2, color='#27ae60', label='Confidence Band')

# Add annotation showing convergence
final_rate = df['cumulative_hit_rate'].iloc[-1]
ax.annotate(f'Converged: {final_rate:.1f}%', 
            xy=(df['timestamp'].iloc[-1], final_rate),
            xytext=(df['timestamp'].iloc[-100], final_rate - 3),
            arrowprops=dict(arrowstyle='->', color='#155724', lw=2),
            fontsize=12, fontweight='bold', color='#155724')

ax.set_xlabel('Training Timestep', fontweight='bold', fontsize=16)
ax.set_ylabel('Cumulative Hit Rate (%)', fontweight='bold', fontsize=16)
ax.grid(True, linestyle='--', alpha=0.3, linewidth=1)
ax.legend(loc='lower right', frameon=True, fancybox=True, shadow=True)

# Set y-axis limits to focus on the learning progression
min_rate = max(0, df['cumulative_hit_rate'].min() - 5)
max_rate = min(100, df['cumulative_hit_rate'].max() + 2)
ax.set_ylim([min_rate, max_rate])

plt.tight_layout()

# Save
pdf_path = output_dir / "fig_fl_convergence.pdf"
png_path = output_dir / "fig_fl_convergence.png"
plt.savefig(pdf_path, dpi=300, bbox_inches='tight')
plt.savefig(png_path, dpi=300, bbox_inches='tight')
plt.close()

print(f"✓ FL convergence plot saved:")
print(f"  PDF: {pdf_path}")
print(f"  PNG: {png_path}")
print(f"\nFinal hit rate: {final_rate:.2f}%")
print(f"Initial hit rate: {df['cumulative_hit_rate'].iloc[0]:.2f}%")
print(f"Improvement: {final_rate - df['cumulative_hit_rate'].iloc[0]:.2f} percentage points")
