#!/usr/bin/env python3
"""Analyze timing decisions and cache performance with deadline awareness."""

import json
import pandas as pd
import matplotlib.pyplot as plt
from pathlib import Path
from typing import Dict, List, Any

def analyze_timing_decisions(results_file: str, output_dir: str = "experiments/timing_analysis"):
    """Analyze timing decisions from experiment results."""
    
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    # Load results
    with open(results_file) as f:
        results = json.load(f)
    
    # Extract timing statistics
    timing_stats = results.get("timing_statistics", {})
    if not timing_stats:
        print("No timing statistics found in results")
        return
    
    # Create analysis report
    report = {
        "Cache Performance": {
            "Total Decisions": timing_stats.get("total_decisions", 0),
            "Cache Usage Rate": f"{timing_stats.get('cache_usage_rate', 0):.1%}",
            "Average Cache Time": f"{timing_stats.get('avg_cache_time', 0):.2f}ms",
            "Average Compute Time": f"{timing_stats.get('avg_compute_time', 0):.2f}ms",
            "Deadline Miss Rate": f"{timing_stats.get('deadline_miss_rate', 0):.1%}"
        },
        "Decision Reasons": timing_stats.get("decision_reasons", {}),
        "Performance Metrics": {
            "Total Tasks": results.get("total_tasks", 0),
            "Success Rate": f"{results.get('success_rate', 0):.1%}",
            "Cache Hits": results.get("cache_hits", 0),
            "Cache Misses": results.get("cache_misses", 0),
            "Hit Rate": f"{results.get('cache_hits', 0) / (results.get('cache_hits', 0) + results.get('cache_misses', 1)):.1%}"
        }
    }
    
    # Save analysis report
    with open(output_path / "timing_analysis.json", "w") as f:
        json.dump(report, f, indent=2)
    
    print("=== Deadline-Aware Cache Analysis ===")
    for category, metrics in report.items():
        print(f"\n{category}:")
        for key, value in metrics.items():
            print(f"  {key}: {value}")
    
    return report

if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        analyze_timing_decisions(sys.argv[1])
    else:
        print("Usage: python analyze_timing.py <results_file.json>")
