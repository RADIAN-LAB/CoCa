# SUMO Trace Experiment Results

## Experiment Setup

- **Trace**: SUMO-generated FCD trace (5×5 grid network, 200 vehicles, 500s simulation)
- **Total Tasks**: 16,472
- **Unique Cache Keys**: 145 (10 task types × 5 data size buckets × 3 priorities)
- **RSUs**: 5 (at strategic intersections)
- **Cache Capacity**: 100 entries per RSU (500 total, covers ~69% of unique keys per RSU)
- **TTL**: 300 seconds
- **Deadline**: 5ms (dynamic per task type/priority)
- **Computation Overhead**: 25ms base (uncached tasks incur edge computation penalty)

## Architecture Differences

| Feature | No Cache | Baselines (Random/LRU/LFU) | FL-Only | CoCa (FL+RL) |
|---------|----------|---------------------------|---------|---------------|
| Cache Lookup | No | Local RSU only | Local RSU only | Cross-RSU forwarding |
| Auto-Cache | No | Yes | Yes | Yes |
| FL Pre-placement | No | No | No | Yes (predict-then-serve) |
| RL Eviction | No | Fixed policy | Fixed (LFU) | Adaptive DQN |

## Results Summary

| Method | Success Rate | Avg Completion (ms) | Cache Hits | Cache Misses | Hit Rate | Runtime (s) |
|--------|-------------|---------------------|------------|--------------|----------|-------------|
| No Cache | 33.3% | 14.31 | 0 | 0 | N/A | 267.7 |
| Random | 86.5% | 3.24 | 13,016 | 3,456 | 79.0% | 89.0 |
| LRU | 90.8% | 2.99 | 13,921 | 2,551 | 84.5% | 77.3 |
| LFU | 90.8% | 2.99 | 13,921 | 2,551 | 84.5% | 83.5 |
| FL-Only | 90.8% | 2.99 | 13,921 | 2,551 | 84.5% | 74.7 |
| **CoCa (FL+RL)** | **97.4%** | **2.50** | **15,728** | **744** | **95.5%** | **52.8** |

## CoCa Improvements Over Best Baseline

| Metric | Best Baseline | CoCa (FL+RL) | Improvement |
|--------|--------------|---------------|-------------|
| Success Rate | 90.8% (LRU/LFU) | 97.4% | **+6.6 pp** |
| Avg Completion | 2.99ms (LRU) | 2.50ms | **-16.4% faster** |
| Cache Hit Rate | 84.5% (LRU/LFU) | 95.5% | **+11.0 pp** |
| Cache Misses | 2,551 (LRU/LFU) | 744 | **-70.8% fewer misses** |
| Runtime | 74.7s (FL-Only) | 52.8s | **-29.3% faster** |

## CoCa vs No Cache

| Metric | No Cache | CoCa (FL+RL) | Improvement |
|--------|----------|---------------|-------------|
| Success Rate | 33.3% | 97.4% | **+64.1 pp** |
| Avg Completion | 14.31ms | 2.50ms | **-82.5% faster** |

## Key Findings

1. **CoCa dominates all metrics by a wide margin**: 97.4% success rate vs 90.8% for the best baseline (+6.6 pp), with 95.5% cache hit rate vs 84.5% (+11 pp). The gap is substantial and consistent across all metrics.

2. **FL predict-then-serve architecture is the key differentiator**: CoCa pre-places FL-predicted results BEFORE tasks arrive at each timestep. Baselines must compute each unique key at least once per RSU before caching, losing ~15.5% of tasks to cache misses.

3. **Cross-RSU forwarding amplifies CoCa's advantage**: CoCa enables inter-RSU cache sharing, effectively pooling 500 cache slots. Baselines are limited to 100 local slots each, covering only ~69% of the 145 unique keys.

4. **Cache pressure creates meaningful differentiation**: With 145 unique keys and 100 slots per RSU, eviction quality matters. CoCa's RL-driven eviction retains the most valuable entries, achieving 95.5% hit rate vs 84.5% for static LRU/LFU.

5. **Caching is critical for VANET task success**: Without caching, only 33.3% of tasks meet the 5ms deadline. Edge computation overhead (25ms base) makes fresh computation infeasible for most tasks under tight deadlines.

6. **Runtime efficiency scales with hit rate**: CoCa's 95.5% hit rate means far fewer LP solver invocations, resulting in 29-41% faster experiment runtime compared to baselines.
