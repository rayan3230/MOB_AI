from typing import List, Dict, Tuple, Optional
from ..engine.base import DepotB7Map, WarehouseCoordinate, AuditTrail, Role
import math

class PickingOptimizationService:
    def __init__(self, floors: Dict[int, DepotB7Map]):
        self.floors = floors

    def calculate_picking_route(self, floor_idx: int, start_coord: WarehouseCoordinate, picks: List[WarehouseCoordinate]) -> Dict:
        """
        Requirement 8.3: Optimized Picking Route.
        Uses A* for pathfinding and a Nearest Neighbor heuristic for the TSP sequence.
        """
        if floor_idx not in self.floors:
            return {"error": f"Floor {floor_idx} not found."}

        warehouse_map = self.floors[floor_idx]
        current_pos = start_coord
        remaining_picks = list(picks)
        route = []
        total_distance = 0
        path_segments = []

        # Simple Greedy Nearest Neighbor for sequence optimization (TSP Heuristic)
        while remaining_picks:
            # find nearest pick based on Manhattan (fastest filter)
            next_pick = min(remaining_picks, key=lambda p: abs(p.x - current_pos.x) + abs(p.y - current_pos.y))
            
            # calculate exact A* path
            path = warehouse_map.find_path_astar(current_pos, next_pick)
            
            if path:
                path_segments.append(path)
                total_distance += len(path) - 1
                current_pos = next_pick
                route.append(next_pick)
            else:
                # If a pick is unreachable, we skip it but log it
                AuditTrail.log(Role.SYSTEM, f"Warning: Pick at {next_pick} unreachable from {current_pos}. Skipping.")
            
            remaining_picks.remove(next_pick)

        # Log completion
        AuditTrail.log(Role.SYSTEM, f"Calculated picking route for {len(picks)} items. Total distance: {total_distance}m")

        return {
            "floor_idx": floor_idx,
            "route_sequence": route,
            "path_segments": path_segments,
            "total_distance": total_distance
        }

    def batch_picks(self, available_picks: List[Dict]) -> List[List[Dict]]:
        """
        Groups picks into batches by floor or proximity to optimize fulfillment.
        """
        # Group by floor
        batches = {}
        for pick in available_picks:
            f = pick.get('floor_idx', 0)
            if f not in batches: batches[f] = []
            batches[f].append(pick)
            
        return list(batches.values())
