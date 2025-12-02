#!/usr/bin/env python3
"""
Comprehensive comparison of caching strategies for VANET task offloading.

Comparison scenarios:
1. No Cache - baseline task scheduling without any caching
2. Traditional Cache - LRU, LFU, Random (no FL)
3. FL-based Cache - Federated Learning for popularity prediction (from literature)
4. FL+RL Cache - Our proposed method (FL + Reinforcement Learning)

Metrics:
- Task success rate (%)
- Average completion time (ms)
- Cache hit rate (%)
- Energy consumption (J)
- Execution time (s)
"""

import json
import subprocess
import sys
from pathlib import Path
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np

# Configuration
TRACE_FILE = "experiments/synthetic/input/final_test.csv"
OUTPUT_DIR = Path("experiments/comparison")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# Experiment scenarios
SCENARIOS = {
    "1_no_cache": {
        "name": "No Cache",
        "description": "Baseline: Task scheduling without caching",
        "args": ["--evict_policy", "none", "--no_fl"],
        "color": "#e74c3c"
    },
    "2_random": {
        "name": "Random Eviction",
        "description": "Traditional cache with random eviction",
        "args": ["--evict_policy", "random"],
        "color": "#95a5a6"
    },
    "3_lru": {
        "name": "LRU",
        "description": "Traditional cache with LRU eviction",
        "args": ["--evict_policy", "lru"],
        "color": "#3498db"
    },
    "4_lfu": {
        "name": "LFU",
        "description": "Traditional cache with LFU eviction",
        "args": ["--evict_policy", "lfu"],
        "color": "#9b59b6"
    },
    "5_fl_only": {
        "name": "FL-based Cache",
        "description": "Federated Learning for popularity prediction (literature approach)",
        "args": ["--evict_policy", "lru"],  # FL with fixed LRU eviction
        "color": "#f39c12"
    },
    "6_fl_rl": {
        "name": "FL+RL (Ours)",
        "description": "Our proposed: FL + RL adaptive caching",
        "args": ["--load_rl", "experiments/models/final_rl_trained.pt"],
        "color": "#27ae60"
    }
}

def run_experiment(scenario_id, scenario_config):
    """Run a single experiment scenario."""
    print(f"\n{'='*60}")
    print(f"Running: {scenario_config['name']}")
    print(f"Description: {scenario_config['description']}")
    print(f"{'='*60}")
    
    output_file = OUTPUT_DIR / f"{scenario_id}_results.json"
    
    cmd = [
        "python3", "scripts/run_experiment.py",
        "--trace", TRACE_FILE,
        "--output", str(output_file)
    ] + scenario_config['args']
    
    print(f"Command: {' '.join(cmd)}")
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        print(result.stdout)
        return output_file
    except subprocess.CalledProcessError as e:
        print(f"Error running {scenario_id}: {e}")
        print(f"Stdout: {e.stdout}")
        print(f"Stderr: {e.stderr}")
        return None

def calculate_energy(results):
    """
    Calculate energy consumption based on:
    - Cache hits: low energy (local access)
    - Cache misses: high energy (remote computation + transmission)
    - Task failures: wasted energy
    
    Energy model (simplified):
    - Cache hit: 0.1 J (local memory access)
    - Cache miss + success: 2.0 J (computation + transmission)
    - Cache miss + failure: 1.5 J (partial computation + transmission)
    """
    hits = results['cache_hits']
    misses = results['cache_misses']
    total_tasks = results['total_tasks']
    success_rate = results['success_rate']
    
    # Successful tasks from cache
    energy_hits = hits * 0.1
    
    # Successful tasks computed remotely
    successful_misses = misses * success_rate
    energy_successful_misses = successful_misses * 2.0
    
    # Failed tasks (wasted energy)
    failed_tasks = total_tasks * (1 - success_rate)
    energy_failures = failed_tasks * 1.5
    
    total_energy = energy_hits + energy_successful_misses + energy_failures
    
    return {
        'total_energy_j': total_energy,
        'energy_per_task_j': total_energy / total_tasks,
        'energy_hits_j': energy_hits,
        'energy_misses_j': energy_successful_misses,
        'energy_failures_j': energy_failures
    }

def collect_results():
    """Collect results from all experiments."""
    results = {}
    
    for scenario_id, scenario_config in SCENARIOS.items():
        result_file = OUTPUT_DIR / f"{scenario_id}_results.json"
        
        if not result_file.exists():
            print(f"Warning: {result_file} not found, skipping {scenario_id}")
            continue
        
        with open(result_file) as f:
            data = json.load(f)
        
        # Calculate energy consumption
        energy = calculate_energy(data)
        
        # Compile metrics
        results[scenario_id] = {
            'name': scenario_config['name'],
            'color': scenario_config['color'],
            'success_rate': data['success_rate'] * 100,  # Convert to percentage
            'avg_completion_time': data['average_completion'] * 1000,  # Convert to ms
            'cache_hit_rate': (data['cache_hits'] / (data['cache_hits'] + data['cache_misses']) * 100) 
                              if (data['cache_hits'] + data['cache_misses']) > 0 else 0,
            'energy_consumption': energy['total_energy_j'],
            'energy_per_task': energy['energy_per_task_j'],
            'execution_time': data['runtime_seconds'],
            'total_tasks': data['total_tasks'],
            'cache_hits': data['cache_hits'],
            'cache_misses': data['cache_misses']
        }
    
    return results

def generate_comparison_table(results):
    """Generate comparison table."""
    df = pd.DataFrame(results).T
    
    # Reorder columns
    columns = ['name', 'success_rate', 'avg_completion_time', 'cache_hit_rate', 
               'energy_consumption', 'energy_per_task', 'execution_time']
    df = df[columns]
    
    # Save to CSV
    csv_file = OUTPUT_DIR / "comparison_table.csv"
    df.to_csv(csv_file, index=True)
    print(f"\nComparison table saved to: {csv_file}")
    
    # Print formatted table
    print("\n" + "="*100)
    print("COMPREHENSIVE COMPARISON RESULTS")
    print("="*100)
    print(f"{'Method':<20} {'Success Rate':<15} {'Avg Time (ms)':<15} {'Hit Rate':<12} {'Energy (J)':<12} {'Exec Time (s)':<12}")
    print("-"*100)
    
    for idx, row in df.iterrows():
        print(f"{row['name']:<20} {row['success_rate']:>13.2f}% {row['avg_completion_time']:>13.2f} "
              f"{row['cache_hit_rate']:>10.2f}% {row['energy_consumption']:>10.2f} {row['execution_time']:>13.2f}")
    
    return df

def generate_plots(results):
    """Generate comparison plots."""
    sns.set_style("whitegrid")
    fig, axes = plt.subplots(2, 3, figsize=(18, 12))
    fig.suptitle('Comprehensive Comparison of Caching Strategies', fontsize=16, fontweight='bold')
    
    # Extract data
    names = [r['name'] for r in results.values()]
    colors = [r['color'] for r in results.values()]
    
    metrics = {
        'Success Rate (%)': [r['success_rate'] for r in results.values()],
        'Avg Completion Time (ms)': [r['avg_completion_time'] for r in results.values()],
        'Cache Hit Rate (%)': [r['cache_hit_rate'] for r in results.values()],
        'Energy Consumption (J)': [r['energy_consumption'] for r in results.values()],
        'Energy per Task (J)': [r['energy_per_task'] for r in results.values()],
        'Execution Time (s)': [r['execution_time'] for r in results.values()]
    }
    
    # Plot each metric
    for idx, (metric_name, values) in enumerate(metrics.items()):
        ax = axes[idx // 3, idx % 3]
        bars = ax.bar(names, values, color=colors, alpha=0.8, edgecolor='black', linewidth=1.5)
        ax.set_title(metric_name, fontsize=12, fontweight='bold')
        ax.set_ylabel(metric_name.split('(')[0].strip())
        ax.tick_params(axis='x', rotation=45)
        ax.grid(axis='y', alpha=0.3)
        
        # Add value labels on bars
        for bar in bars:
            height = bar.get_height()
            ax.text(bar.get_x() + bar.get_width()/2., height,
                   f'{height:.1f}',
                   ha='center', va='bottom', fontsize=9)
        
        # Highlight best performer
        best_idx = values.index(max(values)) if 'Time' not in metric_name and 'Energy' not in metric_name else values.index(min(values))
        bars[best_idx].set_edgecolor('gold')
        bars[best_idx].set_linewidth(3)
    
    plt.tight_layout()
    plot_file = OUTPUT_DIR / "comparison_plots.png"
    plt.savefig(plot_file, dpi=300, bbox_inches='tight')
    print(f"\nComparison plots saved to: {plot_file}")
    plt.close()
    
    # Generate radar chart for overall comparison
    generate_radar_chart(results)

def generate_radar_chart(results):
    """Generate radar chart for multi-metric comparison."""
    from math import pi
    
    # Normalize metrics to 0-100 scale
    metrics_data = {}
    for scenario_id, data in results.items():
        metrics_data[scenario_id] = {
            'name': data['name'],
            'color': data['color'],
            'values': []
        }
    
    # Metrics to include (normalized)
    metric_names = ['Success\nRate', 'Cache\nHit Rate', 'Completion\nTime', 'Energy\nEfficiency']
    
    # Collect and normalize
    success_rates = [r['success_rate'] for r in results.values()]
    hit_rates = [r['cache_hit_rate'] for r in results.values()]
    completion_times = [r['avg_completion_time'] for r in results.values()]
    energies = [r['energy_per_task'] for r in results.values()]
    
    for idx, scenario_id in enumerate(results.keys()):
        # Normalize to 0-100 (higher is better)
        norm_success = success_rates[idx]
        norm_hit = hit_rates[idx]
        norm_time = 100 * (1 - (completion_times[idx] - min(completion_times)) / (max(completion_times) - min(completion_times) + 1e-9))
        norm_energy = 100 * (1 - (energies[idx] - min(energies)) / (max(energies) - min(energies) + 1e-9))
        
        metrics_data[scenario_id]['values'] = [norm_success, norm_hit, norm_time, norm_energy]
    
    # Create radar chart
    fig, ax = plt.subplots(figsize=(10, 10), subplot_kw=dict(projection='polar'))
    
    angles = [n / float(len(metric_names)) * 2 * pi for n in range(len(metric_names))]
    angles += angles[:1]
    
    ax.set_theta_offset(pi / 2)
    ax.set_theta_direction(-1)
    ax.set_xticks(angles[:-1])
    ax.set_xticklabels(metric_names, size=11)
    ax.set_ylim(0, 100)
    ax.set_yticks([20, 40, 60, 80, 100])
    ax.set_yticklabels(['20', '40', '60', '80', '100'], size=9)
    ax.grid(True, linestyle='--', alpha=0.7)
    
    # Plot each method
    for scenario_id, data in metrics_data.items():
        values = data['values'] + data['values'][:1]
        ax.plot(angles, values, 'o-', linewidth=2, label=data['name'], color=data['color'])
        ax.fill(angles, values, alpha=0.15, color=data['color'])
    
    ax.legend(loc='upper right', bbox_to_anchor=(1.3, 1.1), fontsize=10)
    plt.title('Multi-Metric Performance Comparison\n(Higher is Better)', 
              size=14, fontweight='bold', pad=20)
    
    radar_file = OUTPUT_DIR / "radar_comparison.png"
    plt.savefig(radar_file, dpi=300, bbox_inches='tight')
    print(f"Radar chart saved to: {radar_file}")
    plt.close()

def main():
    """Main execution."""
    print("="*60)
    print("COMPREHENSIVE CACHING STRATEGY COMPARISON")
    print("="*60)
    
    # Run all experiments
    for scenario_id, scenario_config in SCENARIOS.items():
        run_experiment(scenario_id, scenario_config)
    
    # Collect and analyze results
    print("\n" + "="*60)
    print("COLLECTING RESULTS")
    print("="*60)
    results = collect_results()
    
    if not results:
        print("Error: No results collected!")
        return 1
    
    # Generate comparison table
    df = generate_comparison_table(results)
    
    # Generate plots
    print("\n" + "="*60)
    print("GENERATING VISUALIZATIONS")
    print("="*60)
    generate_plots(results)
    
    # Save detailed results
    detailed_file = OUTPUT_DIR / "detailed_results.json"
    with open(detailed_file, 'w') as f:
        json.dump(results, f, indent=2)
    print(f"\nDetailed results saved to: {detailed_file}")
    
    print("\n" + "="*60)
    print("COMPARISON COMPLETE!")
    print("="*60)
    print(f"All results saved to: {OUTPUT_DIR}")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
