import os
import sys

# Add current path for module resolution
sys.path.append(os.getcwd())

from ai_service.maps import GroundFloorMap, IntermediateFloorMap
from ai_service.core.product_manager import ProductStorageManager
from ai_service.engine.manager import WMSOperationManager
from ai_service.engine.base import WarehouseCoordinate

def test_picking_optimization():
    print("=== STEP 8.3: PICKING OPTIMIZATION TEST ===\n")
    
    # 1. Setup Environment
    base_path = "folder_data/csv_export"
    prod_csv = os.path.join(base_path, "produits.csv")
    dem_csv = os.path.join(base_path, "historique_demande.csv")
    
    pm = ProductStorageManager(prod_csv, dem_csv)
    floors = {
        0: GroundFloorMap(),
        1: IntermediateFloorMap(1)
    }
    
    manager = WMSOperationManager(floors, pm)

    # 2. Assign some products to locations across floors
    # Let's put SKU 31336 on Floor 0 and SKU 31463 on Floor 1
    p1 = 31336
    p2 = 31463
    
    print(f"Placing products for picking test...")
    # Manual assignment for testing
    manager.confirm_placement(p1, 0, WarehouseCoordinate(25, 9))
    manager.confirm_placement(p2, 1, WarehouseCoordinate(10, 10))

    # 3. Generate Picking Order
    print(f"\nRequesting Picking Route for SKUs: {[p1, p2]}...")
    route_result = manager.generate_picking_order([p1, p2])

    if "error" in route_result:
        print(f"❌ Error: {route_result['error']}")
        return

    print(f"✅ Route Found!")
    print(f"   Total Travel Distance: {route_result['total_distance']} units")
    print(f"   Items to Collect: {route_result['items_collected']}")
    
    # Check if route visits both floors
    visited_floors = set(step['floor'] for step in route_result['route'])
    print(f"   Visited Floors: {visited_floors}")
    
    if len(visited_floors) >= 2:
        print("\n✅ Success: Multi-floor routing confirmed (visited Floor 0 and Floor 1).")
    else:
        print("\n❌ FAILED: Route did not visit multiple floors as expected.")

    # Show a few steps
    print("\n   Sample Route Steps (First 5):")
    for step in route_result['route'][:5]:
        print(f"    - Floor {step['floor']} at {step['coord']}")

if __name__ == "__main__":
    test_picking_optimization()
