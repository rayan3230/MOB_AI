import os
import django
import sys
from datetime import datetime

# Setup Django
sys.path.append(r'c:\Users\hp\OneDrive\Bureau\MOB_AI\backend')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')
django.setup()

from ai_service.core.forecasting_service import ForecastingService
from ai_service.core.storage import StorageOptimizationService
from ai_service.core.product_manager import ProductStorageManager
from ai_service.maps import GroundFloorMap, IntermediateFloorMap, UpperFloorMap

print("--- INITIALIZING AI SERVICES ---")
fs = ForecastingService()
pm = ProductStorageManager()
floor_maps = {0: GroundFloorMap(), 1: IntermediateFloorMap(1), 2: UpperFloorMap(2)}
ss = StorageOptimizationService(floor_maps, pm)

print("\n--- AI DEMAND PREDICTIONS (REPLENISHMENT) ---")
forecasts = fs.get_all_forecasts_raw(limit_products=5)
if not forecasts:
    print("No forecasts generated. Check history.")
for pid, data in forecasts.items():
    print(f"SKU {pid}: Forecast -> {data['forecast']} units | Confidence: {data['confidence']}%")
    print(f"  Reasoning: {data['reasoning']}")

print("\n--- AI STORAGE ACTIONS (RELOCATIONS/ZONING) ---")
# Check a few product classes
skus_to_check = [31334, 31335, 31779]
for sku in skus_to_check:
    p_class = pm.get_product_class(sku)
    print(f"SKU {sku}: Classified as {p_class.name} (Optimal zone based on turnover)")

print("\n--- AI REBALANCING (SIMULATED CONGESTION) ---")
# Simulate high traffic at a specific location to force a relocation suggestion
from ai_service.engine.base import WarehouseCoordinate
hot_coord = WarehouseCoordinate(5, 5) # Assume a slot is here
# Record 20 events to trigger threshold
for _ in range(20):
    ss.record_picking_event(0, hot_coord)

# Map a product to this slot
ss.slot_to_product[(0, 5, 5)] = 31779 

suggestions = ss.check_for_rebalancing(traffic_threshold=10)
if not suggestions:
    print("No immediate relocations needed.")
else:
    for sug in suggestions:
        print(f"🚀 ACTION: RELOCATE SKU {sug['product_id']}")
        print(f"  FROM: {sug['from_coord']} (Overcrowded Area)")
        print(f"  TO:   {sug['to_coord']} (Optimal Quiet Zone)")
        print(f"  WHY:  {sug['reason']}")

print("\n--- AI REPLENISHMENT PLAN ---")
for pid, data in forecasts.items():
    print(f"📦 ACTION: REPLENISH SKU {pid} -> Order {data['forecast']} units")
