import os
import sys

# Add current path for module resolution
sys.path.append(os.getcwd())

from ai_service.maps import GroundFloorMap, IntermediateFloorMap
from ai_service.core.storage import StorageOptimizationService
from ai_service.core.product_manager import ProductStorageManager

def test_ranking_and_output():
    print("=== STEP 6: RANKING AND FORMATTED OUTPUT TEST ===\n")
    
    # Setup
    base_path = "folder_data/csv_export"
    prod_csv = os.path.join(base_path, "produits.csv")
    dem_csv = os.path.join(base_path, "historique_demande.csv")
    
    pm = ProductStorageManager(prod_csv, dem_csv)
    rdc = GroundFloorMap()
    f1 = IntermediateFloorMap(1)
    storage = StorageOptimizationService({0: rdc, 1: f1}, pm)

    # Test some products
    sample_products = [31334, 31336, 31340]
    
    for pid in sample_products:
        p_name = pm.get_product_details(pid).get('nom_produit', 'Unknown')[:30]
        result = storage.suggest_slot(pid)
        
        if result:
            print(f"Product ID: {pid} ({p_name}...)")
            print(f"  > Suggested Slot: {result['slot_name']}")
            print(f"  > Score: {result['score']:.2f}")
            print(f"  > Floor: {result['floor_idx']}")
            print(f"  > Class: {result['class'].value}\n")

if __name__ == "__main__":
    test_ranking_and_output()
