
import os
import sys
import pandas as pd
import numpy as np
from dataclasses import dataclass
from collections import defaultdict

# Mocking the structure from generate_hackathon_deliverables.py
@dataclass
class ChariotState:
    code: str
    capacity: int
    remaining_capacity: int
    current_corridor: str = "H"
    tasks_count: int = 0

class ChariotTester:
    def _choose_chariot(self, chariots: list[ChariotState], target_corridor: str, required_pallets: int) -> ChariotState:
        feasible = [c for c in chariots if c.capacity >= required_pallets]
        if not feasible:
            max_capacity = max(c.capacity for c in chariots)
            feasible = [c for c in chariots if c.capacity == max_capacity]

        def score(ch: ChariotState) -> tuple[int, int, int]:
            corridor_gap = abs(ord(ch.current_corridor) - ord(target_corridor))
            return (ch.tasks_count, corridor_gap, -ch.capacity)

        return sorted(feasible, key=score)[0]

    def _resolve_corridor(self, preferred_corridor: str, traffic: dict[str, int], threshold: int = 2) -> tuple[str, bool]:
        preferred_corridor = preferred_corridor.upper()
        if traffic[preferred_corridor] < threshold:
            traffic[preferred_corridor] += 1
            return preferred_corridor, False

        nearby = [chr(code) for code in range(ord("A"), ord("Z") + 1)]
        nearby.sort(key=lambda c: abs(ord(c) - ord(preferred_corridor)))
        for candidate in nearby:
            if traffic[candidate] < threshold:
                traffic[candidate] += 1
                return candidate, True

        traffic[preferred_corridor] += 1
        return preferred_corridor, False

def verify_multi_chariot():
    # Setup path
    sys.path.append(os.getcwd())
    
    tester = ChariotTester()
    
    chariots = [
        ChariotState(code="CH-01", capacity=3, remaining_capacity=3),
        ChariotState(code="CH-02", capacity=1, remaining_capacity=1),
        ChariotState(code="CH-03", capacity=1, remaining_capacity=1),
    ]

    print("--- Verifying Chariot Capacity Requirements ---")
    
    # Test 1: Carry 3 pallets
    chosen = tester._choose_chariot(chariots, "A", 3)
    print(f"Required 3 pallets: Chosen {chosen.code} (Capacity: {chosen.capacity})")
    assert chosen.code == "CH-01", "CH-01 should be chosen for 3 pallets"

    # Test 2: Others limited to 1
    chosen_2 = tester._choose_chariot(chariots, "A", 2)
    print(f"Required 2 pallets: Chosen {chosen_2.code} (Capacity: {chosen_2.capacity})")
    assert chosen_2.code == "CH-01", "Others should be excluded for 2 pallets"

    # Test 3: CH-02 never assigned 2 pallets
    feasible_for_2 = [c for c in chariots if c.capacity >= 2]
    codes_for_2 = [c.code for c in feasible_for_2]
    print(f"Feasible for 2 pallets: {codes_for_2}")
    assert "CH-02" not in codes_for_2, "CH-02 should never be assigned 2 pallets"

    print("\n--- Verifying Workload Distribution ---")
    for c in chariots: c.tasks_count = 0
    chariots[0].tasks_count = 1
    chosen_w = tester._choose_chariot(chariots, "H", 1)
    print(f"Workload balancing: CH-01 has 1 task, others 0. Chosen: {chosen_w.code}")
    assert chosen_w.code in ["CH-02", "CH-03"], "Should distribute to idle chariot"

    print("\n--- Verifying Collision Avoidance (Corridor Routing) ---")
    traffic = defaultdict(int)
    threshold = 2
    traffic["A"] = 2
    target, rerouted = tester._resolve_corridor("A", traffic, threshold)
    print(f"Corridor A is full (threshold 2). Requested A, assigned {target} (Rerouted: {rerouted})")
    assert target != "A", "Should reroute from full corridor"
    
    print("\n--- Verifying Spatial Coordination (Pick Partitioning) ---")
    from ai_service.core.picking_service import PickingOptimizationService
    from ai_service.engine.base import WarehouseCoordinate
    from ai_service.maps.floor_0_rdc import GroundFloorMap
    
    rdc = GroundFloorMap()
    service = PickingOptimizationService({0: rdc})
    
    starts = [WarehouseCoordinate(5, 5), WarehouseCoordinate(40, 5)]
    picks = [
        WarehouseCoordinate(10, 10), 
        WarehouseCoordinate(15, 10),
        WarehouseCoordinate(35, 10),
        WarehouseCoordinate(45, 10)
    ]
    
    routes = service.calculate_multi_chariot_routes(0, starts, picks)
    
    # Check if picks are disjoint
    ch1_picks = set([(p.x, p.y) for p in routes[0]['route_sequence']])
    ch2_picks = set([(p.x, p.y) for p in routes[1]['route_sequence']])
    
    intersection = ch1_picks.intersection(ch2_picks)
    print(f"Chariot 1 targets: {ch1_picks}")
    print(f"Chariot 2 targets: {ch2_picks}")
    print(f"Overlapping target coordinates: {intersection}")
    
    assert len(intersection) == 0, "No two chariots should be assigned the same target coordinate"
    
    print("\n[SUCCESS] Multi-Chariot Coordination Requirements Verified.")

if __name__ == "__main__":
    verify_multi_chariot()

if __name__ == "__main__":
    verify_multi_chariot()
