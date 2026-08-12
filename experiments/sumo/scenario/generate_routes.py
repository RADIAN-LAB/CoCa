"""Generate random vehicle trips for the 5x5 grid SUMO network.

Vehicles depart at staggered intervals over the simulation window to produce a
realistic urban arrival pattern.

The seed and the fleet size are both command-line arguments. They used to be
module-level constants with ``random.seed(42)`` hardcoded, which meant every
replication of the experiment reused one single mobility realisation: confidence
intervals reflected task-assignment randomness only, not mobility variance.
``--num-vehicles`` additionally lets the offered load be swept.

Usage:
    python3 generate_routes.py --seed 7 --num-vehicles 200 --output trips.xml

Then compute routes:
    duarouter -n grid.net.xml -t trips.xml -o routes.rou.xml --ignore-errors

``scripts/build_mobility.py`` drives both steps plus SUMO for a range of seeds.
"""
from __future__ import annotations

import argparse
import random
import xml.etree.ElementTree as ET
from pathlib import Path

SCENARIO_DIR = Path(__file__).resolve().parent
DEFAULT_NET_FILE = SCENARIO_DIR / "grid.net.xml"

DEFAULT_NUM_VEHICLES = 200
DEFAULT_SIM_DURATION = 500  # seconds
DEPART_MARGIN = 50          # keep last departure this far from the end


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--seed", type=int, default=42,
                        help="RNG seed for trip generation (default: 42)")
    parser.add_argument("--num-vehicles", type=int, default=DEFAULT_NUM_VEHICLES,
                        help=f"Fleet size (default: {DEFAULT_NUM_VEHICLES})")
    parser.add_argument("--duration", type=int, default=DEFAULT_SIM_DURATION,
                        help=f"Simulation window in seconds (default: {DEFAULT_SIM_DURATION})")
    parser.add_argument("--net-file", type=Path, default=DEFAULT_NET_FILE,
                        help="SUMO network file to draw edges from")
    parser.add_argument("--output", type=Path, default=SCENARIO_DIR / "trips.xml",
                        help="Destination trips XML (default: scenario/trips.xml)")
    parser.add_argument("--quiet", action="store_true", help="Suppress the summary")
    return parser.parse_args()


def network_edges(net_file: Path) -> list[str]:
    """Return the ids of all non-internal edges in a SUMO network."""
    root = ET.parse(net_file).getroot()
    return [
        edge.get("id")
        for edge in root.findall("edge")
        if not edge.get("id").startswith(":")
    ]


def generate_trips(edges: list[str], num_vehicles: int, duration: int,
                   rng: random.Random) -> list[tuple[float, int, str, str, float]]:
    """Sample (depart, index, from_edge, to_edge, speed_factor) tuples."""
    if len(edges) < 2:
        raise ValueError(f"network has {len(edges)} usable edges, need at least 2")

    trips = []
    for i in range(num_vehicles):
        depart = round(rng.uniform(0, max(duration - DEPART_MARGIN, 1)), 1)
        from_edge = rng.choice(edges)
        to_edge = rng.choice(edges)
        while to_edge == from_edge:
            to_edge = rng.choice(edges)
        speed_factor = round(rng.uniform(0.8, 1.3), 2)
        trips.append((depart, i, from_edge, to_edge, speed_factor))

    trips.sort(key=lambda t: t[0])
    return trips


def write_trips(trips, output: Path) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w") as handle:
        handle.write('<?xml version="1.0" encoding="UTF-8"?>\n')
        handle.write("<trips>\n")
        for depart, i, from_edge, to_edge, speed_factor in trips:
            handle.write(
                f'    <trip id="veh_{i}" depart="{depart}" from="{from_edge}" '
                f'to="{to_edge}" speedFactor="{speed_factor}"/>\n'
            )
        handle.write("</trips>\n")


def main() -> int:
    args = parse_args()

    # A dedicated Random instance rather than the global one, so importing this
    # module cannot perturb another component's RNG stream.
    rng = random.Random(args.seed)

    edges = network_edges(args.net_file)
    trips = generate_trips(edges, args.num_vehicles, args.duration, rng)
    write_trips(trips, args.output)

    if not args.quiet:
        print(f"Generated {len(trips)} trips in {args.output}")
        print(f"  seed={args.seed}  vehicles={args.num_vehicles}  duration={args.duration}s")
        print(f"  network has {len(edges)} usable edges")
        print("\nNext: compute routes with")
        print(f"  duarouter -n {args.net_file} -t {args.output} "
              f"-o {args.output.parent / 'routes.rou.xml'} --ignore-errors")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
