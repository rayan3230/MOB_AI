import os
import sys

# Add current path for module resolution
sys.path.append(os.getcwd())

from ai_service.maps import GroundFloorMap
from ai_service.core.storage import StorageOptimizationService
from ai_service.core.product_manager import ProductStorageManager
from ai_service.engine.base import WarehouseCoordinate

def test_slot_rebalancing():
    print("=== SLOT REBALANCING TEST ===\n")
    
    # Setup
    base_path = "folder_data/csv_export"
    prod_csv = os.path.join(base_path, "produits.csv")
    dem_csv = os.path.join(base_path, "historique_demande.csv")
    
    pm = ProductStorageManager(prod_csv, dem_csv)
    rdc = GroundFloorMap()
    storage = StorageOptimizationService({0: rdc}, pm)

    pid_hot = 31336 
    
    # 1. Assign product to a slot
    initial = storage.suggest_slot(pid_hot)
    storage.assign_slot(pid_hot, initial['floor_idx'], initial['coord'])
    print(f"Initial Assignment: SKU {pid_hot} at {initial['slot_name']}")
    
    # 2. Simulate EXTREME congestion in that slot
    print(f"Simulating heavy traffic (20 picks) at {initial['slot_name']}...")
    for _ in range(20):
        storage.record_picking_event(initial['floor_idx'], initial['coord'])
    
    # 3. Trigger rebalancing check
    print("\nRunning Rebalancing Check (Threshold: 15)...")
    suggestions = storage.check_for_rebalancing(traffic_threshold=15)
    
    if suggestions:
        for s in suggestions:
            print(f"✅ RELOCATION SUGGESTED:")
            print(f"   Product: {s['product_id']}")
            print(f"   From: Floor {s['from_floor']} {s['from_coord']}")
            print(f"   To: Floor {s['to_floor']} {s['to_coord']}")
            print(f"   Reason: {s['reason']}")
    else:
        print("❌ No relocation suggested (perhaps no better slots available or score didn't improve enough).")

if __name__ == "__main__":
    test_slot_rebalancing()
