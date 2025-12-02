#!/usr/bin/env python3
"""
Generate Simple System Architecture Diagram for FL-RL Caching System
"""

import matplotlib.pyplot as plt
import matplotlib.patches as patches
from matplotlib.patches import FancyBboxPatch, Rectangle
import numpy as np

# Set up the figure
fig, ax = plt.subplots(1, 1, figsize=(14, 10))
ax.set_xlim(0, 14)
ax.set_ylim(0, 10)
ax.axis('off')

# Define colors
colors = {
    'fl_blue': '#3498DB',
    'rl_green': '#2ECC71', 
    'cache_orange': '#E67E22',
    'light_gray': '#ECF0F1',
    'dark_gray': '#34495E',
    'vehicle_blue': '#5DADE2',
    'rsu_green': '#58D68D'
}

# Title
ax.text(7, 9.5, 'FL-RL Intelligent Caching System Architecture', 
        fontsize=16, fontweight='bold', ha='center')

# Layer 3: Central Coordination (Top)
layer3_y = 7.5
ax.text(1, layer3_y + 0.3, 'Layer 3: Central Coordination', 
        fontsize=12, fontweight='bold', color=colors['dark_gray'])

# SDN Controller with FL Server
controller = FancyBboxPatch((3, layer3_y-0.4), 3, 0.8, 
                           boxstyle="round,pad=0.1", 
                           facecolor=colors['fl_blue'], alpha=0.7,
                           edgecolor=colors['fl_blue'], linewidth=2)
ax.add_patch(controller)
ax.text(4.5, layer3_y, 'SDN Controller\n+ FL Server', 
        fontsize=11, fontweight='bold', ha='center', va='center', color='white')

# DQN Agent
dqn = FancyBboxPatch((8, layer3_y-0.4), 2.5, 0.8, 
                     boxstyle="round,pad=0.1", 
                     facecolor=colors['rl_green'], alpha=0.7,
                     edgecolor=colors['rl_green'], linewidth=2)
ax.add_patch(dqn)
ax.text(9.25, layer3_y, 'DQN Agent', 
        fontsize=11, fontweight='bold', ha='center', va='center', color='white')

# Layer 2: Edge Computing (Middle)
layer2_y = 5
ax.text(1, layer2_y + 0.3, 'Layer 2: Edge Computing', 
        fontsize=12, fontweight='bold', color=colors['dark_gray'])

# RSUs with Caches
rsu_positions = [3, 5.5, 8, 10.5]
for i, x in enumerate(rsu_positions):
    # RSU
    rsu = FancyBboxPatch((x-0.6, layer2_y-0.3), 1.2, 0.6, 
                         boxstyle="round,pad=0.05", 
                         facecolor=colors['rsu_green'], alpha=0.7,
                         edgecolor=colors['rsu_green'], linewidth=1.5)
    ax.add_patch(rsu)
    ax.text(x, layer2_y, f'RSU {i+1}', 
            fontsize=10, fontweight='bold', ha='center', va='center', color='white')
    
    # Cache below RSU
    cache = Rectangle((x-0.4, layer2_y-1), 0.8, 0.4, 
                     facecolor=colors['cache_orange'], alpha=0.7,
                     edgecolor=colors['cache_orange'], linewidth=1.5)
    ax.add_patch(cache)
    ax.text(x, layer2_y-0.8, 'Cache', 
            fontsize=9, ha='center', va='center', color='white', fontweight='bold')

# Layer 1: Vehicular Network (Bottom)
layer1_y = 2.5
ax.text(1, layer1_y + 0.3, 'Layer 1: Vehicular Network', 
        fontsize=12, fontweight='bold', color=colors['dark_gray'])

# Road
road_y = layer1_y - 0.8
ax.plot([2.5, 11], [road_y, road_y], color='gray', linewidth=12, alpha=0.8)
ax.plot([2.5, 11], [road_y, road_y], color='yellow', linewidth=2, linestyle='--')

# Vehicles
vehicle_positions = [3, 4.5, 6, 7.5, 9, 10.5]
for i, x in enumerate(vehicle_positions):
    vehicle = FancyBboxPatch((x-0.3, road_y-0.15), 0.6, 0.3, 
                            boxstyle="round,pad=0.02", 
                            facecolor=colors['vehicle_blue'], alpha=0.8,
                            edgecolor='navy', linewidth=1)
    ax.add_patch(vehicle)
    ax.text(x, road_y, f'V{i+1}', 
            fontsize=9, fontweight='bold', ha='center', va='center', color='white')

# Communication Lines
# FL Model Updates (Layer 3 to Layer 2)
for x in rsu_positions:
    ax.plot([4.5, x], [layer3_y-0.4, layer2_y+0.3], 
            color=colors['fl_blue'], linewidth=2, alpha=0.8, linestyle='--')

# Policy Distribution (DQN to RSUs)
for x in rsu_positions:
    ax.plot([9.25, x], [layer3_y-0.4, layer2_y+0.3], 
            color=colors['rl_green'], linewidth=2, alpha=0.8, linestyle=':')

# V2I Communication (Vehicles to RSUs)
for i, v_x in enumerate(vehicle_positions):
    r_x = rsu_positions[min(i, len(rsu_positions)-1)]
    ax.plot([v_x, r_x], [road_y+0.15, layer2_y-0.3], 
            color='red', linewidth=1.5, alpha=0.7)

# V2V Communication (between some vehicles)
v2v_pairs = [(3, 4.5), (6, 7.5), (9, 10.5)]
for x1, x2 in v2v_pairs:
    ax.plot([x1, x2], [road_y+0.4, road_y+0.4], 
            color='blue', linewidth=2, alpha=0.7)

# Legend (Bottom Right)
legend_x = 11.5
legend_y = 3.5

ax.text(legend_x, legend_y + 0.8, 'Legend', 
        fontsize=12, fontweight='bold', color=colors['dark_gray'])

# FL Component
fl_box = Rectangle((legend_x, legend_y + 0.4), 0.3, 0.2, 
                  facecolor=colors['fl_blue'], alpha=0.7)
ax.add_patch(fl_box)
ax.text(legend_x + 0.4, legend_y + 0.5, 'Federated Learning', fontsize=10)

# RL Component  
rl_box = Rectangle((legend_x, legend_y + 0.1), 0.3, 0.2, 
                  facecolor=colors['rl_green'], alpha=0.7)
ax.add_patch(rl_box)
ax.text(legend_x + 0.4, legend_y + 0.2, 'Reinforcement Learning', fontsize=10)

# Cache Component
cache_box = Rectangle((legend_x, legend_y - 0.2), 0.3, 0.2, 
                     facecolor=colors['cache_orange'], alpha=0.7)
ax.add_patch(cache_box)
ax.text(legend_x + 0.4, legend_y - 0.1, 'Intelligent Cache', fontsize=10)

# Communication Lines in Legend
ax.plot([legend_x, legend_x + 0.3], [legend_y - 0.5, legend_y - 0.5], 
        color=colors['fl_blue'], linewidth=2, linestyle='--')
ax.text(legend_x + 0.4, legend_y - 0.5, 'FL Model Updates', fontsize=10)

ax.plot([legend_x, legend_x + 0.3], [legend_y - 0.8, legend_y - 0.8], 
        color=colors['rl_green'], linewidth=2, linestyle=':')
ax.text(legend_x + 0.4, legend_y - 0.8, 'Policy Distribution', fontsize=10)

ax.plot([legend_x, legend_x + 0.3], [legend_y - 1.1, legend_y - 1.1], 
        color='red', linewidth=2)
ax.text(legend_x + 0.4, legend_y - 1.1, 'V2I Communication', fontsize=10)

ax.plot([legend_x, legend_x + 0.3], [legend_y - 1.4, legend_y - 1.4], 
        color='blue', linewidth=2)
ax.text(legend_x + 0.4, legend_y - 1.4, 'V2V Communication', fontsize=10)

# Add layer background boxes for clarity
layer3_bg = FancyBboxPatch((2.5, layer3_y-0.7), 8.5, 1.4, 
                          boxstyle="round,pad=0.1", 
                          facecolor=colors['fl_blue'], alpha=0.1,
                          edgecolor=colors['fl_blue'], linewidth=1, linestyle='-')
ax.add_patch(layer3_bg)

layer2_bg = FancyBboxPatch((2.5, layer2_y-1.3), 8.5, 1.6, 
                          boxstyle="round,pad=0.1", 
                          facecolor=colors['rl_green'], alpha=0.1,
                          edgecolor=colors['rl_green'], linewidth=1, linestyle='-')
ax.add_patch(layer2_bg)

layer1_bg = FancyBboxPatch((2.5, layer1_y-1.2), 8.5, 1.5, 
                          boxstyle="round,pad=0.1", 
                          facecolor=colors['cache_orange'], alpha=0.1,
                          edgecolor=colors['cache_orange'], linewidth=1, linestyle='-')
ax.add_patch(layer1_bg)

plt.tight_layout()
plt.savefig('/Users/kosar/Documents/Ph.D code/windsurf/sdn-vanet-optimizer/docs/system_architecture_simple.png', 
            dpi=300, bbox_inches='tight', facecolor='white')
plt.close()

print("✅ Simple System Architecture diagram saved: system_architecture_simple.png")
