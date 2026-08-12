"""Replay a task trace and evaluate scheduler performance.

Usage:
    python3 scripts/run_experiment.py --trace experiments/sumo/input/sumo_tasks.csv \
        --output experiments/sumo/output/summary.json

Outputs summary JSON with:
    success_rate, avg_completion, cache_hits, cache_misses, total_runtime_s
"""
from __future__ import annotations

import argparse
import csv
import json
# Ensure project root in path BEFORE local imports
import os
import sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import random
import numpy as np
import torch

# Seed all RNGs for reproducibility; varies across multi-seed runs
_SEED = int(os.environ.get("TASK_GEN_SEED", "42"))
random.seed(_SEED)
np.random.seed(_SEED)
torch.manual_seed(_SEED)

import random
import numpy as np
import torch

# Seed all RNGs for reproducibility; varies across multi-seed runs
_SEED = int(os.environ.get("TASK_GEN_SEED", "42"))
random.seed(_SEED)
np.random.seed(_SEED)
torch.manual_seed(_SEED)

from cache.rl_agent import RLAgent
from cache.distributed_manager import DistributedCacheManager
from cache import distributed_manager as dm_module  # Import module to update singleton
from cache.manager import make_task_key
import time
from collections import defaultdict
from typing import List

# Ensure project root in path

from sdn_core.scheduler import task_scheduling
from sdn_core.provenance import provenance



def load_trace(csv_path: Path):
    """Load CSV and bucket rows by timestamp.

    Returns dict[timestamp] -> list[row_dict]. The CSV is expected to contain
    at least the columns:
        timestamp,node_id,task_id,task_type,priority,data_size_kB,
        origin_rsu,destination_rsu,fog_rsu,final_rsu
    Extra columns are preserved.
    """
    buckets: dict[int, List[dict[str, str]]] = defaultdict(list)
    with csv_path.open() as fh:
        reader = csv.DictReader(fh)
        for row in reader:
            ts = int(row["timestamp"])
            buckets[ts].append(row)
    return dict(sorted(buckets.items()))


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--trace", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--max_ts", type=int, default=None, help="Process only timestamps ≤ this value for quick tests")
    parser.add_argument("--evict_policy", choices=["lru", "lfu", "fifo", "random", "none"], default=None,
                        help="If set, use a fixed eviction policy instead of RL agent (none=no eviction)")
    parser.add_argument("--load_rl", type=Path, default=None, help="Load pretrained RL agent from checkpoint")
    parser.add_argument("--no_fl", action="store_true", help="Disable FL pre-placement to compare pure policies")
    parser.add_argument("--save_rl", type=Path, default=None, help="Save RL agent after training")
    parser.add_argument("--fl_placement", action="store_true",
                        help="Enable FL pre-placement even when a fixed eviction policy is set. "
                             "Without this, --evict_policy suppresses pre-placement, which made "
                             "the 'FL-Only' baseline identical to plain LFU.")
    parser.add_argument("--preplace_budget", type=int, default=10,
                        help="Top-K predictions each RSU pre-places per timestep (default: 10). "
                             "Must be well below cache capacity or placements evict real results.")
    parser.add_argument("--preplace_mode", choices=["compute", "reserve"], default="compute",
                        help="'compute': speculatively run the predicted task and cache a real "
                             "result, paying its cost. 'reserve': hold capacity without computing "
                             "(ablation showing what pre-placement is worth without the work).")
    args = parser.parse_args()

    trace = load_trace(args.trace)

    total_success = 0
    total_tasks = 0
    total_completion = 0.0

    start = time.time()
    # Per-run FL log, derived from the output path. It used to be a single fixed
    # file under experiments/logs/, so every run overwrote the previous one and
    # concurrent runs interleaved their writes into the same file.
    log_path = args.output.with_name(f"{args.output.stem}_fl_training.csv")
    log_path.parent.mkdir(parents=True, exist_ok=True)
    log_path.write_text("timestamp,cache_hits,cache_misses,fl_loss\n")
    # Determine eviction policy for the cache
    # For RL mode, use LRU as base (RL will override with explicit evictions)
    # For fixed policy mode, use that policy for ALL auto-evictions
    if args.evict_policy and args.evict_policy != "none":
        cache_eviction_policy = args.evict_policy.upper()
    else:
        cache_eviction_policy = "LRU"  # Default for RL mode
    
    # Create fresh distributed cache manager with the correct eviction policy
    # This ensures ALL auto-evictions (in store/preplace) use the chosen policy
    distributed_cache_manager = DistributedCacheManager(
        rsu_ids=[1, 2, 3, 4, 5],
        cache_capacity=100,  # 500 total across 5 RSUs — pressure for 145 unique keys
        default_ttl=300,  # Long TTL to prevent expiration
        eviction_policy=cache_eviction_policy
    )
    # CRITICAL: Update the module-level singleton so the scheduler sees the same instance
    dm_module.distributed_cache_manager = distributed_cache_manager
    
    # CRITICAL FIX: Disable auto-caching for FL+RL mode, enable for traditional policies
    # This allows FL+RL to have full control over what gets cached
    # Enable auto-cache for ALL modes - scheduler will update placeholders with real results
    if args.evict_policy == "none":
        # No-cache baseline: disable both lookup and store
        distributed_cache_manager.ENABLE_AUTO_CACHE = False
        distributed_cache_manager.ENABLE_CACHE_LOOKUP = False
        distributed_cache_manager.ENABLE_FORWARDING = False
        print(f"Cache manager created: capacity=100/RSU (500 total), NO-CACHE mode")
    elif args.evict_policy:
        # Traditional policy mode: local RSU cache only, no cross-RSU forwarding
        distributed_cache_manager.ENABLE_AUTO_CACHE = True
        distributed_cache_manager.ENABLE_CACHE_LOOKUP = True
        distributed_cache_manager.ENABLE_FORWARDING = False
        print(f"Cache manager created: capacity=100/RSU (500 total), eviction_policy={cache_eviction_policy}, LOCAL-ONLY")
    else:
        # FL+RL mode: FL preplaces across RSUs, cross-RSU forwarding enabled
        distributed_cache_manager.ENABLE_AUTO_CACHE = True
        distributed_cache_manager.ENABLE_CACHE_LOOKUP = True
        distributed_cache_manager.ENABLE_FORWARDING = True
        print(f"Cache manager created: capacity=100/RSU (500 total), FL+RL mode, FORWARDING=ON")
    
    # Per-RSU FL clients are now owned by the distributed cache manager
    rl_agent = None if args.evict_policy else RLAgent()
    
    # Load pretrained RL agent if specified
    if rl_agent is not None and args.load_rl and args.load_rl.exists():
        rl_agent.load(str(args.load_rl))
        print(f"Loaded pretrained RL agent from {args.load_rl}, epsilon={rl_agent.epsilon:.3f}")
    
    # FL pre-placement runs when FL is on and either no fixed eviction policy is
    # set (the FL+RL configuration) or it is explicitly requested (--fl_placement,
    # used by the FL-Only baseline, which otherwise silently degenerated to LFU).
    fl_placement_enabled = (
        not args.no_fl and (not args.evict_policy or args.fl_placement)
    )
    print(f"FL pre-placement: {'ON' if fl_placement_enabled else 'OFF'}"
          + (f" (mode={args.preplace_mode}, budget={args.preplace_budget}/RSU/step)"
             if fl_placement_enabled else ""))

    prev_hits = 0
    prev_hit_rate = 0.0  # Track hit rate for delta calculation
    progress_interval = 100
    for ts, tasks in trace.items():
        if args.max_ts is not None and ts > args.max_ts:
            break
        if ts % progress_interval == 0:
            print(f"[run_experiment] processing ts={ts} (cache_hits={prev_hits})")
        # Phase A: FL pre-placement BEFORE scheduling (predict-then-serve)
        # CoCa pre-places predictions from PREVIOUS observations so the cache
        # is warm when the scheduler processes current tasks.
        if fl_placement_enabled:
            # FL pre-placement: the RSU speculatively *computes* its top-ranked
            # predictions so the cache holds real results when the scheduler
            # runs. The budget matters: the advisor used to place up to 100
            # entries per RSU per timestep into a 100-entry cache, which
            # displaces every real result once placements stop being free.
            for rid in [1, 2, 3, 4, 5]:
                top_predictions = distributed_cache_manager.fl_select_pool(rid)
                for k in top_predictions[:args.preplace_budget]:
                    attrs = distributed_cache_manager.fl_attrs(rid, k)
                    if args.preplace_mode == "compute":
                        distributed_cache_manager.precompute(k, rid, attrs)
                    else:  # "reserve" — ablation: capacity held, nothing computed
                        distributed_cache_manager.preplace(k, rid)

        # Phase B: Build task keys for this timestep
        items_this_step = [
            (
                make_task_key(
                    row["task_type"],
                    row["priority"],
                    row["data_size_kB"],
                ),
                row,
            )
            for row in tasks
        ]


        # Compute workload aggregates (used by RL and logging)
        mean_priority = sum(int(r["priority"]) for r in tasks) / (len(tasks) * 3.0)
        mean_size = sum(int(r["data_size_kB"]) for r in tasks) / (len(tasks) * 1000.0)
        locality_ratio = sum(1 for r in tasks if r["origin_rsu"] == r["destination_rsu"]) / len(tasks)
        mean_speed = sum(float(r["veh_speed_kmh"]) for r in tasks) / (len(tasks) * 120.0)
        mean_rsu_load = sum(float(r["rsu_load"]) for r in tasks) / len(tasks)
        mean_pop_decay = sum(float(r["pop_decay"]) for r in tasks) / len(tasks)

        # Compute aggregated state for RL decision
        agg_state = distributed_cache_manager.get_aggregated_state()
        
        # Phase-aware features (assuming 100-step phases)
        PHASE_LENGTH = 100
        phase_position = (ts % PHASE_LENGTH) / PHASE_LENGTH  # 0.0 to 1.0 within phase
        current_hit_rate = agg_state["hit_rate"]
        hit_rate_delta = current_hit_rate - prev_hit_rate
        
        state_dict = {
            "cache_usage": agg_state["cache_usage"],
            "hit_rate": current_hit_rate,
            "avg_completion": total_completion / (total_success + 1e-9) if total_success else 0.0,
            "mean_priority": mean_priority,
            "mean_size": mean_size,
            "locality_ratio": locality_ratio,
            "mean_speed": mean_speed,
            "mean_rsu_load": mean_rsu_load,
            "mean_pop_decay": mean_pop_decay,
            "phase_position": phase_position,
            "hit_rate_delta": hit_rate_delta,
        }
        
        # Eviction decision
        if args.evict_policy:
            if args.evict_policy == "none":
                action = "noop"
            else:
                action = f"evict_{args.evict_policy}"
        elif rl_agent is not None:
            action = rl_agent.decide(state_dict)
        else:
            action = "noop"
        
        # Apply eviction action if needed
        if action != "noop":
            # Apply action to the most loaded RSU
            rsu_states = {rsu_id: distributed_cache_manager.get_rsu_state(rsu_id) 
                         for rsu_id in [1, 2, 3, 4, 5]}
            target_rsu = max(rsu_states.keys(), key=lambda r: rsu_states[r]["cache_usage"])
            distributed_cache_manager.evict_action(action, target_rsu)


        # Convert to scheduler input format
        sched_tasks = [
            (
                int(row["node_id"]),
                int(row["task_id"]),
                int(row["fog_rsu"]),
                int(row["final_rsu"]),
            )
            for row in tasks
        ]
        
        # Create vehicle attributes dictionary for enhanced cache keys
        vehicle_attributes = {}
        for row in tasks:
            node_id = int(row["node_id"])
            vehicle_attributes[node_id] = {
                'task_type': int(row["task_type"]),
                'priority': int(row["priority"]),
                'data_size': int(row["data_size_kB"]),
                'x': float(row.get('pos_x', 0)),  # Default if not available
                'y': float(row.get('pos_y', 0)),  # Default if not available
                'speed': float(row["veh_speed_kmh"]),
                'time': float(row["timestamp"])
            }
        
        # Phase B: run scheduler with enhanced attributes
        success, avg_comp = task_scheduling(
            sched_tasks,
            1,      # delay_edge_rsu
            0.5,    # delay_rsu_rsu
            0.1,    # delay_car_car
            4,      # task_size
            5,      # deadline — tight to penalize cache misses
            True,   # enable_trajectory_prediction
            vehicle_attributes  # Pass task attributes for enhanced caching
        )
        
        # RL agent learning (if enabled)
        hits_after, _ = distributed_cache_manager.get_global_stats()
        if rl_agent is not None:
            # Reward function for FL+RL cache management
            # Primary goal: maximize cache hits step-to-step.
            cache_hit_delta = hits_after - prev_hits

            # Strongly punish actions that reduce future hits, reward ones that increase them.
            if cache_hit_delta > 0:
                cache_reward = 10.0 * cache_hit_delta
            elif cache_hit_delta < 0:
                cache_reward = -15.0 * abs(cache_hit_delta)
            else:
                # No change in hits: small penalty if we evicted anyway.
                cache_reward = -0.5 if action != "noop" else 0.0

            # Secondary goal: maintain task success.
            success_reward = success * 1.0

            # Additional regularization: discourage evictions when cache is far from full.
            cache_usage = agg_state["cache_usage"]
            if cache_usage < 0.6 and action != "noop":
                eviction_penalty = -1.0
            else:
                eviction_penalty = 0.0

            reward = cache_reward + success_reward + eviction_penalty
            next_agg_state = distributed_cache_manager.get_aggregated_state()
            next_hit_rate = next_agg_state["hit_rate"]
            next_state = {
                "cache_usage": next_agg_state["cache_usage"],
                "hit_rate": next_hit_rate,
                "avg_completion": (total_completion + avg_comp * success) / (total_success + success + 1e-9),
                "mean_priority": mean_priority,
                "mean_size": mean_size,
                "locality_ratio": locality_ratio,
                "mean_speed": mean_speed,
                "mean_rsu_load": mean_rsu_load,
                "mean_pop_decay": mean_pop_decay,
                "phase_position": phase_position,
                "hit_rate_delta": next_hit_rate - current_hit_rate,
            }
            rl_agent.observe(state_dict, action, reward, next_state)
        # log metrics
        with log_path.open("a") as _f:
            _, misses = distributed_cache_manager.get_global_stats()
            # log mean FL loss across RSUs for monitoring
            fl_losses = [adv.last_loss or 0.0 for adv in distributed_cache_manager.fl_clients.values() if adv.last_loss is not None]
            mean_loss = sum(fl_losses)/len(fl_losses) if fl_losses else 0.0
            _f.write(f"{ts},{hits_after},{misses},{mean_loss:.4f}\n")

        # Phase C: FL observation and training AFTER scheduling
        # FL learns from current timestep so it can predict for the NEXT timestep
        if not args.no_fl:
            items_by_rsu = {rid: [] for rid in [1,2,3,4,5]}
            for k, row in items_this_step:
                items_by_rsu[int(row['fog_rsu'])].append((k, row))
            for rid, lst in items_by_rsu.items():
                if lst:
                    distributed_cache_manager.fl_observe_tasks(rid, lst)
            distributed_cache_manager.fl_step(ts)

        total_success += success
        total_tasks += len(tasks)
        total_completion += avg_comp * success  # weighted sum
        # Purge expired entries from all RSU caches
        for rsu_id in distributed_cache_manager.rsu_ids:
            distributed_cache_manager.rsu_caches[rsu_id].purge_expired()
        prev_hits = hits_after
        prev_hit_rate = current_hit_rate  # Update for next iteration's delta

    runtime = time.time() - start
    hits, misses = distributed_cache_manager.get_global_stats()

    summary = {
        "total_tasks": total_tasks,
        "success_rate": total_success / total_tasks if total_tasks else 0,
        "average_completion": total_completion / total_success if total_success else 0,
        "cache_hits": hits,
        "cache_misses": misses,
        "hit_rate": hits / (hits + misses) if (hits + misses) else 0.0,
        # Reservations made by the FL advisor. These hold no result, so they
        # never count as hits; they are reported because they consume cache
        # capacity and (in the energy model) proactive-placement cost.
        "preplacements": distributed_cache_manager.total_preplacements,
        **distributed_cache_manager.proactive_stats(),
        "runtime_seconds": runtime,
        "provenance": provenance(
            params={
                "trace": str(args.trace),
                "seed": _SEED,
                "max_ts": args.max_ts,
                "evict_policy": args.evict_policy,
                "load_rl": str(args.load_rl) if args.load_rl else None,
                "no_fl": args.no_fl,
                "fl_placement_enabled": fl_placement_enabled,
                "preplace_mode": args.preplace_mode,
                "preplace_budget": args.preplace_budget,
                "cache_capacity_per_rsu": distributed_cache_manager.cache_capacity,
                "default_ttl": distributed_cache_manager.default_ttl,
                "eviction_policy": cache_eviction_policy,
                "rsu_ids": distributed_cache_manager.rsu_ids,
                "enable_auto_cache": distributed_cache_manager.ENABLE_AUTO_CACHE,
                "enable_cache_lookup": distributed_cache_manager.ENABLE_CACHE_LOOKUP,
                "enable_forwarding": distributed_cache_manager.ENABLE_FORWARDING,
            }
        ),
    }

    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("w") as fh:
        json.dump(summary, fh, indent=2)
    print("Experiment completed. Summary:\n", json.dumps(summary, indent=2))
    
    # Save RL agent if specified
    if rl_agent is not None and args.save_rl:
        args.save_rl.parent.mkdir(parents=True, exist_ok=True)
        rl_agent.save(str(args.save_rl))
        print(f"RL agent saved to {args.save_rl} (epsilon={rl_agent.epsilon:.3f}, steps={rl_agent.step_counter})")


if __name__ == "__main__":
    main()
