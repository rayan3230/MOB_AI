import os
import sys

# Add current path for module resolution
sys.path.append(os.getcwd())

from ai_service.maps import GroundFloorMap
from ai_service.core.storage import StorageOptimizationService
from ai_service.core.product_manager import ProductStorageManager
from ai_service.engine.base import WarehouseCoordinate

def test_dynamic_heatmap():
    print("=== STEP 8: DYNAMIC HEATMAP TEST ===\n")
    
    # Setup
    base_path = "folder_data/csv_export"
    prod_csv = os.path.join(base_path, "produits.csv")
    dem_csv = os.path.join(base_path, "historique_demande.csv")
    
    pm = ProductStorageManager(prod_csv, dem_csv)
    rdc = GroundFloorMap()
    storage = StorageOptimizationService({0: rdc}, pm)

    pid = 31336 # Test product
    
    # 1. Get initial suggestion
    first_result = storage.suggest_slot(pid)
    print(f"Initial Suggestion: {first_result['slot_name']} (Score: {first_result['score']:.2f})")
    
    # 2. Simulate high traffic in that specific slot
    print(f"\nSimulating high traffic (10 picking events) for {first_result['slot_name']}...")
    for _ in range(10):
        storage.record_picking_event(first_result['floor_idx'], first_result['coord'])
    
    # 3. Request suggestion again
    second_result = storage.suggest_slot(pid)
    print(f"Suggestion after traffic: {second_result['slot_name']} (Score: {second_result['score']:.2f})")
    
    # NEW: Check the score of the ORIGINAL slot to see if penalty applied
    original_slot_new_score = storage.calculate_slot_score(first_result['floor_idx'], first_result['coord'], pid)
    print(f"Original Slot ({first_result['slot_name']}) New Score: {original_slot_new_score:.2f}")

    if original_slot_new_score > first_result['score']:
        print(f"\n✅ Success: Penalty applied! {first_result['slot_name']} score increased from {first_result['score']:.2f} to {original_slot_new_score:.2f}")
    else:
        print("\n❌ FAILED: Penalty NOT applied.")

    if first_result['slot_name'] != second_result['slot_name']:
         print("✅ Success: The algorithm rerouted to a lower-traffic slot.")
    else:
         print("ℹ️ Note: The algorithm still preferred the same slot (likely still the best even with traffic penalty).")

if __name__ == "__main__":
    test_dynamic_heatmap()
