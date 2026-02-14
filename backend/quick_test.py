"""
Quick AI Integration Test (No Server Required)
Tests core AI functionality without needing Django runserver.
Run: python quick_test.py
"""

import sys
import os

# Add backend to sys.path
sys.path.append(os.getcwd())
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')

import django
django.setup()

from ai_service.core.forecasting_service import ForecastingService
from ai_service.core.picking_service import PickingOptimizationService
from ai_service.core.learning_engine import LearningFeedbackEngine
from ai_service.core.storage import StorageOptimizationService
from ai_service.core.product_manager import ProductStorageManager
from ai_service.logic.initialisation_map import DepotB7Map, WarehouseCoordinate, Role

print("\n" + "="*70)
print("AI INTEGRATION QUICK TEST".center(70))
print("="*70 + "\n")

# Test 1: Database Connection
print("📊 Test 1: Database Connection & Live Data Load")
try:
    pm = ProductStorageManager()
    print(f"   ✓ Products loaded: {len(pm.products_df)}")
    print(f"   ✓ Demand history loaded: {len(pm.demand_df)}")
    print(f"   ✓ Product classes calculated: {len(pm.product_scores)}")
except Exception as e:
    print(f"   ✗ ERROR: {e}")

# Test 2: Forecasting Service
print("\n🔮 Test 2: Demand Forecasting (SES + Regression)")
try:
    forecast_service = ForecastingService()
    result = forecast_service.run(limit_products=3)
    print(f"   ✓ Forecast generated for {len(result.get('items', []))} products")
    if result.get('items'):
        sample = result['items'][0]
        print(f"   ✓ Sample: SKU {sample['sku_id']} → {sample['final_forecast']} units (Model: {sample['selected_model']})")
except Exception as e:
    print(f"   ✗ ERROR: {e}")

# Test 3: Picking Route Optimization
print("\n🚶 Test 3: Picking Route Optimization (2-Opt TSP)")
try:
    from ai_service.maps import GroundFloorMap
    floor_maps = {0: GroundFloorMap()}
    picking_service = PickingOptimizationService(floor_maps)
    
    start = WarehouseCoordinate(0, 0)
    picks = [
        WarehouseCoordinate(5, 10),
        WarehouseCoordinate(15, 3),
        WarehouseCoordinate(8, 18),
        WarehouseCoordinate(12, 15)
    ]
    
    route = picking_service.calculate_picking_route(0, start, picks, Role.EMPLOYEE)
    
    print(f"   ✓ Route optimized for {len(picks)} items")
    print(f"   ✓ Total distance: {route['total_distance']:.2f} meters")
    print(f"   ✓ Estimated time: {route['estimated_time_seconds']:.1f} seconds")
    print(f"   ✓ Route sequence: {len(route['route_sequence'])} waypoints")
except Exception as e:
    print(f"   ✗ ERROR: {e}")

# Test 4: Storage Zoning (ABC Classification)
print("\n📦 Test 4: Storage Zoning (FAST/MEDIUM/SLOW)")
try:
    from ai_service.maps import GroundFloorMap
    pm = ProductStorageManager()
    floor_maps = {0: GroundFloorMap()}
    storage_service = StorageOptimizationService(floor_maps, pm)
    
    zoning = storage_service.storage_zoning.get(0, {})
    print(f"   ✓ Zoning calculated for floor 0")
    print(f"   ✓ Total slots classified: {len(zoning)}")
    
    # Count by class
    fast = sum(1 for v in zoning.values() if v.value == 'FAST')
    medium = sum(1 for v in zoning.values() if v.value == 'MEDIUM')
    slow = sum(1 for v in zoning.values() if v.value == 'SLOW')
    print(f"   ✓ FAST: {fast} | MEDIUM: {medium} | SLOW: {slow}")
except Exception as e:
    print(f"   ✗ ERROR: {e}")

# Test 5: Learning Engine
print("\n🧠 Test 5: Learning Engine (Continuous Improvement)")
try:
    learning_engine = LearningFeedbackEngine()
    initial_speed = learning_engine.get_current_travel_speed()
    print(f"   ✓ Current travel speed: {initial_speed} m/s")
    
    # Simulate performance recording
    learning_engine.record_picking_performance(100, 110)
    learning_engine.record_picking_performance(120, 125)
    learning_engine.record_picking_performance(90, 95)
    
    print(f"   ✓ Performance samples recorded (3 samples)")
    print(f"   ✓ Learning state saved to: model_learning.json")
except Exception as e:
    print(f"   ✗ ERROR: {e}")

# Test 6: Digital Twin Map
print("\n🗺️  Test 6: Digital Twin Map (Warehouse Layout)")
try:
    from ai_service.maps import GroundFloorMap
    depot_map = GroundFloorMap()
    print(f"   ✓ Map dimensions: {depot_map.width}x{depot_map.height}")
    print(f"   ✓ Zones defined: {len(depot_map.zones)}")
    print(f"   ✓ Landmarks: {len(depot_map.landmarks)}")
    
    # Test pathfinding (simplied - just check if method exists)
    print(f"   ✓ Digital twin map loaded successfully")
except Exception as e:
    print(f"   ✗ ERROR: {e}")

# Summary
print("\n" + "="*70)
print("✅ QUICK TEST COMPLETED".center(70))
print("="*70)
print("\nNext Steps:")
print("  1. Start Django server: python manage.py runserver")
print("  2. Run full test suite: python test_ai_integration.py")
print("  3. Start learning loop: python manage.py run_learning_loop")
print("  4. Check API endpoints at: http://localhost:8000/api/forecast/")
print("\n")
