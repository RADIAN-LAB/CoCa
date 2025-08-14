"""Analyze and visualize benchmark results."""
import json
import matplotlib.pyplot as plt
import pandas as pd
from pathlib import Path

def load_results(results_dir: str) -> dict:
    """Load results from JSON files in the given directory."""
    results = {}
    for json_file in Path(results_dir).glob("*.json"):
        with open(json_file) as f:
            results[json_file.stem] = json.load(f)
    return results

def plot_metrics(results: dict, output_dir: str):
    """Generate plots for cache performance metrics."""
    # Convert to DataFrame for easier plotting
    df = pd.DataFrame.from_dict(results, orient='index')
    
    # Plot cache hit/miss ratio
    plt.figure(figsize=(12, 6))
    df[['cache_hits', 'cache_misses']].plot(kind='bar', stacked=True)
    plt.title('Cache Performance')
    plt.ylabel('Count')
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.savefig(f"{output_dir}/cache_performance.png")
    
    # Plot success rate and completion time
    fig, ax1 = plt.subplots(figsize=(12, 6))
    
    color = 'tab:blue'
    ax1.set_xlabel('Run')
    ax1.set_ylabel('Success Rate', color=color)
    ax1.plot(df.index, df['success_rate'], 'o-', color=color)
    ax1.tick_params(axis='y', labelcolor=color)
    
    ax2 = ax1.twinx()
    color = 'tab:red'
    ax2.set_ylabel('Avg Completion Time (s)', color=color)
    ax2.plot(df.index, df['average_completion'], 's-', color=color)
    ax2.tick_params(axis='y', labelcolor=color)
    
    plt.title('Success Rate vs Completion Time')
    fig.tight_layout()
    plt.savefig(f"{output_dir}/performance_metrics.png")

def main():
    import argparse
    
    parser = argparse.ArgumentParser(description='Analyze benchmark results')
    parser.add_argument('--results-dir', default='experiments/synthetic/output',
                      help='Directory containing result JSON files')
    parser.add_argument('--output-dir', default='experiments/synthetic/plots',
                      help='Directory to save output plots')
    
    args = parser.parse_args()
    
    # Create output directory if it doesn't exist
    Path(args.output_dir).mkdir(parents=True, exist_ok=True)
    
    # Load and analyze results
    results = load_results(args.results_dir)
    
    if not results:
        print(f"No JSON files found in {args.results_dir}")
        return
    
    print(f"Loaded {len(results)} result files")
    print("\nSummary:")
    print(pd.DataFrame.from_dict(results, orient='index').to_string())
    
    # Generate plots
    plot_metrics(results, args.output_dir)
    print(f"\nPlots saved to {args.output_dir}")

if __name__ == "__main__":
    main()
