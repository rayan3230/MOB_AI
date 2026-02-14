import sys
import os
import matplotlib.pyplot as plt

# Add backend to sys.path
sys.path.append(os.getcwd())

from ai_service.maps import GroundFloorMap, IntermediateFloorMap
from ai_service.core.storage import StorageOptimizationService
from ai_service.core.product_manager import ProductStorageManager

def show_zoning():
    base_path = "folder_data/csv_export"
    prod_csv = os.path.join(base_path, "produits.csv")
    dem_csv = os.path.join(base_path, "historique_demande.csv")

    pm = ProductStorageManager(prod_csv, dem_csv)
    rdc = GroundFloorMap()
    f1 = IntermediateFloorMap(floor_index=1)
    
    storage = StorageOptimizationService({0: rdc, 1: f1}, pm)
    
    print("Generating Storage Zoning Maps...")
    print("Green = FAST, Yellow = MEDIUM, Red = SLOW")
    
    storage.visualize_zoning(0) # Ground floor
    # storage.visualize_zoning(1) # Floor 1

if __name__ == "__main__":
    show_zoning()
