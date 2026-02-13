import os
import sys

# Add current path for module resolution
sys.path.append(os.getcwd())

from ai_service.maps import GroundFloorMap
from ai_service.core.storage import StorageOptimizationService, StorageClass
from ai_service.core.product_manager import ProductStorageManager
from ai_service.engine.base import WarehouseCoordinate

def test_business_constraints():
    print("=== STEP 5: BUSINESS CONSTRAINTS TEST ===\n")
    
    # Setup
    base_path = "folder_data/csv_export"
    prod_csv = os.path.join(base_path, "produits.csv")
    dem_csv = os.path.join(base_path, "historique_demande.csv")
    
    pm = ProductStorageManager(prod_csv, dem_csv)
    rdc = GroundFloorMap()
    storage = StorageOptimizationService({0: rdc}, pm)

    # 1. Hazardous Item Test
    print("--- 1. Testing Hazardous Item Restriction ---")
    haz_pid = 90001
    pm.products_df = pm.products_df._append({
        'id_produit': haz_pid, 
        'sku': 'HAZ-SKU', 
        'categorie': 'CHIMIE', 
        'nom_produit': 'Sulfuric Acid'
    }, ignore_index=True)
    pm.product_scores[haz_pid] = StorageClass.FAST # Usually FAST, but haz constraint should win
    
    suggestion = storage.suggest_slot(haz_pid)
    print(f"Hazardous Product Category: CHIMIE")
    print(f"Suggested Slot: {suggestion[1]}")
    
    # Verify it is in Zone Spec or Rack X
    in_safe_zone = False
    for name, coords in rdc.zones.items():
        if any(k in name for k in ["Zone Spec", "Rack X"]):
            segments = coords if isinstance(coords, list) else [coords]
            for (x1, y1, x2, y2) in segments:
                if x1 <= suggestion[1].x < x2 and y1 <= suggestion[1].y < y2:
                    in_safe_zone = True
                    print(f"Confirmed: Slot is within {name}")
    if not in_safe_zone:
        print("❌ FAILED: Hazardous item placed in non-safe zone.")

    # 2. Fragile Item Test
    print("\n--- 2. Testing Fragile Item Restriction ---")
    fragile_pid = 90002
    pm.products_df = pm.products_df._append({
        'id_produit': fragile_pid, 
        'sku': 'FRAG-SKU', 
        'categorie': 'DECORATION', 
        'nom_produit': 'MIROIR DESIGN'
    }, ignore_index=True)
    pm.product_scores[fragile_pid] = StorageClass.FAST # Usually FAST, but fragile constraint should avoid high traffic
    
    suggestion = storage.suggest_slot(fragile_pid)
    dist = storage.slot_distance_scores[0].get((int(suggestion[1].x), int(suggestion[1].y)))
    print(f"Fragile Product Name: MIROIR DESIGN (Category: DECORATION)")
    print(f"Suggested Slot: {suggestion[1]}, Distance: {dist:.2f}m")
    
    if dist >= 15.0:
        print("✅ Success: Fragile item avoided high-traffic zone (Distance >= 15m).")
    else:
        print("❌ FAILED: Fragile item placed in high-traffic zone.")

if __name__ == "__main__":
    test_business_constraints()
