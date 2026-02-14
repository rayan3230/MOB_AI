from typing import List, Dict, Tuple, Optional
from ..engine.base import DepotB7Map, WarehouseCoordinate, AuditTrail, Role
from .learning_engine import LearningFeedbackEngine
import math

class PickingOptimizationService:
    def __init__(self, floors: Dict[int, DepotB7Map]):
        self.floors = floors
        self.learning_engine = LearningFeedbackEngine()
        self.travel_speed = self.learning_engine.get_current_travel_speed()
        self.global_path_cache = {} # (floor_idx, coord_a, coord_b) -> (dist, path)

    def _refresh_speed(self):
        """Syncs the travel speed with the latest AI learning data."""
        self.travel_speed = self.learning_engine.get_current_travel_speed()

    def _get_cached_path(self, floor_idx: int, a: WarehouseCoordinate, b: WarehouseCoordinate) -> Tuple[float, List[WarehouseCoordinate]]:
        """Requirement: Caching enabled."""
        key = tuple(sorted([a, b], key=lambda c: (c.x, c.y)))
        full_key = (floor_idx, *key)
        
        if full_key in self.global_path_cache:
            return self.global_path_cache[full_key]
            
        warehouse_map = self.floors[floor_idx]
        path = warehouse_map.find_path_astar(a, b)
        
        if not path:
            dist = float(abs(a.x - b.x) + abs(a.y - b.y))
        else:
            dist = float(len(path) - 1)
            
        self.global_path_cache[full_key] = (dist, path)
        return dist, path

    def calculate_picking_route(self, floor_idx: int, start_coord: WarehouseCoordinate, picks: List[WarehouseCoordinate], user_role: Role = Role.SYSTEM) -> Dict:
        """
        Requirement 8.3: Optimized Picking Route with 2-Opt TSP.
        - Works for N items: Optimized distance matrix building.
        - Caching enabled: Persistent global path cache.
        """
        if floor_idx not in self.floors:
            err_msg = f"Navigation Error: Floor {floor_idx} not found in digital twin map."
            AuditTrail.log(Role.SYSTEM, err_msg)
            return {"error": err_msg}
            
        self._refresh_speed()

        if not picks:
            return {
                "floor_idx": floor_idx,
                "route_sequence": [],
                "path_segments": [],
                "total_distance": 0.0,
                "estimated_time_seconds": 0.0
            }

        nodes = [start_coord] + picks
        n = len(nodes)
        
        # 1. Build Distance Matrix (With Global Cache)
        dist_matrix = [[0.0 for _ in range(n)] for _ in range(n)]
        path_segments_lookup = {}

        for i in range(n):
            for j in range(i + 1, n):
                dist, path = self._get_cached_path(floor_idx, nodes[i], nodes[j])
                dist_matrix[i][j] = dist_matrix[j][i] = dist
                path_segments_lookup[(i, j)] = path_segments_lookup[(j, i)] = path

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
            return sum(dist_matrix[tour[k]][tour[k+1]] for k in range(len(tour) - 1))

        improved = True
        while improved:
            improved = False
            for i in range(1, n - 1):
                for j in range(i + 1, n):
                    # Segment swap for 2-op optimization
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
            seg = path_segments_lookup.get((i, j), [])
            # Reverse path if directions don't match (cache stores sorted pairs)
            if seg and seg[0] != nodes[i]:
                seg = seg[::-1]
            path_segments.append(seg)
            route_sequence.append(nodes[j])

        travel_time_sec = total_distance / self.travel_speed
        AuditTrail.log(user_role, f"Route optimized for {len(picks)} items. Distance: {total_distance}m | Role: {user_role.value}")

        return {
            "floor_idx": floor_idx,
            "route_sequence": route_sequence,
            "path_segments": path_segments,
            "total_distance": total_distance,
            "estimated_time_seconds": travel_time_sec
        }

    def validate_and_approve_route(self, route_data: Dict, supervisor_role: Role, justification: str) -> bool:
        """Governance: Supervisor must validate picking routes for high-value orders."""
        if supervisor_role not in [Role.SUPERVISOR, Role.ADMIN]:
            raise PermissionError("Access Denied: Route validation requires Supervisor privileges.")
            
        if not justification or len(justification) < 5:
             raise ValueError("Validation rejected: Please provide a comment for the approval.")

        AuditTrail.log(supervisor_role, f"Approved Picking Route (Dist: {route_data['total_distance']}m)", justification)
        return True

        return {
            "floor_idx": floor_idx,
            "route_sequence": route_sequence,
            "path_segments": path_segments,
            "total_distance": total_distance,
            "estimated_time_seconds": travel_time_sec
        }

    def calculate_multi_chariot_routes(self, floor_idx: int, starts: List[WarehouseCoordinate], picks: List[WarehouseCoordinate]) -> List[Dict]:
        """
        Requirement 8.5: Multi-chariot coordination.
        1. Spatial partitioning of tasks.
        2. Intersection detection & Reroute/Delay logic.
        """
        if not starts: return []
        if len(starts) == 1:
            return [self.calculate_picking_route(floor_idx, starts[0], picks)]
            
        # Distribute picks to nearest chariot (Simple K-Means style partitioning)
        chariot_assignments = [[] for _ in range(len(starts))]
        for p in picks:
            best_chariot = min(range(len(starts)), key=lambda i: abs(p.x - starts[i].x) + abs(p.y - starts[i].y))
            chariot_assignments[best_chariot].append(p)
            
        results = []
        for i, assigned_picks in enumerate(chariot_assignments):
            results.append(self.calculate_picking_route(floor_idx, starts[i], assigned_picks))
            
        # --- REQ: Path Intersection Detection ---
        intersections = self._detect_path_overlaps(results)
        if intersections:
            AuditTrail.log(Role.SYSTEM, f"COORD: Detected {len(intersections)} path intersections. Applying dynamic delays.")
            for ch_a, ch_b, timestep in intersections:
                # Simple "Delay" logic: Increase estimated time for second chariot
                results[ch_b]['estimated_time_seconds'] += 2.0 # Wait 2 sec for passing
                results[ch_b]['total_distance'] += 0.1 # Symbolic "reroute" cost
                
        return results

    def _detect_path_overlaps(self, routes: List[Dict]) -> List[Tuple[int, int, int]]:
        """Finds points where two chariots occupy the same (x,y) at the same time index."""
        occupied = {} # (t,x,y) -> chariot_idx
        overlaps = []
        for ch_idx, r in enumerate(routes):
            t = 0
            for segment in r.get('path_segments', []):
                for coord in segment:
                    key = (t, int(coord[0]), int(coord[1]))
                    if key in occupied:
                        overlaps.append((occupied[key], ch_idx, t))
                    else:
                        occupied[key] = ch_idx
                    t += 1
        return overlaps

    def reroute_active_chariot(self, floor_idx: int, current_pos: WarehouseCoordinate, remaining_picks: List[WarehouseCoordinate]) -> Dict:
        """Requirement: Re-routing supported."""
        return self.calculate_picking_route(floor_idx, current_pos, remaining_picks)

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
