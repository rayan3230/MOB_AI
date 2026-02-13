import sys
import os

# Add the current directory to path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from initialisation_map import DepotB7Map, WarehouseCoordinate
from picking_optimization import AStarPathfinder, AdvancedPickingService, PickingOrder

def run_step_9_demo():
    print("=== DEPOT B7: STEP 9 - EDGE CASES & MULTI-CHARIOT DEMO ===\n")
    
    # 1. Initialize Map and Service
    warehouse = DepotB7Map()
    warehouse.build_walkable_graph() # Ensure graph is built
    service = AdvancedPickingService(warehouse)
    
    # 2. Test Cases for Step 9:
    # A. One item is exactly inside a pillar (x=16, y=13) - should snap to neighbor
    # B. One item is deep inside a rack
    # C. Standard items
    
    items = [
        WarehouseCoordinate(16, 13), # Inside Pillar (Blocked)
        WarehouseCoordinate(5, 5),   # Inside Rack H
        WarehouseCoordinate(10, 10), # Random point
        WarehouseCoordinate(25, 20), # Near Rack R
        WarehouseCoordinate(38, 5),  # Bureau/Expedition area
        WarehouseCoordinate(2, 25)   # Far corner (Rack G)
    ]
    
    print(f"Testing with {len(items)} items, including blocked coordinates.")
    
    # 3. Multi-Chariot Distribution (Step 9.3)
    multi_results = service.distribute_to_chariots(items, chariot_count=2)
    
    total_meters = 0
    total_items = 0
    
    for c_id, (path, kpis) in multi_results.items():
        print(f"\n--- Results for Chariot {c_id} ---")
        if not path:
            print("No items assigned or all items blocked.")
            continue
            
        print(f"Items picked ({kpis['item_count']}): {[warehouse.get_slot_name(i) for i in path]}")
        print(f"Total Distance: {kpis['total_distance']}m")
        print(f"Turns: {kpis['turns']}")
        print(f"Blocked Items: {kpis['blocked_items']}")
        
        total_meters += kpis['total_distance']
        total_items += kpis['item_count']

    print(f"\nGLOBAL SUMMARY:")
    print(f"Total Workflow Distance: {total_meters:.2f}m")
    print(f"Total Successful Picks: {total_items}")

if __name__ == "__main__":
    run_step_9_demo()
