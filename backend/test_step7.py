import os
import sys

# Add current path for module resolution
sys.path.append(os.getcwd())

from ai_service.maps import GroundFloorMap
from ai_service.core.storage import StorageOptimizationService
from ai_service.core.product_manager import ProductStorageManager

def test_occupancy_update():
    print("=== STEP 7: UPDATE OCCUPANCY TEST ===\n")
    
    # Setup
    base_path = "folder_data/csv_export"
    prod_csv = os.path.join(base_path, "produits.csv")
    dem_csv = os.path.join(base_path, "historique_demande.csv")
    
    pm = ProductStorageManager(prod_csv, dem_csv)
    rdc = GroundFloorMap()
    storage = StorageOptimizationService({0: rdc}, pm)

    pid = 31336 # Test product
    
    # 1. Get first suggestion
    first_result = storage.suggest_slot(pid)
    print(f"Product {pid}: First suggested slot: {first_result['slot_name']}")
    
    # 2. Assign the slot (STEP 7)
    print(f"Assigning {first_result['slot_name']} (Marking as occupied)...")
    storage.assign_slot(first_result['floor_idx'], first_result['coord'])
    
    # 3. Get next suggestion for same product (or different)
    second_result = storage.suggest_slot(pid)
    print(f"Product {pid}: Second suggested slot: {second_result['slot_name']}")
    
    if first_result['slot_name'] != second_result['slot_name']:
        print("\n✅ Success: State updated correctly. Slot was not double-assigned.")
    else:
        print("\n❌ FAILED: Algorithm suggested the same occupied slot.")

    # 4. Release and re-suggest
    print(f"\nReleasing {first_result['slot_name']}...")
    storage.release_slot(first_result['floor_idx'], first_result['coord'])
    
    third_result = storage.suggest_slot(pid)
    print(f"Product {pid}: Third suggested slot: {third_result['slot_name']}")
    
    if third_result['slot_name'] == first_result['slot_name']:
        print("✅ Success: Release function works. Best slot is available again.")

if __name__ == "__main__":
    test_occupancy_update()
