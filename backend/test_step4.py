import os
import sys

# Add current path for module resolution
sys.path.append(os.getcwd())

from ai_service.maps import GroundFloorMap
from ai_service.core.storage import StorageOptimizationService
from ai_service.core.product_manager import ProductStorageManager
from ai_service.engine.base import WarehouseCoordinate

def test_filtering():
    print("=== STEP 4: FILTERING CANDIDATE SLOTS TEST ===\n")
    
    # Setup
    base_path = "folder_data/csv_export"
    prod_csv = os.path.join(base_path, "produits.csv")
    dem_csv = os.path.join(base_path, "historique_demande.csv")
    
    pm = ProductStorageManager(prod_csv, dem_csv)
    rdc = GroundFloorMap()
    
    storage = StorageOptimizationService({0: rdc}, pm)
    
    # 1. Test Pillar Filtering
    # Choose a coordinate known to have a pillar (e.g., 11, 7 on RDC)
    pillar_coord = WarehouseCoordinate(11, 7)
    print(f"Checking Pillar at {pillar_coord}:")
    is_available = rdc.is_slot_available(pillar_coord)
    print(f"  Is available in Map? {is_available} (Expected: False)")
    
    # Observe if any suggestion ever picks a pillar
    # We can try to force a check on all suggestions
    found_pillar_in_suggestions = False
    for pid in pm.products_df['id_produit'].head(50):
        s = storage.suggest_slot(pid)
        if s and int(s[1].x) == 11 and int(s[1].y) == 7:
            found_pillar_in_suggestions = True
            break
    print(f"  Found pillars in 50 random suggestions? {found_pillar_in_suggestions} (Expected: False)")

    # 2. Test Reserved Zone Filtering
    # (25, 25) is in the "Reserved" zone on RDC
    reserved_coord = WarehouseCoordinate(25, 25)
    print(f"\nChecking Reserved Zone at {reserved_coord}:")
    is_prohibited = storage._is_in_prohibited_zone(rdc, reserved_coord)
    print(f"  Is prohibited in Storage Service? {is_prohibited} (Expected: True)")
    
    # 3. Test Occupied Slot Filtering
    # Suggest a slot, mark it as occupied, then suggest again
    pid = 31336
    first_suggestion = storage.suggest_slot(pid)
    print(f"\nFirst suggestion for {pid}: {first_suggestion[1]}")
    
    # Occupy it
    rdc.occupied_slots.add((int(first_suggestion[1].x), int(first_suggestion[1].y)))
    
    second_suggestion = storage.suggest_slot(pid)
    print(f"Second suggestion for {pid}: {second_suggestion[1]}")
    
    if first_suggestion[1] != second_suggestion[1]:
        print("✅ Correctly avoided recently occupied slot.")
    else:
        print("❌ Failed to avoid occupied slot.")

if __name__ == "__main__":
    test_filtering()
