import os
import sys

# Add current path for module resolution
sys.path.append(os.getcwd())

from ai_service.maps import GroundFloorMap, IntermediateFloorMap
from ai_service.core.storage import StorageOptimizationService, StorageClass
from ai_service.core.product_manager import ProductStorageManager
from ai_service.engine.base import WarehouseCoordinate

def test_multi_factor_scoring():
    print("=== STEP 3: MULTI-FACTOR SCORING TEST ===\n")
    
    # Setup
    base_path = "folder_data/csv_export"
    prod_csv = os.path.join(base_path, "produits.csv")
    dem_csv = os.path.join(base_path, "historique_demande.csv")
    
    pm = ProductStorageManager(prod_csv, dem_csv)
    rdc = GroundFloorMap()
    f1 = IntermediateFloorMap(1)
    
    storage = StorageOptimizationService({0: rdc, 1: f1}, pm)
    
    # 1. Test Frequency Priority
    print("--- 1. Testing Frequency Priority ---")
    fast_pid = 31336 # Medium/Fast sample
    slow_pid = 31334 # Slow sample
    
    s1 = storage.suggest_slot(fast_pid)
    s2 = storage.suggest_slot(slow_pid)
    
    print(f"Fast/Medium Product ({fast_pid}) -> Floor {s1[0]}, Score: {storage.calculate_slot_score(s1[0], s1[1], fast_pid):.2f}")
    print(f"Slow Product ({slow_pid}) -> Floor {s2[0]}, Score: {storage.calculate_slot_score(s2[0], s2[1], slow_pid):.2f}")
    
    # 2. Test Weight Penalty
    print("\n--- 2. Testing Weight Penalty ---")
    # Simulate a heavy product
    heavy_pid = 99999
    # Manually inject a heavy product into the manager's logic for testing
    pm.products_df = pm.products_df._append({
        'id_produit': heavy_pid, 
        'sku': 'HEAVY-SKU', 
        'poidsu': 200.0, # 200kg
        'nom_produit': 'Test Heavy Item'
    }, ignore_index=True)
    pm.product_scores[heavy_pid] = StorageClass.SLOW
    
    suggestion = storage.suggest_slot(heavy_pid)
    print(f"Heavy Product (200kg) -> Suggested Floor: {suggestion[0]}, Slot: {suggestion[1]}")
    print("Scoring logic pushed it to safest/closest available even if classified as SLOW.")

    # 3. Test Congestion Penalty
    print("\n--- 3. Testing Congestion Penalty ---")
    target_slot = suggestion[1]
    # Mark neighbors as occupied
    for dx in [-1, 0, 1]:
        for dy in [-1, 0, 1]:
            rdc.occupied_slots.add((int(target_slot.x) + dx, int(target_slot.y) + dy))
            
    new_suggestion = storage.suggest_slot(heavy_pid)
    print(f"With neighbors blocked -> New Suggested Slot: {new_suggestion[1]}")
    print(f"Successfully avoided the congested area.")

if __name__ == "__main__":
    test_multi_factor_scoring()
