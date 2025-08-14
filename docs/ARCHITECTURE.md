# Architecture Overview

## System Design

The VANET SDN Scheduler implements a modular architecture with clear separation of concerns:

```
┌─────────────────────────────────────────────────────────────────┐
│                    Experiment Controller                        │
│  ┌─────────────────────────────────────────────────────────────┐│
│  │              scripts/run_experiment.py                     ││
│  │  • Orchestrates FL+RL+SDN integration                      ││
│  │  • Manages timestep-based simulation                       ││
│  │  • Collects performance metrics                            ││
│  └─────────────────────────────────────────────────────────────┘│
└─────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│                     Learning Layer                              │
│  ┌──────────────────┐    ┌──────────────────┐                  │
│  │   FL Advisor     │    │    RL Agent      │                  │
│  │                  │    │                  │                  │
│  │ • 12D Features   │    │ • 9D State       │                  │
│  │ • PyTorch MLP    │    │ • DQN Policy     │                  │
│  │ • FedAvg Sim     │    │ • 5 Actions      │                  │
│  │ • Cache Pool     │    │ • Experience     │                  │
│  └──────────────────┘    └──────────────────┘                  │
└─────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│                     Cache Layer                                 │
│  ┌─────────────────────────────────────────────────────────────┐│
│  │                 cache/manager.py                            ││
│  │  • LFU/LRU eviction policies                               ││
│  │  • TTL-based expiration                                    ││
│  │  • Frequency tracking                                      ││
│  │  • Hit/miss statistics                                     ││
│  │  • Pre-placement support                                   ││
│  └─────────────────────────────────────────────────────────────┘│
└─────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│                      SDN Core                                   │
│  ┌─────────────────────────────────────────────────────────────┐│
│  │                sdn_core/scheduler.py                        ││
│  │  • MILP-based task scheduling                              ││
│  │  • Hard deadline constraints                               ││
│  │  • Knapsack optimization                                   ││
│  │  • Success rate calculation                                ││
│  └─────────────────────────────────────────────────────────────┘│
└─────────────────────────────────────────────────────────────────┘
```

## Data Flow

### 1. Initialization Phase
```
Trace Loading → Feature Extraction → Agent Initialization
     ↓                ↓                      ↓
   CSV File    Task Attributes        FL/RL Models
```

### 2. Per-Timestep Execution
```
1. Task Observation
   ├── FL Advisor observes (key, task_attributes)
   └── Frequency tracking updated

2. FL Pre-placement
   ├── Feature vector construction (12D)
   ├── MLP inference for popularity scores
   └── Top-K cache pool selection

3. RL State Assessment
   ├── Aggregate workload statistics
   ├── Cache state monitoring
   └── 9D state vector construction

4. RL Action Selection
   ├── DQN policy inference
   ├── ε-greedy exploration
   └── Action execution on cache

5. SDN Scheduling
   ├── Cache lookup for each task
   ├── MILP optimization
   └── Task assignment decisions

6. Learning Updates
   ├── FL: Cache hit/miss labeling
   ├── RL: Experience storage
   └── Model training steps
```

## Module Dependencies

```
scripts/
├── run_experiment.py
│   ├── cache.manager (CacheManager singleton)
│   ├── cache.fl_agent (FLAdvisor)
│   ├── cache.rl_agent (RLAgent)
│   └── sdn_core.scheduler (task_scheduling)
│
├── generate_synthetic_trace.py
│   └── Independent trace generation
│
└── tune_decay.py
    ├── os.environ (DECAY_LAMBDA)
    └── run_experiment.py (subprocess)

cache/
├── manager.py
│   ├── collections.OrderedDict
│   └── time (TTL management)
│
├── fl_agent.py
│   ├── torch.nn (MLP architecture)
│   ├── torch.optim (Adam optimizer)
│   └── math (logarithmic features)
│
└── rl_agent.py
    ├── torch.nn (DQN architecture)
    ├── collections.deque (replay buffer)
    └── random (ε-greedy policy)

sdn_core/
├── scheduler.py
│   ├── pulp (MILP solver)
│   └── cache.manager (cache lookup)
│
└── routing.py
    └── Network utilities
```

## Design Patterns

### 1. Singleton Pattern
- `CacheManager` uses singleton to ensure consistent state across modules
- Prevents cache inconsistencies from multiple instances

### 2. Strategy Pattern
- Multiple eviction policies (LRU, LFU, Random, Aging)
- Configurable through action selection

### 3. Observer Pattern
- FL Advisor observes task patterns
- RL Agent observes state transitions
- Cache Manager notifies hit/miss events

### 4. Template Method Pattern
- Experiment loop defines execution template
- Specific algorithms implement learning steps

## Configuration Management

### Hierarchical Configuration
```yaml
# config/cache.yaml
cache:
  capacity: 1000
  default_ttl: 300
  eviction_policy: "LFU"

fl_advisor:
  max_pool_size: 500
  learning_rate: 0.01
  round_frequency: 20

rl_agent:
  state_dim: 9
  gamma: 0.95
  learning_rate: 0.001
  batch_size: 32
  epsilon: 0.1

logging:
  level: "INFO"
  cache_stats: true
  fl_progress: true
```

### Environment Variables
- `DECAY_LAMBDA`: Popularity decay rate
- `PYTHONPATH`: Module path resolution

## Performance Considerations

### Memory Management
- **Cache capacity limits**: Prevents unbounded growth
- **Experience replay buffer**: Fixed-size deque for RL
- **Batch processing**: Efficient tensor operations

### Computational Complexity
- **FL inference**: O(F) where F = feature dimension
- **RL decision**: O(S×A) where S = state dim, A = action space
- **Cache operations**: O(log C) for most operations
- **MILP solving**: Depends on problem size and solver

### Scalability Factors
- **Number of vehicles**: Linear impact on task generation
- **Cache capacity**: Affects memory and lookup time
- **Feature dimensions**: Impacts ML model complexity
- **Trace length**: Determines total runtime

## Error Handling Strategy

### Graceful Degradation
```python
# FL Advisor fallback
if not self._freq:
    return []  # Empty pool selection

# RL Agent fallback  
if len(self.replay_buffer) < self.batch_size:
    return random.choice(self.actions)  # Random action

# Cache Manager fallback
if key not in self._store:
    return None  # Cache miss
```

### Exception Propagation
- **Configuration errors**: Fail fast at startup
- **Runtime errors**: Log and continue with defaults
- **Solver failures**: Retry with relaxed constraints

## Testing Strategy

### Unit Tests
- Individual component functionality
- Mock dependencies for isolation
- Edge case handling

### Integration Tests
- End-to-end experiment execution
- Cross-module communication
- Performance regression detection

### Validation Tests
- Parameter sensitivity analysis
- Convergence behavior verification
- Comparative benchmarking

## Extensibility Points

### New Learning Algorithms
```python
# Add new FL algorithm
class NewFLAdvisor(FLAdvisor):
    def select_pool(self) -> List[str]:
        # Custom implementation
        pass

# Add new RL algorithm  
class NewRLAgent(RLAgent):
    def decide(self, state: Dict) -> str:
        # Custom policy
        pass
```

### New Cache Policies
```python
# Add new eviction policy
def evict_custom(self) -> None:
    # Custom eviction logic
    pass

# Register in action space
_ACTIONS.append("evict_custom")
```

### New Features
```python
# Extend FL feature vector
def extract_features(self, task_row: dict) -> List[float]:
    features = self._base_features(task_row)
    features.extend([
        # New mobility features
        task_row.get("acceleration", 0.0),
        task_row.get("heading_change", 0.0),
    ])
    return features
```

This architecture provides a solid foundation for VANET caching research while maintaining flexibility for future enhancements and extensions.
