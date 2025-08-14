# API Reference

## Cache Module

### CacheManager

The core cache management system with LFU eviction and TTL enforcement.

#### Constructor
```python
CacheManager(capacity: int = 1000, default_ttl: int = 300)
```

**Parameters:**
- `capacity`: Maximum number of entries in cache
- `default_ttl`: Default time-to-live in seconds

#### Methods

##### `lookup(key: str) -> Any | None`
Retrieve cached value if present and fresh.

**Returns:** Cached value or None if miss/expired

##### `store(key: str, value: Any, ttl: int | None = None) -> None`
Insert or update cache entry.

**Parameters:**
- `key`: Cache key identifier
- `value`: Value to cache
- `ttl`: Custom TTL (uses default if None)

##### `evict_lru() -> None`
Evict least recently used entry.

##### `evict_lfu() -> None`
Evict least frequently used entry.

##### `evict_random() -> None`
Evict random entry.

##### `shrink_ttl(factor: float = 0.5) -> None`
Multiply remaining TTL of all entries by factor.

##### `preplace(key: str, ttl: int | None = None) -> None`
Reserve cache space with placeholder value.

##### `stats() -> Tuple[int, int]`
Get hit and miss counts.

### FLAdvisor

Federated learning agent for cache pre-placement decisions.

#### Constructor
```python
FLAdvisor(max_pool_size: int = 500, lr: float = 0.01, round_freq: int = 20)
```

**Parameters:**
- `max_pool_size`: Maximum cache pool size
- `lr`: Learning rate for optimizer
- `round_freq`: FedAvg round frequency

#### Methods

##### `observe_tasks(items: List[tuple[str, dict]]) -> None`
Observe tasks for frequency tracking and feature extraction.

**Parameters:**
- `items`: List of (cache_key, task_attributes) tuples

##### `observe_cache_result(key: str, hit: bool) -> None`
Record cache hit/miss for supervised learning.

##### `select_pool() -> List[str]`
Select top-K cache keys by popularity score.

**Returns:** List of cache keys to pre-place

##### `maybe_fedavg_round() -> None`
Execute federated averaging and local training step.

### RLAgent

Reinforcement learning agent for dynamic cache eviction.

#### Constructor
```python
RLAgent(state_dim: int = 9, gamma: float = 0.95, lr: float = 1e-3, batch_size: int = 32)
```

**Parameters:**
- `state_dim`: State vector dimension
- `gamma`: Discount factor
- `lr`: Learning rate
- `batch_size`: Training batch size

#### Methods

##### `decide(state: Dict[str, Any]) -> str`
Choose action based on current state.

**Parameters:**
- `state`: State dictionary with required keys

**Returns:** Action string from {"noop", "evict_lru", "evict_random", "evict_lfu", "shrink_ttl"}

##### `observe(state: Dict, action: str, reward: float, next_state: Dict) -> None`
Store experience and potentially train.

##### `train_step() -> None`
Execute one DQN training step if sufficient experience.

## SDN Core Module

### task_scheduling

Main scheduling function using MILP optimization.

```python
task_scheduling(
    tasks: List[Tuple[int, int, int, int]], 
    delay_edge_rsu: float,
    delay_rsu_rsu: float, 
    delay_car_car: float
) -> Tuple[int, float]
```

**Parameters:**
- `tasks`: List of (node_id, task_id, fog_rsu, final_rsu) tuples
- `delay_edge_rsu`: Edge to RSU delay
- `delay_rsu_rsu`: RSU to RSU delay  
- `delay_car_car`: Car to car delay

**Returns:** (successful_tasks, average_completion_time)

## Scripts Module

### run_experiment.py

Main experiment runner with FL+RL integration.

```bash
python scripts/run_experiment.py --trace <path> --output <path>
```

**Arguments:**
- `--trace`: Path to input CSV trace file
- `--output`: Path for output JSON results

### generate_synthetic_trace.py

Synthetic trace generator with configurable parameters.

```bash
DECAY_LAMBDA=0.2 python scripts/generate_synthetic_trace.py
```

**Environment Variables:**
- `DECAY_LAMBDA`: Popularity decay rate (default: 0.05)

### tune_decay.py

Parameter optimization script for decay rate.

```bash
python scripts/tune_decay.py
```

Automatically tests λ ∈ {0.01, 0.02, 0.05, 0.1, 0.2} and reports optimal value.

## Configuration

### Cache Configuration (config/cache.yaml)

```yaml
cache:
  capacity: 1000
  default_ttl: 300
  eviction_policy: "LFU"

logging:
  level: "INFO"
  cache_stats: true
```

## Data Formats

### Task Trace CSV

Required columns:
- `timestamp`: Integer timestep
- `node_id`: Vehicle identifier
- `task_id`: Unique task ID
- `task_type`: Task category (0-3)
- `priority`: Urgency level (0-3)
- `data_size_kB`: Payload size
- `origin_rsu`: Source RSU
- `destination_rsu`: Target RSU
- `fog_rsu`: Processing RSU
- `final_rsu`: Result delivery RSU
- `veh_speed_kmh`: Vehicle speed
- `veh_dir_deg`: Movement direction
- `rsu_load`: RSU load factor (0-1)
- `pop_decay`: Popularity decay factor

### Experiment Results JSON

```json
{
  "total_tasks": 2982,
  "success_rate": 1.0,
  "average_completion": 2.27,
  "cache_hits": 4515,
  "cache_misses": 1449,
  "runtime_seconds": 33.2
}
```

## Feature Vectors

### FL Advisor Features (12D)

1. Normalized frequency
2. Log-scaled frequency
3. Normalized priority
4. Normalized data size
5. Locality flag
6. Normalized vehicle speed
7. RSU load
8. Popularity decay
9-12. One-hot task type encoding

### RL Agent State (9D)

1. Cache usage ratio
2. Hit rate
3. Average completion time
4. Mean priority
5. Mean size
6. Locality ratio
7. Mean speed
8. Mean RSU load
9. Mean popularity decay

## Error Handling

### Common Exceptions

- `KeyError`: Missing required state/task attributes
- `ValueError`: Invalid parameter ranges
- `RuntimeError`: MILP solver failures
- `FileNotFoundError`: Missing trace/config files

### Debugging

Enable detailed logging:
```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

Monitor cache statistics:
```python
hits, misses = cache_manager.stats()
hit_rate = hits / (hits + misses)
```

Track FL training progress:
```python
# Check experiments/logs/fl_training.csv
# Columns: timestamp, cache_hits, cache_misses, fl_loss
```
