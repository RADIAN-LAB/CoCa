#!/usr/bin/env python3
"""
Generate FL training curve showing cache hit rate improvement over time.
"""

import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

# Read FL training data
df = pd.read_csv('experiments/logs/fl_training.csv')

# Calculate cache hit rate at each timestep
df['total_requests'] = df['cache_hits'] + df['cache_misses']
df['hit_rate'] = (df['cache_hits'] / df['total_requests']) * 100

# Create figure with professional styling
plt.figure(figsize=(10, 6))
plt.style.use('seaborn-v0_8-darkgrid')

# Plot hit rate over time
plt.plot(df['timestamp'], df['hit_rate'], 
         linewidth=2.5, color='#2E86AB', label='Cache Hit Rate',
         marker='o', markersize=3, markevery=10)

# Add trend line
z = np.polyfit(df['timestamp'], df['hit_rate'], 3)
p = np.poly1d(z)
plt.plot(df['timestamp'], p(df['timestamp']), 
         '--', linewidth=2, color='#A23B72', alpha=0.7, label='Trend')

# Formatting
plt.xlabel('Training Timestep', fontsize=14, fontweight='bold')
plt.ylabel('Cache Hit Rate (%)', fontsize=14, fontweight='bold')
plt.title('FL Advisor Training Convergence', fontsize=16, fontweight='bold', pad=20)
plt.grid(True, alpha=0.3, linestyle='--')
plt.legend(fontsize=12, loc='lower right', framealpha=0.9)

# Add annotations for key milestones
initial_hit_rate = df['hit_rate'].iloc[10]
final_hit_rate = df['hit_rate'].iloc[-1]

plt.annotate(f'Initial: {initial_hit_rate:.1f}%', 
             xy=(10, initial_hit_rate), 
             xytext=(30, initial_hit_rate - 10),
             fontsize=11, fontweight='bold',
             bbox=dict(boxstyle='round,pad=0.5', facecolor='yellow', alpha=0.7),
             arrowprops=dict(arrowstyle='->', color='black', lw=1.5))

plt.annotate(f'Final: {final_hit_rate:.1f}%', 
             xy=(199, final_hit_rate), 
             xytext=(160, final_hit_rate + 5),
             fontsize=11, fontweight='bold',
             bbox=dict(boxstyle='round,pad=0.5', facecolor='lightgreen', alpha=0.7),
             arrowprops=dict(arrowstyle='->', color='black', lw=1.5))

# Set axis limits
plt.xlim(-5, 205)
plt.ylim(0, 100)

# Add horizontal reference line at 90%
plt.axhline(y=90, color='red', linestyle=':', linewidth=1.5, alpha=0.5, label='90% Target')

plt.tight_layout()

# Save figure
plt.savefig('experiments/results/fl_training_curve.pdf', dpi=300, bbox_inches='tight')
plt.savefig('experiments/results/fl_training_curve.png', dpi=300, bbox_inches='tight')

print("✓ FL training curve saved to experiments/results/")
print(f"  Initial hit rate (t=10): {initial_hit_rate:.2f}%")
print(f"  Final hit rate (t=199): {final_hit_rate:.2f}%")
print(f"  Improvement: {final_hit_rate - initial_hit_rate:.2f} percentage points")

# Show plot
plt.show()
