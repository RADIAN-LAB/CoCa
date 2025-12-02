"""Train RL agent for multiple epochs for extended learning.

Usage:
    python scripts/train_rl_multi_epoch.py --epochs 5
"""

import argparse
import json
import subprocess
from pathlib import Path

def train_epoch(trace_file, epoch_num, load_checkpoint=None):
    """Train for one epoch."""
    output_file = f"experiments/results/fl_rl_epoch_{epoch_num}.json"
    checkpoint_file = f"experiments/models/rl_epoch_{epoch_num}.pt"
    
    cmd = [
        "python3", "scripts/run_experiment.py",
        "--trace", trace_file,
        "--output", output_file,
        "--save_rl", checkpoint_file
    ]
    
    if load_checkpoint:
        cmd.extend(["--load_rl", load_checkpoint])
    
    print(f"\n{'='*60}")
    print(f"Training Epoch {epoch_num}")
    print(f"{'='*60}")
    print(f"Command: {' '.join(cmd)}")
    
    result = subprocess.run(cmd, capture_output=True, text=True)
    
    if result.returncode != 0:
        print(f"ERROR in epoch {epoch_num}:")
        print(result.stderr)
        return None
    
    # Parse results
    with open(output_file) as f:
        results = json.load(f)
    
    hits = results['cache_hits']
    misses = results['cache_misses']
    hit_rate = hits / (hits + misses) * 100
    
    print(f"\nEpoch {epoch_num} Results:")
    print(f"  Cache Hits: {hits}")
    print(f"  Hit Rate: {hit_rate:.2f}%")
    print(f"  Success Rate: {results['success_rate']*100:.2f}%")
    print(f"  Runtime: {results['runtime_seconds']:.2f}s")
    print(f"  Checkpoint saved: {checkpoint_file}")
    
    return {
        'epoch': epoch_num,
        'hit_rate': hit_rate,
        'cache_hits': hits,
        'success_rate': results['success_rate'],
        'checkpoint': checkpoint_file,
        'results_file': output_file
    }

def main():
    parser = argparse.ArgumentParser(description='Train RL agent for multiple epochs')
    parser.add_argument('--epochs', type=int, default=5, help='Number of training epochs')
    parser.add_argument('--trace', default='experiments/synthetic/input/tasks.csv',
                       help='Training data trace file')
    args = parser.parse_args()
    
    print(f"Multi-Epoch RL Training")
    print(f"Epochs: {args.epochs}")
    print(f"Dataset: {args.trace}")
    
    results = []
    prev_checkpoint = None
    
    for epoch in range(1, args.epochs + 1):
        epoch_result = train_epoch(args.trace, epoch, prev_checkpoint)
        
        if epoch_result is None:
            print(f"\nTraining stopped at epoch {epoch} due to error")
            break
        
        results.append(epoch_result)
        prev_checkpoint = epoch_result['checkpoint']
    
    # Print summary
    print(f"\n{'='*60}")
    print("TRAINING SUMMARY")
    print(f"{'='*60}")
    print(f"{'Epoch':<8} {'Hit Rate':<12} {'Cache Hits':<12} {'Success Rate':<15}")
    print('-' * 60)
    
    for r in results:
        print(f"{r['epoch']:<8} {r['hit_rate']:<11.2f}% {r['cache_hits']:<12} {r['success_rate']*100:<14.2f}%")
    
    # Find best epoch
    best = max(results, key=lambda x: x['hit_rate'])
    print(f"\n🏆 Best Performance: Epoch {best['epoch']}")
    print(f"   Hit Rate: {best['hit_rate']:.2f}%")
    print(f"   Checkpoint: {best['checkpoint']}")
    
    # Check if improving
    if len(results) >= 2:
        improvement = results[-1]['hit_rate'] - results[0]['hit_rate']
        print(f"\n📈 Improvement: {improvement:+.2f}% (Epoch 1 → Epoch {len(results)})")
    
    # Save summary
    summary_file = Path("experiments/results/multi_epoch_summary.json")
    with open(summary_file, 'w') as f:
        json.dump(results, f, indent=2)
    print(f"\n💾 Summary saved to: {summary_file}")

if __name__ == "__main__":
    main()
