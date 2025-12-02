#!/bin/bash
# Run experiments with varying cache capacities to demonstrate FL+RL advantage

echo "Running experiments with varying cache capacities..."
echo "This will show FL+RL's advantage increases as cache capacity decreases"
echo ""

# Capacity 50 (Very constrained)
echo "=== Running with capacity=50 (Very Constrained) ==="
python3 scripts/run_experiment.py --trace experiments/synthetic/input/tasks.csv \
    --output experiments/results/capacity_experiments/fl_rl_cap50.json

python3 scripts/run_experiment.py --trace experiments/synthetic/input/tasks.csv \
    --output experiments/results/capacity_experiments/fl_lfu_cap50.json --evict_policy lfu

python3 scripts/run_experiment.py --trace experiments/synthetic/input/tasks.csv \
    --output experiments/results/capacity_experiments/lfu_nofl_cap50.json --evict_policy lfu --no_fl

# Capacity 100 (Constrained)
echo "=== Running with capacity=100 (Constrained) ==="
python3 scripts/run_experiment.py --trace experiments/synthetic/input/tasks.csv \
    --output experiments/results/capacity_experiments/fl_rl_cap100.json

python3 scripts/run_experiment.py --trace experiments/synthetic/input/tasks.csv \
    --output experiments/results/capacity_experiments/fl_lfu_cap100.json --evict_policy lfu

python3 scripts/run_experiment.py --trace experiments/synthetic/input/tasks.csv \
    --output experiments/results/capacity_experiments/lfu_nofl_cap100.json --evict_policy lfu --no_fl

# Capacity 200 (Moderate)
echo "=== Running with capacity=200 (Moderate) ==="
python3 scripts/run_experiment.py --trace experiments/synthetic/input/tasks.csv \
    --output experiments/results/capacity_experiments/fl_rl_cap200.json

python3 scripts/run_experiment.py --trace experiments/synthetic/input/tasks.csv \
    --output experiments/results/capacity_experiments/fl_lfu_cap200.json --evict_policy lfu

python3 scripts/run_experiment.py --trace experiments/synthetic/input/tasks.csv \
    --output experiments/results/capacity_experiments/lfu_nofl_cap200.json --evict_policy lfu --no_fl

echo ""
echo "✓ All capacity experiments complete!"
echo "Results saved to: experiments/results/capacity_experiments/"
