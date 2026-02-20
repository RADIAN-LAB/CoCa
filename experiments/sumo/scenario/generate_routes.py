"""Generate random vehicle routes for the 5x5 grid SUMO network.

Creates 200 vehicles with random origins/destinations over a 500-second simulation.
Vehicles depart at staggered intervals to simulate realistic urban traffic.
"""
import random
import xml.etree.ElementTree as ET
from pathlib import Path

random.seed(42)

SCENARIO_DIR = Path(__file__).parent
NET_FILE = SCENARIO_DIR / "grid.net.xml"

# Parse network to get valid edges
tree = ET.parse(NET_FILE)
root = tree.getroot()
edges = [e.get("id") for e in root.findall("edge") if not e.get("id").startswith(":")]

NUM_VEHICLES = 200
SIM_DURATION = 500  # seconds

# Generate trips sorted by departure time
trips = []
for i in range(NUM_VEHICLES):
    depart = round(random.uniform(0, SIM_DURATION - 50), 1)
    from_edge = random.choice(edges)
    to_edge = random.choice(edges)
    while to_edge == from_edge:
        to_edge = random.choice(edges)
    speed_factor = round(random.uniform(0.8, 1.3), 2)
    trips.append((depart, i, from_edge, to_edge, speed_factor))

trips.sort(key=lambda t: t[0])

trips_file = SCENARIO_DIR / "trips.xml"
with open(trips_file, "w") as f:
    f.write('<?xml version="1.0" encoding="UTF-8"?>\n')
    f.write('<trips>\n')
    for depart, i, from_edge, to_edge, speed_factor in trips:
        f.write(f'    <trip id="veh_{i}" depart="{depart}" from="{from_edge}" '
                f'to="{to_edge}" speedFactor="{speed_factor}"/>\n')
    f.write('</trips>\n')

print(f"Generated {NUM_VEHICLES} trips in {trips_file}")
print(f"Network has {len(edges)} edges")
print(f"Simulation duration: {SIM_DURATION}s")
print(f"\nNext: run duarouter to compute routes:")
print(f"  duarouter -n {NET_FILE} -t {trips_file} -o {SCENARIO_DIR}/routes.rou.xml --ignore-errors")
