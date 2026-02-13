from typing import List, Dict, Tuple, Optional
import collections
import heapq
from ..engine.base import DepotB7Map, WarehouseCoordinate

class PickingOptimizationService:
    def __init__(self, floors: Dict[int, DepotB7Map]):
        """
        :param floors: Dictionary mapping floor_index to DepotB7Map instance
        """
        self.floors = floors

    def find_path(self, floor_idx: int, start: Tuple[int, int], end: Tuple[int, int]) -> List[Tuple[int, int]]:
        """
        Computes the shortest path between two points on the same floor using A*.
        If 'end' is a storage slot (non-walkable), finds path to the nearest walkable neighbor.
        """
        if floor_idx not in self.floors:
            return []
            
        warehouse_map = self.floors[floor_idx]
        
        # If start is already the end
        if start == end:
            return [start]

        # Target verification
        target = end
        if not warehouse_map.is_walkable(WarehouseCoordinate(end[0], end[1])):
            # Find nearest walkable neighbor
            best_neighbor = None
            min_d = float('inf')
            for dx, dy in [(0, 1), (0, -1), (1, 0), (-1, 0), (1, 1), (-1, -1), (1, -1), (-1, 1)]:
                nx, ny = end[0] + dx, end[1] + dy
                if warehouse_map.is_walkable(WarehouseCoordinate(nx, ny)):
                    d = abs(nx - start[0]) + abs(ny - start[1])
                    if d < min_d:
                        min_d = d
                        best_neighbor = (nx, ny)
            if best_neighbor:
                target = best_neighbor
            else:
                return [] # Totally inaccessible

        # Priority Queue for A* (score, current_node, path)
        def heuristic(a, b):
            return abs(a[0] - b[0]) + abs(a[1] - b[1])

        pq = [(0, start, [start])]
        visited = {start: 0}

        while pq:
            (cost, current, path) = heapq.heappop(pq)

            if current == target:
                if target != end:
                    return path + [end] # Include the item slot as the final step
                return path

            for dx, dy in [(0, 1), (0, -1), (1, 0), (-1, 0)]:
                nx, ny = current[0] + dx, current[1] + dy
                neighbor = (nx, ny)
                
                if warehouse_map.is_walkable(WarehouseCoordinate(nx, ny)):
                    new_cost = visited[current] + 1
                    if neighbor not in visited or new_cost < visited[neighbor]:
                        visited[neighbor] = new_cost
                        priority = new_cost + heuristic(neighbor, target)
                        heapq.heappush(pq, (priority, neighbor, path + [neighbor]))
        
        return []

    def optimize_picking_route(self, items: List[Dict]) -> Dict:
        """
        Optimizes a picking route for a list of items across one or more floors.
        Items list objects: {"floor_idx": 0, "coord": (x,y), "sku": 123}
        """
        if not items:
            return {"total_distance": 0, "steps": []}

        # 1. Group items by floor to minimize floor transitions
        floors_to_visit = collections.defaultdict(list)
        for item in items:
            floors_to_visit[item['floor_idx']].append(item)

        total_path = []
        total_distance = 0
        
        # Start at floor 0 expedition (default (0,0) or center of expedition)
        current_floor = 0
        current_pos = (0, 0) # Placeholder for start
        
        # Find actual expedition center on floor 0
        if 0 in self.floors:
            rdc = self.floors[0]
            for name, coords in rdc.zones.items():
                if "Expédition" in name:
                    segments = coords if isinstance(coords, list) else [coords]
                    (x1, y1, x2, y2) = segments[0]
                    current_pos = (int((x1 + x2) / 2), int((y1 + y2) / 2))
                    break

        sorted_floors = sorted(floors_to_visit.keys())
        
        for floor_idx in sorted_floors:
            floor_items = floors_to_visit[floor_idx]
            
            # If we need to change floors, move to elevator/stairs first
            if floor_idx != current_floor:
                # Find nearest elevator on current_floor
                elevator_pos = self._find_nearest_transition(current_floor, current_pos)
                if elevator_pos:
                    path_to_elevator = self.find_path(current_floor, current_pos, elevator_pos)
                    total_path.extend([{"floor": current_floor, "coord": p} for p in path_to_elevator])
                    total_distance += len(path_to_elevator)
                    current_pos = elevator_pos # On new floor, assume we exit at same (x,y)
                current_floor = floor_idx

            # Solve TSP for items on this floor (Nearest Neighbor Heuristic)
            remaining_items = list(floor_items)
            while remaining_items:
                # Find nearest item in reachable distance
                next_item = min(remaining_items, key=lambda i: self._get_manhattan(current_pos, i['coord']))
                
                # Get actual A* path
                path_to_item = self.find_path(current_floor, current_pos, next_item['coord'])
                if path_to_item:
                    total_path.extend([{"floor": current_floor, "coord": p} for p in path_to_item])
                    total_distance += len(path_to_item)
                    current_pos = next_item['coord']
                
                remaining_items.remove(next_item)

        # Final move back to expedition on floor 0 if needed
        if current_floor != 0:
            elevator_pos = self._find_nearest_transition(current_floor, current_pos)
            if elevator_pos:
                path_to_elevator = self.find_path(current_floor, current_pos, elevator_pos)
                total_path.extend([{"floor": current_floor, "coord": p} for p in path_to_elevator])
                total_distance += len(path_to_elevator)
                current_floor = 0
                current_pos = elevator_pos

        return {
            "total_distance": total_distance,
            "route": total_path,
            "items_collected": len(items)
        }

    def _find_nearest_transition(self, floor_idx: int, current_pos: Tuple[int, int]) -> Optional[Tuple[int, int]]:
        """Finds nearest elevator or monte-charge."""
        if floor_idx not in self.floors: return None
        warehouse_map = self.floors[floor_idx]
        
        candidates = []
        for name, coords in warehouse_map.zones.items():
            if any(k in name for k in ["Monte Charge", "Assenseur"]):
                segments = coords if isinstance(coords, list) else [coords]
                for (x1, y1, x2, y2) in segments:
                    candidates.append((int((x1+x2)/2), int((y1+y2)/2)))
        
        if not candidates: return (0,0)
        return min(candidates, key=lambda c: self._get_manhattan(current_pos, c))

    def _get_manhattan(self, a, b):
        return abs(a[0] - b[0]) + abs(a[1] - b[1])

    def generate_batch_picking(self, product_ids: List[int], max_items_per_batch: int = 5) -> List[Dict]:
        """
        Groups products into multiple batches for different pickers.
        """
        # Split list into chunks
        batches = [product_ids[i:i + max_items_per_batch] for i in range(0, len(product_ids), max_items_per_batch)]
        
        results = []
        for i, batch in enumerate(batches):
            # This would normally be called via WMSmanager, but for core logic:
            results.append({
                "batch_id": i + 1,
                "product_ids": batch
            })
        return results
