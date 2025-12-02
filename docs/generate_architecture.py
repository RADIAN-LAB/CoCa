#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Generate System Architecture Diagram for FL-RL Caching System
"""

import matplotlib.pyplot as plt
import matplotlib.patches as patches
from matplotlib.patches import FancyBboxPatch, Circle, Rectangle
import numpy as np

# Set up the figure
fig, ax = plt.subplots(1, 1, figsize=(16, 12))
ax.set_xlim(0, 16)
ax.set_ylim(0, 12)
ax.axis('off')

# Define colors
colors = {
    'fl_blue': '#4682B4',
    'rl_green': '#228B22', 
    'cache_orange': '#FF8C00',
    'light_gray': '#F0F0F0',
    'dark_gray': '#808080',
    'vehicle_blue': '#87CEEB',
    'rsu_gray': '#D3D3D3'
}

# Title
ax.text(8, 11.5, 'Federated Learning-Enhanced Intelligent Caching System\nfor Vehicular Networks', 
        fontsize=18, fontweight='bold', ha='center', va='center')

# Layer 3: Central Coordination Layer (top)
layer3_y = 9.5
ax.text(0.5, layer3_y + 0.5, 'Layer 3:\nCentral\nCoordination', 
        fontsize=12, fontweight='bold', ha='left', va='center')

# Global FL Coordinator
fl_coord = FancyBboxPatch((3, layer3_y-0.3), 3, 0.8, 
                         boxstyle="round,pad=0.1", 
                         facecolor=colors['fl_blue'], alpha=0.3,
                         edgecolor=colors['fl_blue'], linewidth=2)
ax.add_patch(fl_coord)
ax.text(4.5, layer3_y, 'Global FL\nCoordinator', fontsize=11, fontweight='bold', 
        ha='center', va='center')

# DQN Agent (Brain)
brain = Circle((10, layer3_y), 0.6, facecolor=colors['rl_green'], alpha=0.3,
               edgecolor=colors['rl_green'], linewidth=2)
ax.add_patch(brain)
ax.text(10, layer3_y, 'DQN\nAgent', fontsize=11, fontweight='bold', 
        ha='center', va='center')

# Neural Network representation
nn_x, nn_y = 11.5, layer3_y
# Input layer
for i in range(3):
    circle = Circle((nn_x, nn_y + 0.4 - i*0.4), 0.08, 
                   facecolor=colors['rl_green'], alpha=0.6)
    ax.add_patch(circle)

# Hidden layer
for i in range(4):
    circle = Circle((nn_x + 0.8, nn_y + 0.6 - i*0.4), 0.08, 
                   facecolor=colors['rl_green'], alpha=0.6)
    ax.add_patch(circle)

# Output layer
circle = Circle((nn_x + 1.6, nn_y), 0.08, 
               facecolor=colors['rl_green'], alpha=0.6)
ax.add_patch(circle)

# Neural network connections
for i in range(3):
    for j in range(4):
        ax.plot([nn_x + 0.08, nn_x + 0.72], 
                [nn_y + 0.4 - i*0.4, nn_y + 0.6 - j*0.4], 
                'gray', alpha=0.3, linewidth=0.5)

for i in range(4):
    ax.plot([nn_x + 0.88, nn_x + 1.52], 
            [nn_y + 0.6 - i*0.4, nn_y], 
            'gray', alpha=0.3, linewidth=0.5)

ax.text(nn_x + 0.8, nn_y - 1, 'Q-Network', fontsize=9, ha='center')

# Policy Distribution
policy_dist = FancyBboxPatch((12.5, layer3_y-0.3), 2.5, 0.8, 
                            boxstyle="round,pad=0.1", 
                            facecolor=colors['dark_gray'], alpha=0.3,
                            edgecolor=colors['dark_gray'], linewidth=2)
ax.add_patch(policy_dist)
ax.text(13.75, layer3_y, 'Policy\nDistribution', fontsize=11, fontweight='bold', 
        ha='center', va='center')

# Arrows between components
ax.annotate('', xy=(9.3, layer3_y), xytext=(6.1, layer3_y),
            arrowprops=dict(arrowstyle='->', lw=2, color=colors['fl_blue']))
ax.text(7.7, layer3_y + 0.3, 'Model Updates', fontsize=9, ha='center')

ax.annotate('', xy=(12.4, layer3_y), xytext=(10.7, layer3_y),
            arrowprops=dict(arrowstyle='->', lw=2, color=colors['rl_green']))
ax.text(11.5, layer3_y + 0.3, 'Policies', fontsize=9, ha='center')

# Layer 2: Edge/Fog Computing Layer (middle)
layer2_y = 6.5
ax.text(0.5, layer2_y + 0.5, 'Layer 2:\nEdge/Fog\nComputing', 
        fontsize=12, fontweight='bold', ha='left', va='center')

# Edge servers and caches
edge_positions = [3, 5.5, 8, 10.5, 13]
for i, x in enumerate(edge_positions):
    # Edge server
    edge_server = FancyBboxPatch((x-0.6, layer2_y-0.3), 1.2, 0.8, 
                                boxstyle="round,pad=0.1", 
                                facecolor=colors['fl_blue'], alpha=0.3,
                                edgecolor=colors['fl_blue'], linewidth=2)
    ax.add_patch(edge_server)
    ax.text(x, layer2_y, f'Edge\nServer {i+1}', fontsize=9, fontweight='bold', 
            ha='center', va='center')
    
    # Cache (cylinder representation)
    cache_base = patches.Ellipse((x, layer2_y-1.2), 0.8, 0.2, 
                                facecolor=colors['cache_orange'], alpha=0.3,
                                edgecolor=colors['cache_orange'])
    ax.add_patch(cache_base)
    cache_body = Rectangle((x-0.4, layer2_y-1.3), 0.8, 0.3, 
                          facecolor=colors['cache_orange'], alpha=0.3,
                          edgecolor=colors['cache_orange'])
    ax.add_patch(cache_body)
    cache_top = patches.Ellipse((x, layer2_y-1.0), 0.8, 0.2, 
                               facecolor=colors['cache_orange'], alpha=0.3,
                               edgecolor=colors['cache_orange'])
    ax.add_patch(cache_top)
    ax.text(x, layer2_y-1.15, 'Cache', fontsize=9, fontweight='bold', 
            ha='center', va='center')
    
    # FL Node
    fl_node = FancyBboxPatch((x-0.4, layer2_y+0.6), 0.8, 0.4, 
                            boxstyle="round,pad=0.05", 
                            facecolor=colors['fl_blue'], alpha=0.2,
                            edgecolor=colors['fl_blue'], linewidth=1)
    ax.add_patch(fl_node)
    ax.text(x, layer2_y+0.8, 'FL Node', fontsize=8, ha='center', va='center')
    
    # Cache hit/miss indicators
    hit_circle = Circle((x+0.3, layer2_y-1.15), 0.1, facecolor='green', alpha=0.6)
    miss_circle = Circle((x-0.3, layer2_y-1.15), 0.1, facecolor='red', alpha=0.6)
    ax.add_patch(hit_circle)
    ax.add_patch(miss_circle)
    ax.text(x+0.3, layer2_y-1.15, 'H', fontsize=7, ha='center', va='center', color='white', fontweight='bold')
    ax.text(x-0.3, layer2_y-1.15, 'M', fontsize=7, ha='center', va='center', color='white', fontweight='bold')
    
    # Arrows from edge to cache
    ax.annotate('', xy=(x, layer2_y-0.9), xytext=(x, layer2_y-0.4),
                arrowprops=dict(arrowstyle='->', lw=1.5, color=colors['cache_orange']))
    
    # FL aggregation arrows (dashed)
    ax.annotate('', xy=(4.5, layer3_y-0.4), xytext=(x, layer2_y+1.1),
                arrowprops=dict(arrowstyle='->', lw=1, color=colors['fl_blue'], 
                               linestyle='dashed', alpha=0.7))
    
    # Policy distribution arrows (dashed)
    ax.annotate('', xy=(x, layer2_y+0.5), xytext=(13.75, layer3_y-0.4),
                arrowprops=dict(arrowstyle='->', lw=1, color=colors['rl_green'], 
                               linestyle='dashed', alpha=0.7))

# Layer 1: Vehicular Network Layer (bottom)
layer1_y = 3
ax.text(0.5, layer1_y + 0.5, 'Layer 1:\nVehicular\nNetwork', 
        fontsize=12, fontweight='bold', ha='left', va='center')

# RSUs
rsu_positions = [3, 5.5, 8, 10.5, 13]
for i, x in enumerate(rsu_positions):
    rsu = Rectangle((x-0.2, layer1_y-0.4), 0.4, 1.2, 
                   facecolor=colors['rsu_gray'], alpha=0.7,
                   edgecolor='black', linewidth=1)
    ax.add_patch(rsu)
    ax.text(x, layer1_y+0.2, f'RSU\n{i+1}', fontsize=9, fontweight='bold', 
            ha='center', va='center')
    
    # Connection to edge server
    ax.annotate('', xy=(x, layer2_y-0.4), xytext=(x, layer1_y+0.9),
                arrowprops=dict(arrowstyle='->', lw=2, color='black'))

# Vehicles on road
vehicle_positions = [2.5, 3.5, 4.8, 6.2, 7.5, 8.5, 9.8, 11.2, 12.5, 13.5]
road_y = layer1_y - 1.5

# Roads
ax.plot([2, 14.5], [road_y-0.2, road_y-0.2], color='gray', linewidth=8, alpha=0.7)
ax.plot([2, 14.5], [road_y+0.2, road_y+0.2], color='gray', linewidth=8, alpha=0.7)
ax.plot([2, 14.5], [road_y, road_y], color='yellow', linewidth=1, linestyle='--')

for i, x in enumerate(vehicle_positions):
    vehicle = FancyBboxPatch((x-0.25, road_y-0.15), 0.5, 0.3, 
                            boxstyle="round,pad=0.02", 
                            facecolor=colors['vehicle_blue'], alpha=0.8,
                            edgecolor='navy', linewidth=1)
    ax.add_patch(vehicle)
    ax.text(x, road_y, 'V', fontsize=8, fontweight='bold', ha='center', va='center')

# V2V Communications (wavy lines between some vehicles)
v2v_pairs = [(2.5, 3.5), (4.8, 6.2), (8.5, 9.8), (11.2, 12.5)]
for x1, x2 in v2v_pairs:
    # Create wavy line
    x_wave = np.linspace(x1, x2, 20)
    y_wave = road_y + 0.3 + 0.1 * np.sin(10 * np.pi * (x_wave - x1) / (x2 - x1))
    ax.plot(x_wave, y_wave, color='blue', linewidth=1.5, alpha=0.7)
    ax.text((x1+x2)/2, road_y + 0.5, 'V2V', fontsize=7, ha='center', color='blue')

# V2I Communications (wavy lines from vehicles to nearby RSUs)
for v_x in vehicle_positions:
    for r_x in rsu_positions:
        if abs(v_x - r_x) < 1.5:  # Only show nearby connections
            # Create wavy line
            x_wave = np.linspace(v_x, r_x, 15)
            y_wave = np.linspace(road_y + 0.15, layer1_y - 0.4, 15) + 0.1 * np.sin(8 * np.pi * np.linspace(0, 1, 15))
            ax.plot(x_wave, y_wave, color='red', linewidth=1, alpha=0.6)

ax.text(8, road_y - 0.8, 'V2I Communications', fontsize=9, ha='center', color='red')

# Legend
legend_x = 1
legend_y = 8
ax.text(legend_x, legend_y + 0.5, 'Legend:', fontsize=12, fontweight='bold')

# FL component
fl_legend = Rectangle((legend_x, legend_y), 0.4, 0.2, 
                     facecolor=colors['fl_blue'], alpha=0.3,
                     edgecolor=colors['fl_blue'])
ax.add_patch(fl_legend)
ax.text(legend_x + 0.6, legend_y + 0.1, 'Federated Learning', fontsize=10)

# RL component
rl_legend = Rectangle((legend_x, legend_y - 0.4), 0.4, 0.2, 
                     facecolor=colors['rl_green'], alpha=0.3,
                     edgecolor=colors['rl_green'])
ax.add_patch(rl_legend)
ax.text(legend_x + 0.6, legend_y - 0.3, 'Reinforcement Learning', fontsize=10)

# Cache component
cache_legend = Rectangle((legend_x, legend_y - 0.8), 0.4, 0.2, 
                        facecolor=colors['cache_orange'], alpha=0.3,
                        edgecolor=colors['cache_orange'])
ax.add_patch(cache_legend)
ax.text(legend_x + 0.6, legend_y - 0.7, 'Caching System', fontsize=10)

# Communication lines
ax.plot([legend_x, legend_x + 0.4], [legend_y - 1.2, legend_y - 1.2], 
        color='blue', linewidth=2, alpha=0.7)
ax.text(legend_x + 0.6, legend_y - 1.2, 'V2V Communication', fontsize=10)

ax.plot([legend_x, legend_x + 0.4], [legend_y - 1.6, legend_y - 1.6], 
        color='red', linewidth=2, alpha=0.7)
ax.text(legend_x + 0.6, legend_y - 1.6, 'V2I Communication', fontsize=10)

ax.plot([legend_x, legend_x + 0.4], [legend_y - 2.0, legend_y - 2.0], 
        color='black', linewidth=2, linestyle='dashed')
ax.text(legend_x + 0.6, legend_y - 2.0, 'Data Flow', fontsize=10)

# Background boxes for layers
layer3_bg = FancyBboxPatch((2.5, layer3_y-0.8), 13, 2, 
                          boxstyle="round,pad=0.2", 
                          facecolor='lightblue', alpha=0.1,
                          edgecolor='blue', linewidth=1, linestyle='--')
ax.add_patch(layer3_bg)

layer2_bg = FancyBboxPatch((2.5, layer2_y-1.8), 13, 3, 
                          boxstyle="round,pad=0.2", 
                          facecolor='lightgreen', alpha=0.1,
                          edgecolor='green', linewidth=1, linestyle='--')
ax.add_patch(layer2_bg)

layer1_bg = FancyBboxPatch((2.5, layer1_y-2.2), 13, 3, 
                          boxstyle="round,pad=0.2", 
                          facecolor='lightyellow', alpha=0.1,
                          edgecolor='orange', linewidth=1, linestyle='--')
ax.add_patch(layer1_bg)

plt.tight_layout()
plt.savefig('/Users/kosar/Documents/Ph.D code/windsurf/sdn-vanet-optimizer/docs/system_architecture.png', 
            dpi=300, bbox_inches='tight', facecolor='white')
plt.close()

print("✅ System Architecture diagram saved: system_architecture.png")
