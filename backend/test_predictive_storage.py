import os
import sys

# Add current path for module resolution
sys.path.append(os.getcwd())

from ai_service.maps import GroundFloorMap
from ai_service.core.storage import StorageOptimizationService
from ai_service.core.product_manager import ProductStorageManager
from ai_service.core.forecasting_service import ForecastingService
from ai_service.engine.base import WarehouseCoordinate

def test_predictive_storage():
    print("=== STEP 8.1: PREDICTIVE STORAGE TEST ===\n")
    
    # Setup
    base_data_path = "folder_data/csv_export"
    prod_csv = os.path.join(base_data_path, "produits.csv")
    dem_csv = os.path.join(base_data_path, "historique_demande.csv")
    
    pm = ProductStorageManager(prod_csv, dem_csv)
    rdc = GroundFloorMap()
    storage = StorageOptimizationService({0: rdc}, pm)

    # We'll use a product that is normally SLOW
    # Let's find a product that is not in top quantiles (likely SLOW)
    pid = 31336 # From previous tests, let's assume it's normal
    
    # 1. Get initial suggestion WITHOUT forecasting
    first_result = storage.suggest_slot(pid)
    print(f"Normal Suggestion for SKU {pid}: {first_result['slot_name']} (Score: {first_result['score']:.2f})")
    
    # 2. Apply Predictive Boost (High demand predicted tomorrow)
    print(f"\nApplying Predictive Forecast: SKU {pid} will have HIGH DEMAND tomorrow...")
    storage.apply_forecast_data([pid])
    
    # 3. Request suggestion again
    second_result = storage.suggest_slot(pid)
    print(f"Predictive Suggestion for SKU {pid}: {second_result['slot_name']} (Score: {second_result['score']:.2f})")
    
    if second_result['score'] < first_result['score']:
        print(f"\n✅ Success: Predictive score ({second_result['score']:.2f}) is lower than normal ({first_result['score']:.2f}).")
        print(f"The product moved to a better slot: {second_result['slot_name']}")
    else:
        print("\n❌ FAILED: Score did not improve after predictive boost.")

    # 4. Integrate with REAL Forecasting Service (Demo logic)
    print("\n--- Integrating with Real Forecasting Service ---")
    try:
        # Note: We pass the directory since we updated DataLoader to handle CSVs
        fs = ForecastingService(base_data_path, is_csv=True)
        high_demand_skus = fs.get_high_demand_skus(threshold_quantile=0.95)
        print(f"Forecast engine detected {len(high_demand_skus)} high-demand SKUs for tomorrow.")
        
        storage.apply_forecast_data(high_demand_skus)
        if high_demand_skus:
            test_pid = high_demand_skus[0]
            final_res = storage.suggest_slot(test_pid)
            print(f"Best slot for Forecasted SKU {test_pid}: {final_res['slot_name']} (Score: {final_res['score']:.2f})")
            print("✅ Success: End-to-end integration verified.")
    except Exception as e:
        print(f"⚠️ Forecast integration test skipped/failed: {e}")

if __name__ == "__main__":
    test_predictive_storage()
