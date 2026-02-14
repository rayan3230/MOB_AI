import sys
import os
import time

# Ensure imports work from backend root
sys.path.append(os.getcwd())

from ai_service.engine.base import Role, WarehouseCoordinate, DepotB7Map, AuditTrail
from ai_service.core.forecasting_service import ForecastingService
from ai_service.core.storage import StorageOptimizationService
from ai_service.core.picking_service import PickingOptimizationService
from ai_service.core.product_manager import ProductStorageManager
from ai_service.maps import GroundFloorMap

def demo_master_workflow():
    print("\n" + "="*60)
    print("      FLOWLOGIX AI MASTER DEMO: END-TO-END WORKFLOW")
    print("="*60 + "\n")

    # 1. PREPARATION & INITIALIZATION
    print("[1/5] INITIALIZATION: Building Digital Twin...")
    rdc = GroundFloorMap()
    pm = ProductStorageManager(
        products_csv="folder_data/csv_cleaned/produits.csv",
        demand_csv="folder_data/csv_cleaned/historique_demande.csv"
    )
    storage = StorageOptimizationService({0: rdc}, pm)
    picking = PickingOptimizationService({0: rdc})
    print("      ✅ Digital Twin Map Loaded (RDC: 42x27)")
    print("      ✅ Product Metadata & Demand History Loaded.")

    # 2. FORECASTING
    print("\n[2/5] FORECASTING: Running Predictive Engine...")
    forecaster = ForecastingService(data_path="folder_data/csv_cleaned/", is_csv=True)
    high_demand_skus = forecaster.get_high_demand_skus(threshold_quantile=0.95)[:5]
    storage.apply_forecast_data(high_demand_skus)
    print(f"      ✅ Forecast Complete. High-Demand SKUs identified: {high_demand_skus}")
    print("      ✅ Integrating forecasts into Storage scoring weights.")

    # 3. STORAGE OPTIMIZATION
    print("\n[3/5] STORAGE: Calculating Optimal Placements...")
    # Simulate placing one high-demand item and one standard item
    high_sku = high_demand_skus[0] if high_demand_skus else 1
    std_sku = 999
    
    suggestion_high = storage.suggest_slot(high_sku, user_role=Role.SYSTEM)
    suggestion_std = storage.suggest_slot(std_sku, user_role=Role.SYSTEM)
    
    print(f"      ✅ High-Demand SKU {high_sku} -> Suggesting Slot: {suggestion_high['slot_id']} (Priority Cost)")
    print(f"      ✅ Standard SKU {std_sku} -> Suggesting Slot: {suggestion_std['slot_id']}")

    # 4. PICKING & NAVIGATION
    print("\n[4/5] PICKING: Optimizing Preparation Routes...")
    # Targets for the picking mission
    start = WarehouseCoordinate(34, 10) # Expedition Area
    pick_targets = [
        WarehouseCoordinate(10, 5),
        WarehouseCoordinate(5, 15),
        WarehouseCoordinate(25, 5)
    ]
    
    route = picking.calculate_picking_route(0, start, pick_targets, user_role=Role.SYSTEM)
    print(f"      ✅ TSP Route Optimized (2-Opt). Total Dist: {route['total_distance']:.1f}m")
    print(f"      ✅ Estimated Prep Time: {route['estimated_time_seconds']/60:.2f} minutes.")
    print(f"      ✅ Path Sequence: {' -> '.join([str(p) for p in route['route_sequence']])}")

    # 5. VALIDATION & GOVERNANCE
    print("\n[5/5] VALIDATION: Checking Audit Trail & Governance...")
    try:
        # Simulate a manual override by a supervisor
        storage.manual_override_placement(std_sku, 0, WarehouseCoordinate(2, 2), Role.SUPERVISOR, "Emergency re-stocking for VIP client.")
        print("      ✅ Supervisor Manual Override: VALIDATED")
    except Exception as e:
        print(f"      ❌ Governance Check Failed: {e}")

    print("\n" + "="*60)
    print("               DEMO STATUS: READY FOR PRESENTATION")
    print("="*60 + "\n")

if __name__ == "__main__":
    demo_master_workflow()
