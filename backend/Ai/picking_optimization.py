import heapq
from typing import List, Tuple, Dict, Optional, Union
import sys
import os

# Add parent directory to path to allow absolute imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from initialisation_map import DepotB7Map, WarehouseCoordinate, PickingOptimizationService
except ImportError:
    from .initialisation_map import DepotB7Map, WarehouseCoordinate, PickingOptimizationService

class PickingOrder:
    def __init__(self, order_id: str, items: List[WarehouseCoordinate]):
        self.order_id = order_id
        self.items = items

class AStarPathfinder:
    def __init__(self, warehouse_map: DepotB7Map):
        self.map = warehouse_map
        self.graph = warehouse_map.walkable_graph

    def heuristic(self, a: Tuple[int, int], b: Tuple[int, int]) -> int:
        """Manhattan distance as heuristic for A*"""
        return abs(a[0] - b[0]) + abs(a[1] - b[1])

    def find_nearest_walkable(self, coord: Tuple[int, int], search_radius: int = 5) -> Optional[Tuple[int, int]]:
        """
        Step 9: Handle edge case where target is just inside a rack/blocked.
        Search nearby for the closest valid walkable coordinate.
        """
        if coord in self.graph:
            return coord
            
        print(f"Sourcing nearest walkable for {coord}...")
        # Search in a concentric square pattern
        for r in range(1, search_radius + 1):
            for dx in range(-r, r + 1):
                for dy in range(-r, r + 1):
                    neighbor = (coord[0] + dx, coord[1] + dy)
                    if neighbor in self.graph:
                        print(f"Snapped {coord} to {neighbor}")
                        return neighbor
        return None

    def find_path(self, start: Tuple[int, int], goal: Tuple[int, int]) -> Tuple[Optional[List[Tuple[int, int]]], float]:
        """
        Computes the true shortest path using A* search algorithm.
        Step 9: Includes logic to handle start/goal outside walkable graph.
        """
        # STEP 9: Attempt to snap to nearest walkable point if blocked
        adj_start = self.find_nearest_walkable(start)
        adj_goal = self.find_nearest_walkable(goal)
        
        if adj_start is None or adj_goal is None:
            print(f"CRITICAL: Start {start} or Goal {goal} is completely inaccessible!")
            return None, float('inf')

        frontier = []
        heapq.heappush(frontier, (0, adj_start))
        came_from = {adj_start: None}
        cost_so_far = {adj_start: 0}

        while frontier:
            current = heapq.heappop(frontier)[1]

            if current == adj_goal:
                break

            for neighbor in self.graph.get(current, []):
                # STEP 3.1: f(n) = g(n) + h(n)
                g_n = cost_so_far[current] + 1  # Actual cost from start (Step 3.1)
                h_n = self.heuristic(neighbor, adj_goal) # Manhattan heuristic (Step 3.1)
                
                if neighbor not in cost_so_far or g_n < cost_so_far[neighbor]:
                    cost_so_far[neighbor] = g_n
                    f_n = g_n + h_n  # Total estimated cost
                    heapq.heappush(frontier, (f_n, neighbor))
                    came_from[neighbor] = current

        if adj_goal not in cost_so_far:
            return None, float('inf')

        # Reconstruct path
        path = []
        curr = adj_goal
        while curr is not None:
            path.append(curr)
            curr = came_from[curr]
        path.reverse()
        
        # STEP 4: Validate Path Constraints
        if self.validate_path(path):
            return path, float(cost_so_far[adj_goal])
        else:
            return None, float('inf')

    def validate_path(self, path: List[Tuple[int, int]]) -> bool:
        """
        Final safety check for Step 4.
        Ensures none of the path nodes invade forbidden territories:
        - Pillars/Walls
        - Rack Bodies
        - Special Walls
        """
        for node in path:
            coord = WarehouseCoordinate(node[0], node[1])
            if not self.map.is_walkable(coord):
                print(f"PATH ERROR: Node {node} violates constraints!")
                return False
        return True

class AdvancedPickingService(PickingOptimizationService):
    """
    Enhanced Picking Service using A* true shortest path 
    instead of Manhattan heuristics.
    """
    def __init__(self, warehouse_map: DepotB7Map):
        super().__init__(warehouse_map)
        self.pathfinder = AStarPathfinder(warehouse_map)
        # STEP 5: Distance cache (start, end) -> distance
        self.distance_cache: Dict[Tuple[Tuple[int, int], Tuple[int, int]], float] = {}

    def get_cached_distance(self, start: Tuple[int, int], end: Tuple[int, int]) -> float:
        """Helper for Step 5: Retrieves or computes true distance with caching."""
        if start == end:
            return 0.0
        
        # Sort tuple to treat path (A,B) same as (B,A) for undirected uniform cost
        path_key = tuple(sorted([start, end]))
        if path_key in self.distance_cache:
            return self.distance_cache[path_key]
            
        _, cost = self.pathfinder.find_path(start, end)
        self.distance_cache[path_key] = cost
        return cost

    def build_distance_matrix(self, items_coords: List[WarehouseCoordinate], start_coord: WarehouseCoordinate) -> List[List[float]]:
        
        final_output = {
            "timestamp": os.getlogin(), # Or current time
            "chariots": {}
        }
        
        for c_id, (path, kpis) in results.items():
            final_output["chariots"][f"Chariot_{c_id}"] = {
                "sequence": [self.warehouse.get_slot_name(p) for p in path],
                "coordinates": [p.to_tuple() for p in path],
                "metrics": kpis
            }
            
        return final_output

    def get_cached_distance(self, start: Tuple[int, int], end: Tuple[int, int]) -> float:
        """Helper for Step 5: Retrieves or computes true distance with caching."""
        if start == end:
            return 0.0
        
        # Sort tuple to treat path (A,B) same as (B,A) for undirected uniform cost
        path_key = tuple(sorted([start, end]))
        if path_key in self.distance_cache:
            return self.distance_cache[path_key]
            
        _, cost = self.pathfinder.find_path(start, end)
        self.distance_cache[path_key] = cost
        return cost

    def build_distance_matrix(self, items_coords: List[WarehouseCoordinate], start_coord: WarehouseCoordinate) -> List[List[float]]:
        """
        STEP 5: Build Distance Matrix for N items.
        Store in matrix D.
        """
        all_points = [start_coord] + items_coords
        n = len(all_points)
        # Initialize matrix D
        distance_matrix = [[0.0 for _ in range(n)] for _ in range(n)]
        
        print(f"--- Building Distance Matrix for {len(items_coords)} items ---")
        for i in range(n):
            for j in range(i + 1, n):
                dist = self.get_cached_distance(all_points[i].to_tuple(), all_points[j].to_tuple())
                distance_matrix[i][j] = dist
                distance_matrix[j][i] = dist # Symmetrical
                
        return distance_matrix

    def calculate_true_distance(self, start: WarehouseCoordinate, end: WarehouseCoordinate) -> float:
        return self.get_cached_distance(start.to_tuple(), end.to_tuple())

    def compute_kpis(self, full_path_nodes: List[Tuple[int, int]], item_count: int) -> Dict[str, Union[float, int]]:
        """
        STEP 7: Compute KPIs for a calculated picking route.
        """
        # Constants
        WALKING_SPEED = 1.0  # meters per second
        PICK_TIME_PER_ITEM = 15  # seconds
        
        # 1. Total Path Distance
        total_distance = float(len(full_path_nodes) - 1) if full_path_nodes else 0.0
        
        # 2. Number of turns
        turns = 0
        if len(full_path_nodes) > 2:
            for i in range(1, len(full_path_nodes) - 1):
                prev = full_path_nodes[i-1]
                curr = full_path_nodes[i]
                next_node = full_path_nodes[i+1]
                
                # Check if direction changed
                if (curr[0] - prev[0], curr[1] - prev[1]) != (next_node[0] - curr[0], next_node[1] - curr[1]):
                    turns += 1
        
        # 3. Estimated travel time
        travel_time = total_distance / WALKING_SPEED
        
        # 4. Total picking duration
        picking_effort = item_count * PICK_TIME_PER_ITEM
        total_duration = travel_time + picking_effort
        
        return {
            "total_distance": total_distance,
            "turns": turns,
            "travel_time_seconds": travel_time,
            "total_duration_seconds": total_duration,
            "item_count": item_count
        }

    def optimize_picking_path(self, items_coords: List[WarehouseCoordinate], chariot_id: int = 1) -> Tuple[List[WarehouseCoordinate], Dict]:
        """
        Optimizes picking path using True Shortest Path (A*) logic.
        Step 9: Handle blocked paths or invalid coordinates gracefully.
        """
        start_key = f"Chariot Start {chariot_id}"
        start_coord = self.warehouse_map.landmarks.get(start_key, self.warehouse_map.landmarks.get("Bureau"))
        
        current_coord = start_coord
        order = []
        full_path_nodes = []
        remaining = list(items_coords)
        blocked_items = []
        
        print(f"--- Starting Advanced picking (A*) - Chariot {chariot_id} ---")
        
        while remaining:
            # Finds nearest item based on TRUE graph distance
            best_next = None
            min_dist = float('inf')
            best_path = None
            
            for item in remaining:
                path, cost = self.pathfinder.find_path(current_coord.to_tuple(), item.to_tuple())
                if path and cost < min_dist:
                    min_dist = cost
                    best_next = item
                    best_path = path
            
            if best_next is None:
                # Step 9: Re-routing failed for these items
                print(f"WARNING: No path found to remaining {len(remaining)} items. They might be blocked.")
                blocked_items.extend(remaining)
                break
                
            # Valid path found
            if full_path_nodes:
                full_path_nodes.extend(best_path[1:]) 
            else:
                full_path_nodes.extend(best_path)
            
            print(f"Next stop: {self.warehouse_map.get_slot_name(best_next)} (Cost: {min_dist}m)")
            order.append(best_next)
            remaining.remove(best_next)
            current_coord = best_next
            
        kpis = self.compute_kpis(full_path_nodes, len(order))
        kpis["blocked_item_count"] = len(blocked_items)
        kpis["blocked_items"] = [self.warehouse_map.get_slot_name(i) for i in blocked_items]
        
        return order, kpis

    def distribute_to_chariots(self, batch_items: List[WarehouseCoordinate], chariot_count: int = 2) -> Dict[int, Tuple[List[WarehouseCoordinate], Dict]]:
        """
        STEP 9: Multi-Chariot Logic.
        Splits a batch of items between multiple chariots and optimizes each path.
        """
        print(f"\n--- STEP 9: Distributing {len(batch_items)} items to {chariot_count} chariots ---")
        
        # Simple distribution: divide list (could be improved with K-means or balanced clustering)
        # We start by grouping items near each chariot's start
        chariot_assignments = {i: [] for i in range(1, chariot_count + 1)}
        
        # Greedy assignment based on proximity to start landmarks
        for item in batch_items:
            best_chp = 1
            min_start_dist = float('inf')
            for c_id in range(1, chariot_count + 1):
                start_coord = self.warehouse_map.landmarks.get(f"Chariot Start {c_id}", self.warehouse_map.landmarks.get("Bureau"))
                dist = self.calculate_true_distance(start_coord, item)
                if dist < min_start_dist:
                    min_start_dist = dist
                    best_chp = c_id
            chariot_assignments[best_chp].append(item)
            
        results = {}
        for c_id, items in chariot_assignments.items():
            if not items:
                results[c_id] = ([], {"total_distance": 0, "item_count": 0})
                continue
            path, kpis = self.optimize_picking_path(items, chariot_id=c_id)
            results[c_id] = (path, kpis)
            
        return results

    def batch_and_cluster_orders(self, orders: List[PickingOrder]) -> List[WarehouseCoordinate]:
        """
        STEP 8: Multi-Order Optimization.
        1. Merge SKU lists from multiple orders.
        2. Cluster by proximity/zone.
        """
        print(f"\n--- STEP 8: Batching {len(orders)} Orders ---")
        
        # 1. Merge SKU lists
        merged_items = []
        for order in orders:
            merged_items.extend(order.items)
            
        # Remove duplicates (if the same SKU is in multiple orders)
        unique_items = []
        seen = set()
        for item in merged_items:
            # Using tuple as coordinate identity
            coord_tuple = item.to_tuple()
            if coord_tuple not in seen:
                unique_items.append(item)
                seen.add(coord_tuple)
        
        # 2. Cluster by Zone (or simple proximity)
        # We'll use a simple sorting by Y then X to group by aisles/zones roughly
        # but a better clustering would use the actual graph distance or zone name.
        
        def get_zone_priority(coord: WarehouseCoordinate):
            # Try to identify which rack zone the item is in
            for name, coords in self.warehouse_map.zones.items():
                segments = coords if isinstance(coords, list) else [coords]
                for (x1, y1, x2, y2) in segments:
                    if x1 <= coord.x < x2 and y1 <= coord.y < y2:
                        return name
            return "Aisle"

        # Sort items by zone to group them for the picker
        # This reduces "traveling back and forth" between distant sectors
        unique_items.sort(key=lambda c: (get_zone_priority(c), c.y, c.x))
        
        print(f"Batching complete. Total unique pick locations: {len(unique_items)}")
        return unique_items

class DepotB7Engine:
    """
    🎯 FINAL ARCHITECTURE: Core WMS Engine for Depot B7.
    Integrates Layout, Navigation, Optimization, and Edge-Case Handling.
    Now supports Multi-Floor logic (Ground, 1st, 2nd).
    """
    def __init__(self, current_floor: int = 0):
        # 1. INITIALIZATION: Build Map for specific floor, Matrices, and Graph
        self.floor_index = current_floor
        self.warehouse = DepotB7Map(floor_index=current_floor)
        
        # 2. ALGORITHMS: A* Pathfinder and Advanced Logic Service
        self.pathfinder = AStarPathfinder(self.warehouse)
        self.service = AdvancedPickingService(self.warehouse)

    def process_picking_batch(self, skus: List[Tuple[int, int]], chariot_count: int = 2) -> Dict:
        """
        🎯 RUNTIME WORKFLOW:
        1. Receive picking list (SKUs as coordinates)
        2. Compute A* distances (with cached lookup)
        3. Solve TSP approximation (distributed routing)
        4. Output ordered coordinates + full metrics
        """
        # Convert raw coordinates to WarehouseCoordinate objects
        warehouse_coords = [WarehouseCoordinate(x, y) for (x, y) in skus]
        
        # Distribute and Optimize across multiple chariots
        results = self.service.distribute_to_chariots(warehouse_coords, chariot_count=chariot_count)
        
        final_output = {
            "summary": {
                "total_items": len(skus),
                "chariot_count": chariot_count
            },
            "chariots": {}
        }
        
        for c_id, (path, kpis) in results.items():
            final_output["chariots"][f"Chariot_{c_id}"] = {
                "sequence": [self.warehouse.get_slot_name(p) for p in path],
                "coordinates": [p.to_tuple() for p in path],
                "metrics": kpis
            }
            
        return final_output

if __name__ == "__main__":
    # Quick test if run standalone
    try:
        from initialisation_map import Role
    except ImportError:
        from .initialisation_map import Role
    test_map = DepotB7Map()
    service = AdvancedPickingService(test_map)
    
    # Sample items to pick (Walkable coordinates)
    items = [
        WarehouseCoordinate(10, 12),
        WarehouseCoordinate(2, 22),
        WarehouseCoordinate(20, 25)
    ]
    
    # Demonstrate Step 5: Distance Matrix
    start_pos = test_map.landmarks["Chariot Start 1"]
    matrix = service.build_distance_matrix(items, start_pos)
    print("\nDistance Matrix D (Step 5):")
    for row in matrix:
        print([f"{d:.1f}" for d in row])
    
    optimized, kpis = service.optimize_picking_path(items, chariot_id=1)
    print(f"\nFinal Optimized Order: {[test_map.get_slot_name(i) for i in optimized]}")
    
    # Demonstrate Step 8: Multi-Order Batching (Using Walkable coordinates near racks)
    order1 = PickingOrder("ORD-001", [WarehouseCoordinate(10, 12), WarehouseCoordinate(12, 12)])
    order2 = PickingOrder("ORD-002", [WarehouseCoordinate(4, 12), WarehouseCoordinate(15, 12)])
    
    batched_items = service.batch_and_cluster_orders([order1, order2])
    batched_optimized, batched_kpis = service.optimize_picking_path(batched_items, chariot_id=2)
    
    print("\n--- Batch Route KPIs (Step 8) ---")
    print(f"Total Distance: {batched_kpis['total_distance']:.1f}m")
    print(f"Improvement vs Individual: Calculating...")
    
    print("\n--- Route KPIs (Step 7) ---")
    print(f"Total Distance: {kpis['total_distance']:.1f}m")
    print(f"Total Turns: {kpis['turns']}")
    print(f"Est. Travel Time: {kpis['travel_time_seconds']:.1f}s")
    print(f"Total Session Duration: {kpis['total_duration_seconds']:.1f}s")
    print(f"Improvement vs Naive: {kpis['improvement_pct']:.1f}%")
