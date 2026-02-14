
import os
import sys
import django

# Setup path and django
sys.path.append(os.getcwd())
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')
django.setup()

from ai_service.maps.floor_0_rdc import GroundFloorMap
from ai_service.engine.base import WarehouseCoordinate
from ai_service.core.picking_service import PickingOptimizationService

def test_astar_obstacle_avoidance():
    print("\n--- Testing A* Obstacle Avoidance ---")
    map_obj = GroundFloorMap()
    
    # Racks are at x=10, 11.
    # We want to go from aisle x=9 to aisle x=12.
    # The shortest path should go around the rack, either at y=0 or y=11.
    start = WarehouseCoordinate(9, 5)
    end = WarehouseCoordinate(12, 5)
    
    path = map_obj.find_path_astar(start, end)
    
    if path:
        print(f"Path found from {start} to {end}")
        # Check if any point in path is inside the rack (10, y) or (11, y) where 1 <= y < 11
        invalid_points = [p for p in path if 10 <= p[0] <= 11 and 1 <= p[1] < 11]
        if invalid_points:
            print(f"ERROR: A* path goes through a rack! Points: {invalid_points}")
        else:
            # Manhattan dist is 3. Path must be longer.
            # (9,5) -> (9,0) -> (12,0) -> (12,5) = 5+3+5 = 13 steps.
            # or (9,5) -> (9,11) -> (12,11) -> (12,5) = 6+3+6 = 15 steps.
            print(f"Path length: {len(path)} - Success! Obstacles avoided.")
    else:
        print("ERROR: No path found between reachable cells.")

def test_2opt_efficiency():
    print("\n--- Testing 2-Opt Efficiency ---")
    map_obj = GroundFloorMap()
    service = PickingOptimizationService(floors={0: map_obj})
    
    # Points in a sequence that's poorly ordered for greedy
    start_pos = WarehouseCoordinate(34, 10) # Chariot Start 1
    
    points = [
        WarehouseCoordinate(13, 12),
        WarehouseCoordinate(8, 12),
        WarehouseCoordinate(13, 1),
        WarehouseCoordinate(8, 1),
    ]
    
    # floor_idx, start_coord, picks
    result = service.calculate_picking_route(0, start_pos, points)
    
    if "error" in result:
        print(f"ERROR: {result['error']}")
        return

    print(f"Optimal distance: {result['total_distance']:.2f}m")
    # Time is in seconds in the actual implementation
    print(f"Estimated time: {result['estimated_time_seconds'] / 60:.2f} min")
    print(f"Tour sequence: {result['route_sequence']}")
    
    dist = result['total_distance']
    # Check if time logic is correct: dist / speed
    expected_time_s = dist / service.travel_speed
    if abs(result['estimated_time_seconds'] - expected_time_s) < 0.1:
        print("Estimated time calculation: Verified.")
    else:
        print(f"ERROR: Time calculation mismatch. Expected {expected_time_s}, got {result['estimated_time_seconds']}")

def test_rack_access():
    print("\n--- Testing Rack Access (Nearest Walkable Neighbor Logic) ---")
    map_obj = GroundFloorMap()
    # Zone 'V' is at (4, 1, 5, 11). Coordinate (4, 5) is NOT walkable.
    target = WarehouseCoordinate(4, 5) # Inside rack V
    start = WarehouseCoordinate(8, 5) # In aisle
    
    path = map_obj.find_path_astar(start, target)
    if path:
        print(f"Path to rack found: {path[0]} -> ... -> {path[-1]}")
        # Path[-1] is (int(x), int(y))
        end_coord = WarehouseCoordinate(path[-1][0], path[-1][1])
        if map_obj.is_walkable(end_coord):
            print(f"Verified: Target {target} adjusted to nearest walkable space {end_coord}.")
        else:
            print(f"ERROR: End of path {end_coord} is still not walkable!")
    else:
        print("ERROR: Failed to find path to rack.")

if __name__ == "__main__":
    test_astar_obstacle_avoidance()
    test_2opt_efficiency()
    test_rack_access()
