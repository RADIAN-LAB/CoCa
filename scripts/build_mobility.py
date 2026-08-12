#!/usr/bin/env python3
"""Build N independent SUMO mobility realisations, one per seed.

Each replication of the experiment needs its own mobility trace. Previously all
seeds shared a single ``experiments/sumo/output/fcd_trace.xml``, so reported
confidence intervals captured task-assignment randomness only and understated
the true variance.

For every seed this runs:

    generate_routes.py --seed K   ->  trips.xml
    duarouter                     ->  routes.rou.xml
    sumo                          ->  fcd_trace.xml

Layout produced under ``--out-dir`` (default ``experiments/sumo/mobility``):

    mobility/
      seed_01/{trips.xml,routes.rou.xml,sumo.cfg,fcd_trace.xml}
      seed_02/...

Existing complete seeds are skipped unless ``--force`` is given, so an
interrupted build can simply be re-run.

Usage:
    python3 scripts/build_mobility.py --seeds 30 --jobs 4
    python3 scripts/build_mobility.py --seeds 5 --num-vehicles 400   # load sweep
"""
from __future__ import annotations

import argparse
import concurrent.futures
import shutil
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCENARIO_DIR = ROOT / "experiments" / "sumo" / "scenario"
NET_FILE = SCENARIO_DIR / "grid.net.xml"
GENERATE_ROUTES = SCENARIO_DIR / "generate_routes.py"
DEFAULT_OUT_DIR = ROOT / "experiments" / "sumo" / "mobility"

SUMO_CFG_TEMPLATE = """<?xml version="1.0" encoding="UTF-8"?>
<configuration>
    <input>
        <net-file value="{net_file}"/>
        <route-files value="{route_file}"/>
    </input>
    <time>
        <begin value="0"/>
        <end value="{duration}"/>
        <step-length value="1.0"/>
    </time>
    <output>
        <fcd-output value="{fcd_output}"/>
        <fcd-output.geo value="false"/>
    </output>
    <report>
        <no-step-log value="true"/>
        <no-warnings value="true"/>
    </report>
</configuration>
"""


def require_binary(name: str) -> str:
    """Resolve a SUMO binary, failing with an actionable message."""
    path = shutil.which(name)
    if path is None:
        raise FileNotFoundError(
            f"'{name}' not found on PATH. Install SUMO (e.g. 'brew install sumo') "
            "or add its bin directory to PATH."
        )
    return path


def run(command: list[str], label: str) -> None:
    result = subprocess.run(command, capture_output=True, text=True)
    if result.returncode:
        raise RuntimeError(
            f"{label} failed (exit {result.returncode})\n"
            f"command: {' '.join(command)}\n"
            f"stdout: {result.stdout[-1500:]}\n"
            f"stderr: {result.stderr[-2000:]}"
        )


def build_seed(seed: int, out_dir: Path, num_vehicles: int, duration: int,
               force: bool) -> tuple[int, str, float]:
    """Produce one mobility realisation. Returns (seed, status, seconds)."""
    started = time.time()
    seed_dir = out_dir / f"seed_{seed:02d}"
    trips = seed_dir / "trips.xml"
    routes = seed_dir / "routes.rou.xml"
    cfg = seed_dir / "sumo.cfg"
    fcd = seed_dir / "fcd_trace.xml"

    if fcd.exists() and not force:
        return seed, "skipped (already built)", 0.0

    seed_dir.mkdir(parents=True, exist_ok=True)

    run(
        [
            sys.executable, str(GENERATE_ROUTES),
            "--seed", str(seed),
            "--num-vehicles", str(num_vehicles),
            "--duration", str(duration),
            "--net-file", str(NET_FILE),
            "--output", str(trips),
            "--quiet",
        ],
        f"seed {seed}: trip generation",
    )

    run(
        [
            require_binary("duarouter"),
            "-n", str(NET_FILE),
            "-t", str(trips),
            "-o", str(routes),
            "--ignore-errors",
            "--no-warnings",
        ],
        f"seed {seed}: duarouter",
    )

    cfg.write_text(
        SUMO_CFG_TEMPLATE.format(
            net_file=NET_FILE,
            route_file=routes.name,
            duration=duration,
            fcd_output=fcd.name,
        )
    )

    run([require_binary("sumo"), "-c", str(cfg)], f"seed {seed}: sumo")

    if not fcd.exists():
        raise RuntimeError(f"seed {seed}: SUMO produced no FCD output at {fcd}")

    return seed, "built", time.time() - started


def summarise(fcd: Path) -> dict[str, float]:
    """Cheap sanity stats so divergent mobility can be spotted at a glance."""
    import xml.etree.ElementTree as ET

    root = ET.parse(fcd).getroot()
    steps = root.findall("timestep")
    counts = [len(step.findall("vehicle")) for step in steps]
    vehicle_ids = {
        veh.get("id") for step in steps for veh in step.findall("vehicle")
    }
    occupied = [c for c in counts if c]
    return {
        "timesteps": len(steps),
        "unique_vehicles": len(vehicle_ids),
        "mean_concurrent": sum(counts) / len(counts) if counts else 0.0,
        "peak_concurrent": max(counts) if counts else 0,
        "occupied_steps": len(occupied),
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--seeds", type=int, default=30,
                        help="Build seeds 1..N (default: 30)")
    parser.add_argument("--num-vehicles", type=int, default=200,
                        help="Fleet size per realisation (default: 200)")
    parser.add_argument("--duration", type=int, default=500,
                        help="Simulation seconds (default: 500)")
    parser.add_argument("--out-dir", type=Path, default=DEFAULT_OUT_DIR)
    parser.add_argument("--jobs", type=int, default=1,
                        help="Parallel SUMO runs (default: 1)")
    parser.add_argument("--force", action="store_true",
                        help="Rebuild seeds that already have an FCD trace")
    parser.add_argument("--summary", action="store_true",
                        help="Print per-seed mobility statistics when done")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    # Fail fast on a missing toolchain rather than once per seed.
    require_binary("duarouter")
    require_binary("sumo")

    seeds = list(range(1, args.seeds + 1))
    args.out_dir.mkdir(parents=True, exist_ok=True)
    started = time.time()
    failures: list[str] = []

    with concurrent.futures.ThreadPoolExecutor(max_workers=max(args.jobs, 1)) as pool:
        futures = {
            pool.submit(
                build_seed, seed, args.out_dir, args.num_vehicles,
                args.duration, args.force,
            ): seed
            for seed in seeds
        }
        for future in concurrent.futures.as_completed(futures):
            seed = futures[future]
            try:
                _, status, seconds = future.result()
                suffix = f" ({seconds:.1f}s)" if seconds else ""
                print(f"[seed {seed:02d}] {status}{suffix}")
            except Exception as exc:  # noqa: BLE001 — report and continue
                failures.append(f"seed {seed}: {exc}")
                print(f"[seed {seed:02d}] FAILED: {exc}", file=sys.stderr)

    print(f"\n{len(seeds) - len(failures)}/{len(seeds)} mobility realisations "
          f"available in {args.out_dir} ({time.time() - started:.1f}s)")

    if args.summary:
        print(f"\n{'seed':>5} {'steps':>6} {'vehicles':>9} {'mean':>7} {'peak':>6}")
        for seed in seeds:
            fcd = args.out_dir / f"seed_{seed:02d}" / "fcd_trace.xml"
            if not fcd.exists():
                continue
            stats = summarise(fcd)
            print(f"{seed:>5} {stats['timesteps']:>6} {stats['unique_vehicles']:>9} "
                  f"{stats['mean_concurrent']:>7.1f} {stats['peak_concurrent']:>6}")

    if failures:
        print(f"\n{len(failures)} seed(s) failed:", file=sys.stderr)
        for failure in failures:
            print(f"  {failure}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
