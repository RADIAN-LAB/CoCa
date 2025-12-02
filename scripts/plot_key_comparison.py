"""Plot focused comparison of key cache eviction policies.

Usage:
    python scripts/plot_key_comparison.py
"""

import json
import matplotlib.pyplot as plt
import numpy as np
from pathlib import Path

def main():
    # Define key results to compare
    results_dir = Path("experiments/results")
    
    key_methods = {
        'FL+RL (Original)': 'baseline_fl_rl.json',
        'FL+RL (Improved)': 'improved_fl_rl.json',
        'FL+RL (Full)': 'improved_fl_rl_full.json',
        'FL+LFU': 'fl_lfu.json',
        'FL+LRU': 'fl_lru.json',
        'FL+Random': 'fl_random.json',
        'FL+FIFO': 'fl_fifo.json',
        'FL Only': 'fl_only.json',
    }
    
    # Load results
    results = {}
    for name, filename in key_methods.items():
        filepath = results_dir / filename
        if filepath.exists():
            with open(filepath) as f:
                results[name] = json.load(f)
    
    if not results:
        print("No results found!")
        return
    
    # Create comprehensive figure
    fig = plt.figure(figsize=(18, 10))
    gs = fig.add_gridspec(2, 3, hspace=0.3, wspace=0.3)
    
    methods = list(results.keys())
    
    # Extract metrics
    hit_rates = []
    success_rates = []
    runtimes = []
    cache_hits = []
    avg_times = []
    
    for method in methods:
        data = results[method]
        hits = data['cache_hits']
        misses = data['cache_misses']
        hit_rates.append(hits / (hits + misses) * 100)
        success_rates.append(data['success_rate'] * 100)
        runtimes.append(data['runtime_seconds'])
        cache_hits.append(hits)
        avg_times.append(data['average_completion'])
    
    # Color scheme
    colors = ['#e74c3c', '#3498db', '#2ecc71', '#f39c12', '#9b59b6', '#1abc9c', '#e67e22', '#95a5a6']
    
    # Plot 1: Hit Rate Comparison
    ax1 = fig.add_subplot(gs[0, 0])
    bars1 = ax1.bar(range(len(methods)), hit_rates, color=colors[:len(methods)], alpha=0.8, edgecolor='black', linewidth=1.5)
    ax1.set_ylabel('Hit Rate (%)', fontsize=12, fontweight='bold')
    ax1.set_title('Cache Hit Rate', fontsize=13, fontweight='bold')
    ax1.set_xticks(range(len(methods)))
    ax1.set_xticklabels(methods, rotation=45, ha='right', fontsize=9)
    ax1.axhline(y=88.1, color='red', linestyle='--', linewidth=2, alpha=0.7, label='Fixed Policy Baseline')
    ax1.grid(axis='y', alpha=0.3, linestyle='--')
    ax1.legend(fontsize=9)
    ax1.set_ylim([85, 100])
    for bar, rate in zip(bars1, hit_rates):
        height = bar.get_height()
        ax1.text(bar.get_x() + bar.get_width()/2., height + 0.5,
                f'{rate:.1f}%', ha='center', va='bottom', fontsize=9, fontweight='bold')
    
    # Plot 2: Success Rate
    ax2 = fig.add_subplot(gs[0, 1])
    bars2 = ax2.bar(range(len(methods)), success_rates, color=colors[:len(methods)], alpha=0.8, edgecolor='black', linewidth=1.5)
    ax2.set_ylabel('Success Rate (%)', fontsize=12, fontweight='bold')
    ax2.set_title('Task Success Rate', fontsize=13, fontweight='bold')
    ax2.set_xticks(range(len(methods)))
    ax2.set_xticklabels(methods, rotation=45, ha='right', fontsize=9)
    ax2.grid(axis='y', alpha=0.3, linestyle='--')
    ax2.set_ylim([80, 85])
    for bar, rate in zip(bars2, success_rates):
        height = bar.get_height()
        ax2.text(bar.get_x() + bar.get_width()/2., height + 0.15,
                f'{rate:.1f}%', ha='center', va='bottom', fontsize=9, fontweight='bold')
    
    # Plot 3: Runtime
    ax3 = fig.add_subplot(gs[0, 2])
    bars3 = ax3.bar(range(len(methods)), runtimes, color=colors[:len(methods)], alpha=0.8, edgecolor='black', linewidth=1.5)
    ax3.set_ylabel('Runtime (seconds)', fontsize=12, fontweight='bold')
    ax3.set_title('Execution Time (Lower is Better)', fontsize=13, fontweight='bold')
    ax3.set_xticks(range(len(methods)))
    ax3.set_xticklabels(methods, rotation=45, ha='right', fontsize=9)
    ax3.grid(axis='y', alpha=0.3, linestyle='--')
    for bar, time in zip(bars3, runtimes):
        height = bar.get_height()
        ax3.text(bar.get_x() + bar.get_width()/2., height + 0.1,
                f'{time:.2f}s', ha='center', va='bottom', fontsize=9, fontweight='bold')
    
    # Plot 4: Cache Hits (absolute numbers)
    ax4 = fig.add_subplot(gs[1, 0])
    bars4 = ax4.bar(range(len(methods)), cache_hits, color=colors[:len(methods)], alpha=0.8, edgecolor='black', linewidth=1.5)
    ax4.set_ylabel('Total Cache Hits', fontsize=12, fontweight='bold')
    ax4.set_title('Absolute Cache Hits', fontsize=13, fontweight='bold')
    ax4.set_xticks(range(len(methods)))
    ax4.set_xticklabels(methods, rotation=45, ha='right', fontsize=9)
    ax4.grid(axis='y', alpha=0.3, linestyle='--')
    for bar, hits in zip(bars4, cache_hits):
        height = bar.get_height()
        ax4.text(bar.get_x() + bar.get_width()/2., height + 20,
                f'{hits}', ha='center', va='bottom', fontsize=9, fontweight='bold')
    
    # Plot 5: Avg Completion Time
    ax5 = fig.add_subplot(gs[1, 1])
    bars5 = ax5.bar(range(len(methods)), avg_times, color=colors[:len(methods)], alpha=0.8, edgecolor='black', linewidth=1.5)
    ax5.set_ylabel('Avg Completion (ms)', fontsize=12, fontweight='bold')
    ax5.set_title('Average Task Completion Time', fontsize=13, fontweight='bold')
    ax5.set_xticks(range(len(methods)))
    ax5.set_xticklabels(methods, rotation=45, ha='right', fontsize=9)
    ax5.grid(axis='y', alpha=0.3, linestyle='--')
    for bar, time in zip(bars5, avg_times):
        height = bar.get_height()
        ax5.text(bar.get_x() + bar.get_width()/2., height + 0.1,
                f'{time:.2f}', ha='center', va='bottom', fontsize=9, fontweight='bold')
    
    # Plot 6: Normalized Performance Score
    ax6 = fig.add_subplot(gs[1, 2])
    # Normalize metrics (higher is better)
    norm_hit = np.array(hit_rates) / max(hit_rates)
    norm_success = np.array(success_rates) / max(success_rates)
    norm_speed = min(runtimes) / np.array(runtimes)  # Inverse for speed
    
    # Weighted score: 50% hit rate, 30% success, 20% speed
    scores = 0.5 * norm_hit + 0.3 * norm_success + 0.2 * norm_speed
    scores = scores * 100
    
    bars6 = ax6.bar(range(len(methods)), scores, color=colors[:len(methods)], alpha=0.8, edgecolor='black', linewidth=1.5)
    ax6.set_ylabel('Overall Score', fontsize=12, fontweight='bold')
    ax6.set_title('Weighted Performance Score', fontsize=13, fontweight='bold')
    ax6.set_xticks(range(len(methods)))
    ax6.set_xticklabels(methods, rotation=45, ha='right', fontsize=9)
    ax6.grid(axis='y', alpha=0.3, linestyle='--')
    for bar, score in zip(bars6, scores):
        height = bar.get_height()
        ax6.text(bar.get_x() + bar.get_width()/2., height + 1,
                f'{score:.1f}', ha='center', va='bottom', fontsize=9, fontweight='bold')
    
    # Add footnote
    fig.text(0.5, 0.02, 'Score = 50% Hit Rate + 30% Success Rate + 20% Speed (normalized)', 
             ha='center', fontsize=10, style='italic', color='gray')
    
    plt.suptitle('Comprehensive Cache Policy Comparison', fontsize=16, fontweight='bold', y=0.98)
    
    output_path = Path("experiments/plots/key_comparison.png")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    print(f"✅ Saved: {output_path}")
    plt.close()
    
    # Also create a simple before/after for FL+RL
    create_improvement_plot(results)

def create_improvement_plot(results):
    """Create before/after plot for FL+RL improvements."""
    fig, axes = plt.subplots(1, 3, figsize=(15, 5))
    
    methods = ['FL+RL (Original)', 'FL+RL (Improved)', 'FL+RL (Full)', 'FL+LFU']
    methods = [m for m in methods if m in results]
    
    if len(methods) < 3:
        print("Not enough FL+RL results for improvement plot")
        return
    
    # Metrics
    hit_rates = []
    success_rates = []
    cache_hits = []
    
    for method in methods:
        data = results[method]
        hits = data['cache_hits']
        misses = data['cache_misses']
        hit_rates.append(hits / (hits + misses) * 100)
        success_rates.append(data['success_rate'] * 100)
        cache_hits.append(hits)
    
    colors = ['#e74c3c', '#f39c12', '#2ecc71', '#3498db']
    
    # Plot 1: Hit Rate Progress
    ax1 = axes[0]
    bars = ax1.bar(range(len(methods)), hit_rates, color=colors[:len(methods)], alpha=0.8, edgecolor='black', linewidth=2)
    ax1.set_ylabel('Hit Rate (%)', fontsize=13, fontweight='bold')
    ax1.set_title('Hit Rate Improvement', fontsize=14, fontweight='bold')
    ax1.set_xticks(range(len(methods)))
    ax1.set_xticklabels(methods, rotation=25, ha='right', fontsize=11)
    ax1.axhline(y=88.1, color='red', linestyle='--', linewidth=2, alpha=0.7)
    ax1.grid(axis='y', alpha=0.3)
    ax1.set_ylim([85, 100])
    for bar, rate in zip(bars, hit_rates):
        height = bar.get_height()
        ax1.text(bar.get_x() + bar.get_width()/2., height + 0.5,
                f'{rate:.1f}%', ha='center', va='bottom', fontsize=11, fontweight='bold')
    
    # Plot 2: Success Rate
    ax2 = axes[1]
    bars = ax2.bar(range(len(methods)), success_rates, color=colors[:len(methods)], alpha=0.8, edgecolor='black', linewidth=2)
    ax2.set_ylabel('Success Rate (%)', fontsize=13, fontweight='bold')
    ax2.set_title('Task Success Rate', fontsize=14, fontweight='bold')
    ax2.set_xticks(range(len(methods)))
    ax2.set_xticklabels(methods, rotation=25, ha='right', fontsize=11)
    ax2.grid(axis='y', alpha=0.3)
    for bar, rate in zip(bars, success_rates):
        height = bar.get_height()
        ax2.text(bar.get_x() + bar.get_width()/2., height + 0.2,
                f'{rate:.1f}%', ha='center', va='bottom', fontsize=11, fontweight='bold')
    
    # Plot 3: Cache Hits
    ax3 = axes[2]
    bars = ax3.bar(range(len(methods)), cache_hits, color=colors[:len(methods)], alpha=0.8, edgecolor='black', linewidth=2)
    ax3.set_ylabel('Total Cache Hits', fontsize=13, fontweight='bold')
    ax3.set_title('Absolute Cache Hits', fontsize=14, fontweight='bold')
    ax3.set_xticks(range(len(methods)))
    ax3.set_xticklabels(methods, rotation=25, ha='right', fontsize=11)
    ax3.grid(axis='y', alpha=0.3)
    for bar, hits in zip(bars, cache_hits):
        height = bar.get_height()
        ax3.text(bar.get_x() + bar.get_width()/2., height + 30,
                f'{hits}', ha='center', va='bottom', fontsize=11, fontweight='bold')
    
    plt.suptitle('FL+RL Performance Evolution', fontsize=16, fontweight='bold')
    plt.tight_layout()
    
    output_path = Path("experiments/plots/fl_rl_improvement.png")
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    print(f"✅ Saved: {output_path}")
    plt.close()

if __name__ == "__main__":
    main()
