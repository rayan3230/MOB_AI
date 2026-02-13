from typing import List, Dict, Tuple, Optional
from ..engine.base import DepotB7Map, WarehouseCoordinate, AuditTrail, Role
import math

class PickingOptimizationService:
    def __init__(self, floors: Dict[int, DepotB7Map]):
        self.floors = floors
        self.travel_speed = 1.2 # m/s (Average walking speed)

    def calculate_picking_route(self, floor_idx: int, start_coord: WarehouseCoordinate, picks: List[WarehouseCoordinate]) -> Dict:
        """
        Requirement 8.3: Optimized Picking Route with 2-Opt TSP.
        - Distance Matrix: Exact A* path distances precomputed.
        - Initial Solution: Greedy Nearest Neighbor.
        - Optimization: 2-Opt local search improvement.
        """
        if floor_idx not in self.floors:
            return {"error": f"Floor {floor_idx} not found."}

        warehouse_map = self.floors[floor_idx]
        nodes = [start_coord] + picks
        n = len(nodes)
        
        # 1. Build Distance Matrix (Exact A* distances)
        dist_matrix = [[0.0 for _ in range(n)] for _ in range(n)]
        path_cache = {} # (i, j) -> path

        for i in range(n):
            for j in range(i + 1, n):
                path = warehouse_map.find_path_astar(nodes[i], nodes[j])
                if not path:
                    # Fallback to Manhattan if path is blocked (e.g. into a rack)
                    d = abs(nodes[i].x - nodes[j].x) + abs(nodes[i].y - nodes[j].y)
                else:
                    d = len(path) - 1
                dist_matrix[i][j] = dist_matrix[j][i] = float(d)
                path_cache[(i, j)] = path_cache[(j, i)] = path

        # 2. Greedy Initial Solution (Nearest Neighbor)
        current_tour = [0]
        unvisited = list(range(1, n))
        while unvisited:
            last = current_tour[-1]
            next_node = min(unvisited, key=lambda x: dist_matrix[last][x])
            current_tour.append(next_node)
            unvisited.remove(next_node)

        # 3. 2-Opt Improvement
        def get_tour_dist(tour):
            d = 0.0
            for k in range(len(tour) - 1):
                d += dist_matrix[tour[k]][tour[k+1]]
            return d

        improved = True
        while improved:
            improved = False
            for i in range(1, n - 1):
                for j in range(i + 1, n):
                    # For a simple path (not circuit), 2-opt swaps segment [i...j]
                    new_tour = current_tour[:i] + current_tour[i:j+1][::-1] + current_tour[j+1:]
                    
                    if get_tour_dist(new_tour) < get_tour_dist(current_tour):
                        current_tour = new_tour
                        improved = True

        # 4. Final Path Reconstruction
        total_distance = get_tour_dist(current_tour)
        path_segments = []
        route_sequence = []
        for k in range(len(current_tour) - 1):
            i, j = current_tour[k], current_tour[k+1]
            seg = path_cache.get((i, j), [])
            path_segments.append(seg)
            route_sequence.append(nodes[j])

        # 5. Estimated Travel Time
        travel_time_sec = total_distance / self.travel_speed

        AuditTrail.log(Role.SYSTEM, f"Picking route optimized (2-opt). Distance: {total_distance}m | Est. Time: {travel_time_sec/60:.2f} min")

        return {
            "floor_idx": floor_idx,
            "route_sequence": route_sequence,
            "path_segments": path_segments,
            "total_distance": total_distance,
            "estimated_time_seconds": travel_time_sec
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
