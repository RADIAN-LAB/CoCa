"""Plot comprehensive comparison of all cache eviction policies.

Usage:
    python scripts/plot_comparison.py --results experiments/results --output experiments/plots
"""

import json
import matplotlib.pyplot as plt
import numpy as np
from pathlib import Path
import argparse

def load_all_results(results_dir):
    """Load all result JSON files."""
    results = {}
    results_path = Path(results_dir)
    
    # Map filenames to display names
    name_mapping = {
        'baseline_fl_rl': 'FL+RL (Original)',
        'improved_fl_rl': 'FL+RL (Improved 51)',
        'improved_fl_rl_full': 'FL+RL (Improved 200)',
        'fl_lfu': 'FL+LFU',
        'fl_lru': 'FL+LRU',
        'fl_random': 'FL+Random',
        'fl_only': 'FL Only',
        'fl_fifo': 'FL+FIFO',
    }
    
    for json_file in results_path.glob("*.json"):
        key = json_file.stem
        display_name = name_mapping.get(key, key)
        with open(json_file) as f:
            data = json.load(f)
            # Skip if data is a list (like multi_epoch_summary.json)
            if isinstance(data, list):
                continue
            results[display_name] = data
    
    return results

def plot_hit_rate_comparison(results, output_dir):
    """Bar chart comparing cache hit rates."""
    fig, ax = plt.subplots(figsize=(12, 6))
    
    methods = list(results.keys())
    hit_rates = []
    colors = []
    
    for method in methods:
        data = results[method]
        hits = data['cache_hits']
        misses = data['cache_misses']
        hit_rate = hits / (hits + misses) * 100
        hit_rates.append(hit_rate)
        
        # Color code by performance
        if 'Improved 200' in method:
            colors.append('#2ecc71')  # Green for best
        elif hit_rate > 88:
            colors.append('#3498db')  # Blue for good
        elif hit_rate > 87.5:
            colors.append('#f39c12')  # Orange for okay
        else:
            colors.append('#e74c3c')  # Red for poor
    
    bars = ax.bar(range(len(methods)), hit_rates, color=colors, alpha=0.8, edgecolor='black')
    
    # Add value labels on bars
    for i, (bar, rate) in enumerate(zip(bars, hit_rates)):
        height = bar.get_height()
        ax.text(bar.get_x() + bar.get_width()/2., height,
                f'{rate:.1f}%',
                ha='center', va='bottom', fontweight='bold', fontsize=10)
    
    ax.set_ylabel('Cache Hit Rate (%)', fontsize=12, fontweight='bold')
    ax.set_xlabel('Method', fontsize=12, fontweight='bold')
    ax.set_title('Cache Hit Rate Comparison', fontsize=14, fontweight='bold')
    ax.set_xticks(range(len(methods)))
    ax.set_xticklabels(methods, rotation=45, ha='right')
    ax.set_ylim([85, 100])
    ax.grid(axis='y', alpha=0.3, linestyle='--')
    ax.axhline(y=88.1, color='red', linestyle='--', linewidth=2, label='Fixed Policy Baseline (88.1%)')
    ax.legend(loc='lower right')
    
    plt.tight_layout()
    plt.savefig(f"{output_dir}/hit_rate_comparison.png", dpi=300, bbox_inches='tight')
    print(f"Saved: {output_dir}/hit_rate_comparison.png")
    plt.close()

def plot_success_rate_comparison(results, output_dir):
    """Bar chart comparing task success rates."""
    fig, ax = plt.subplots(figsize=(12, 6))
    
    methods = list(results.keys())
    success_rates = [results[m]['success_rate'] * 100 for m in methods]
    
    bars = ax.bar(range(len(methods)), success_rates, color='#9b59b6', alpha=0.8, edgecolor='black')
    
    # Add value labels
    for bar, rate in zip(bars, success_rates):
        height = bar.get_height()
        ax.text(bar.get_x() + bar.get_width()/2., height,
                f'{rate:.1f}%',
                ha='center', va='bottom', fontweight='bold', fontsize=10)
    
    ax.set_ylabel('Task Success Rate (%)', fontsize=12, fontweight='bold')
    ax.set_xlabel('Method', fontsize=12, fontweight='bold')
    ax.set_title('Task Success Rate Comparison', fontsize=14, fontweight='bold')
    ax.set_xticks(range(len(methods)))
    ax.set_xticklabels(methods, rotation=45, ha='right')
    ax.set_ylim([80, 85])
    ax.grid(axis='y', alpha=0.3, linestyle='--')
    
    plt.tight_layout()
    plt.savefig(f"{output_dir}/success_rate_comparison.png", dpi=300, bbox_inches='tight')
    print(f"Saved: {output_dir}/success_rate_comparison.png")
    plt.close()

def plot_runtime_comparison(results, output_dir):
    """Bar chart comparing runtime efficiency."""
    fig, ax = plt.subplots(figsize=(12, 6))
    
    methods = list(results.keys())
    runtimes = [results[m]['runtime_seconds'] for m in methods]
    
    # Color by speed
    colors = ['#2ecc71' if r < 3.0 else '#3498db' if r < 3.5 else '#f39c12' if r < 4.0 else '#e74c3c' 
              for r in runtimes]
    
    bars = ax.bar(range(len(methods)), runtimes, color=colors, alpha=0.8, edgecolor='black')
    
    # Add value labels
    for bar, time in zip(bars, runtimes):
        height = bar.get_height()
        ax.text(bar.get_x() + bar.get_width()/2., height,
                f'{time:.2f}s',
                ha='center', va='bottom', fontweight='bold', fontsize=10)
    
    ax.set_ylabel('Runtime (seconds)', fontsize=12, fontweight='bold')
    ax.set_xlabel('Method', fontsize=12, fontweight='bold')
    ax.set_title('Runtime Comparison (Lower is Better)', fontsize=14, fontweight='bold')
    ax.set_xticks(range(len(methods)))
    ax.set_xticklabels(methods, rotation=45, ha='right')
    ax.grid(axis='y', alpha=0.3, linestyle='--')
    
    plt.tight_layout()
    plt.savefig(f"{output_dir}/runtime_comparison.png", dpi=300, bbox_inches='tight')
    print(f"Saved: {output_dir}/runtime_comparison.png")
    plt.close()

def plot_combined_metrics(results, output_dir):
    """Multi-metric comparison plot."""
    fig, axes = plt.subplots(2, 2, figsize=(16, 12))
    
    methods = list(results.keys())
    
    # Extract metrics
    hit_rates = []
    success_rates = []
    completion_times = []
    cache_hits = []
    
    for method in methods:
        data = results[method]
        hits = data['cache_hits']
        misses = data['cache_misses']
        hit_rates.append(hits / (hits + misses) * 100)
        success_rates.append(data['success_rate'] * 100)
        completion_times.append(data['average_completion'])
        cache_hits.append(hits)
    
    # Plot 1: Hit Rate
    ax1 = axes[0, 0]
    colors1 = ['#2ecc71' if h > 95 else '#3498db' if h > 88 else '#f39c12' for h in hit_rates]
    bars1 = ax1.bar(range(len(methods)), hit_rates, color=colors1, alpha=0.8, edgecolor='black')
    ax1.set_ylabel('Hit Rate (%)', fontweight='bold')
    ax1.set_title('Cache Hit Rate', fontweight='bold', fontsize=12)
    ax1.set_xticks(range(len(methods)))
    ax1.set_xticklabels(methods, rotation=45, ha='right', fontsize=8)
    ax1.grid(axis='y', alpha=0.3)
    for bar, rate in zip(bars1, hit_rates):
        ax1.text(bar.get_x() + bar.get_width()/2., bar.get_height(),
                f'{rate:.1f}%', ha='center', va='bottom', fontsize=8)
    
    # Plot 2: Success Rate
    ax2 = axes[0, 1]
    bars2 = ax2.bar(range(len(methods)), success_rates, color='#9b59b6', alpha=0.8, edgecolor='black')
    ax2.set_ylabel('Success Rate (%)', fontweight='bold')
    ax2.set_title('Task Success Rate', fontweight='bold', fontsize=12)
    ax2.set_xticks(range(len(methods)))
    ax2.set_xticklabels(methods, rotation=45, ha='right', fontsize=8)
    ax2.grid(axis='y', alpha=0.3)
    for bar, rate in zip(bars2, success_rates):
        ax2.text(bar.get_x() + bar.get_width()/2., bar.get_height(),
                f'{rate:.1f}%', ha='center', va='bottom', fontsize=8)
    
    # Plot 3: Completion Time
    ax3 = axes[1, 0]
    bars3 = ax3.bar(range(len(methods)), completion_times, color='#e67e22', alpha=0.8, edgecolor='black')
    ax3.set_ylabel('Avg Completion Time (ms)', fontweight='bold')
    ax3.set_title('Average Completion Time', fontweight='bold', fontsize=12)
    ax3.set_xticks(range(len(methods)))
    ax3.set_xticklabels(methods, rotation=45, ha='right', fontsize=8)
    ax3.grid(axis='y', alpha=0.3)
    for bar, time in zip(bars3, completion_times):
        ax3.text(bar.get_x() + bar.get_width()/2., bar.get_height(),
                f'{time:.2f}', ha='center', va='bottom', fontsize=8)
    
    # Plot 4: Total Cache Hits
    ax4 = axes[1, 1]
    colors4 = ['#2ecc71' if h > 2500 else '#3498db' if h > 645 else '#f39c12' for h in cache_hits]
    bars4 = ax4.bar(range(len(methods)), cache_hits, color=colors4, alpha=0.8, edgecolor='black')
    ax4.set_ylabel('Total Cache Hits', fontweight='bold')
    ax4.set_title('Total Cache Hits', fontweight='bold', fontsize=12)
    ax4.set_xticks(range(len(methods)))
    ax4.set_xticklabels(methods, rotation=45, ha='right', fontsize=8)
    ax4.grid(axis='y', alpha=0.3)
    for bar, hits in zip(bars4, cache_hits):
        ax4.text(bar.get_x() + bar.get_width()/2., bar.get_height(),
                f'{hits}', ha='center', va='bottom', fontsize=8)
    
    plt.suptitle('Comprehensive Performance Comparison', fontsize=16, fontweight='bold', y=0.995)
    plt.tight_layout()
    plt.savefig(f"{output_dir}/combined_metrics.png", dpi=300, bbox_inches='tight')
    print(f"Saved: {output_dir}/combined_metrics.png")
    plt.close()

def plot_performance_radar(results, output_dir):
    """Radar chart comparing normalized metrics - 3 key dimensions."""
    # Select top methods to avoid clutter - only show improved RL, not original
    selected = ['FL+RL (Improved 200)', 'FL+LFU', 'FL+LRU', 'FL+FIFO']
    selected_results = {k: v for k, v in results.items() if k in selected}
    
    if not selected_results:
        print("Not enough methods for radar chart, using all available")
        selected_results = results
    
    fig, ax = plt.subplots(figsize=(10, 10), subplot_kw=dict(projection='polar'))
    
    # Three distinct performance dimensions
    categories = ['Cache\nHit Rate', 'Response\nSpeed', 'Energy\nEfficiency']
    N = len(categories)
    angles = [n / float(N) * 2 * np.pi for n in range(N)]
    angles += angles[:1]
    
    ax.set_theta_offset(np.pi / 2)
    ax.set_theta_direction(-1)
    ax.set_xticks(angles[:-1])
    ax.set_xticklabels(categories, fontsize=13, fontweight='bold')
    
    colors = ['#2ecc71', '#3498db', '#e74c3c', '#f39c12']
    
    # Calculate energy efficiency scores
    # Energy model: Fixed policies are more efficient (simple operations)
    # RL methods consume more energy (neural network inference)
    # Energy efficiency = (performance / energy_cost)
    energy_scores = {}
    for method, data in results.items():
        # Base energy cost from runtime
        base_cost = data['runtime_seconds']
        # RL methods have additional computational cost (NN inference)
        if 'RL' in method:
            computational_overhead = 1.5  # 50% more energy for NN operations
        else:
            computational_overhead = 1.0  # Fixed policies: simple lookups
        
        total_energy_cost = base_cost * computational_overhead
        # Energy efficiency: cache hits per unit energy
        efficiency = (data['cache_hits'] / total_energy_cost)
        energy_scores[method] = efficiency
    
    max_energy_efficiency = max(energy_scores.values())
    
    # Find min/max response time for normalization (lower is better)
    response_times = {m: d['average_completion'] for m, d in results.items()}
    min_response = min(response_times.values())
    max_response = max(response_times.values())
    
    for idx, (method, data) in enumerate(selected_results.items()):
        hits = data['cache_hits']
        misses = data['cache_misses']
        hit_rate = hits / (hits + misses)  # 0-1 scale
        # Response time: invert so lower time = higher score (0-1 scale)
        response_score = 1.0 - ((data['average_completion'] - min_response) / (max_response - min_response + 1e-9))
        energy_efficiency = energy_scores[method] / max_energy_efficiency  # Normalized 0-1
        
        values = [hit_rate, response_score, energy_efficiency]
        values += values[:1]
        
        ax.plot(angles, values, 'o-', linewidth=3, markersize=10, 
                label=method, color=colors[idx % len(colors)],
                markeredgecolor='black', markeredgewidth=1.5)
        ax.fill(angles, values, alpha=0.2, color=colors[idx % len(colors)])
    
    ax.set_ylim(0, 1)
    ax.set_yticks([0.2, 0.4, 0.6, 0.8, 1.0])
    ax.set_yticklabels(['20%', '40%', '60%', '80%', '100%'], fontsize=10)
    ax.legend(loc='upper right', bbox_to_anchor=(1.3, 1.1), fontsize=11, framealpha=0.9)
    ax.set_title('Three-Dimensional Performance Comparison', fontsize=15, fontweight='bold', pad=20)
    ax.grid(True, linestyle='--', alpha=0.7)
    
    plt.tight_layout()
    plt.savefig(f"{output_dir}/performance_radar.png", dpi=300, bbox_inches='tight')
    print(f"Saved: {output_dir}/performance_radar.png")
    plt.close()

def create_summary_table(results, output_dir):
    """Create a visual summary table."""
    fig, ax = plt.subplots(figsize=(14, len(results) * 0.6 + 1))
    ax.axis('tight')
    ax.axis('off')
    
    # Prepare data
    methods = list(results.keys())
    table_data = []
    
    for method in methods:
        data = results[method]
        hits = data['cache_hits']
        misses = data['cache_misses']
        hit_rate = hits / (hits + misses) * 100
        success_rate = data['success_rate'] * 100
        avg_time = data['average_completion']
        runtime = data['runtime_seconds']
        
        table_data.append([
            method,
            f"{hits}",
            f"{hit_rate:.1f}%",
            f"{success_rate:.1f}%",
            f"{avg_time:.2f} ms",
            f"{runtime:.2f} s"
        ])
    
    # Create table
    headers = ['Method', 'Cache Hits', 'Hit Rate', 'Success Rate', 'Avg Time', 'Runtime']
    table = ax.table(cellText=table_data, colLabels=headers, cellLoc='center', loc='center')
    
    # Style table
    table.auto_set_font_size(False)
    table.set_fontsize(10)
    table.scale(1, 2)
    
    # Color header
    for i in range(len(headers)):
        table[(0, i)].set_facecolor('#3498db')
        table[(0, i)].set_text_props(weight='bold', color='white')
    
    # Alternate row colors
    for i in range(1, len(table_data) + 1):
        for j in range(len(headers)):
            if i % 2 == 0:
                table[(i, j)].set_facecolor('#ecf0f1')
            
            # Highlight best values
            if j == 2:  # Hit rate
                val = float(table_data[i-1][j].strip('%'))
                if val > 95:
                    table[(i, j)].set_facecolor('#2ecc71')
                    table[(i, j)].set_text_props(weight='bold')
    
    plt.title('Performance Summary Table', fontsize=14, fontweight='bold', pad=20)
    plt.savefig(f"{output_dir}/summary_table.png", dpi=300, bbox_inches='tight')
    print(f"Saved: {output_dir}/summary_table.png")
    plt.close()

def main():
    parser = argparse.ArgumentParser(description='Plot comparison of all cache policies')
    parser.add_argument('--results', default='experiments/results',
                       help='Directory containing result JSON files')
    parser.add_argument('--output', default='experiments/plots',
                       help='Output directory for plots')
    args = parser.parse_args()
    
    # Create output directory
    output_dir = Path(args.output)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Load results
    print(f"Loading results from {args.results}...")
    results = load_all_results(args.results)
    
    if not results:
        print(f"No results found in {args.results}")
        return
    
    print(f"Found {len(results)} result files")
    print(f"Methods: {', '.join(results.keys())}\n")
    
    # Generate all plots
    print("Generating plots...")
    plot_hit_rate_comparison(results, output_dir)
    plot_success_rate_comparison(results, output_dir)
    plot_runtime_comparison(results, output_dir)
    plot_combined_metrics(results, output_dir)
    plot_performance_radar(results, output_dir)
    create_summary_table(results, output_dir)
    
    print(f"\n✅ All plots saved to {output_dir}/")
    print("\nGenerated files:")
    print("  - hit_rate_comparison.png")
    print("  - success_rate_comparison.png")
    print("  - runtime_comparison.png")
    print("  - combined_metrics.png")
    print("  - performance_radar.png")
    print("  - summary_table.png")

if __name__ == "__main__":
    main()
