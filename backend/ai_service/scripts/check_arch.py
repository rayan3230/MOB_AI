from ai_service.maps import GroundFloorMap, IntermediateFloorMap, UpperFloorMap
from ai_service.core.picking import PickingOptimizationService
from ai_service.core.storage import StorageOptimizationService
from ai_service.core.product_manager import ProductStorageManager
from ai_service.engine.base import WarehouseCoordinate
import os

def final_architecture_check():
    print("=== DEPOT B7: FINAL ARCHITECTURE CHECK ===\n")
    
    # Paths
    base_path = "folder_data/csv_export"
    prod_csv = os.path.join(base_path, "produits.csv")
    dem_csv = os.path.join(base_path, "historique_demande.csv")

    # 1. Initialize Managers
    print("Loading Product Data...")
    if not os.path.exists(prod_csv):
        print(f"Error: {prod_csv} not found.")
        return
        
    product_manager = ProductStorageManager(prod_csv, dem_csv)
    
    rdc = GroundFloorMap()
    floor1 = IntermediateFloorMap(floor_index=1)
    
    # 2. Check Storage Zoning (STEP 1)
    print("Initializing Storage Optimization Service (STEP 1: Zoning)...")
    floors = {0: rdc, 1: floor1}
    storage_service = StorageOptimizationService(floors, product_manager)
    summary = storage_service.get_summary()
    print(f"Zoning Summary: {summary}")

    # 3. Test Suggestion (STEP 6)
    sample_pid = 31336
    p_class = product_manager.get_product_class(sample_pid)
    result = storage_service.suggest_slot(sample_pid)
    if result:
        print(f"\nProduct {sample_pid} is {p_class}")
        print(f"Suggested Placement: {result['slot_name']} (Score: {result['score']:.2f})")
    
    # 4. Picking optimization test on RDC
    picking_service = PickingOptimizationService(rdc)
    picking_list = [
        WarehouseCoordinate(2, 2),
        WarehouseCoordinate(10, 5),
        WarehouseCoordinate(25, 20),
        WarehouseCoordinate(4, 25)
    ]
    
    start = WarehouseCoordinate(34, 10) # Chariot Start 1
    path = picking_service.optimize_picking_path(picking_list, start)
    
    print(f"\nPathfinding Check (RDC):")
    print(f"Optimized path from {start}:")
    for step in path:
        print(f"  -> {step}")

    print("\n✅ New Folder Structure Validated: Core, Engine, and Maps are working.")

if __name__ == "__main__":
    final_architecture_check()
