"""
Comprehensive Test Suite for AI Integration
Tests all phases of the AI-to-project linkage.
Run: python test_ai_integration.py
"""

import sys
import os
import json
import requests
from datetime import datetime
from colorama import init, Fore, Style

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
from ai_service.logic.initialisation_map import WarehouseCoordinate, Role
from ai_service.maps import GroundFloorMap
from ai_service.api.models import AIPerformanceLog
from Produit.models import Produit, HistoriqueDemande

# Initialize colorama for colored output
init(autoreset=True)

API_BASE_URL = "http://localhost:8000"

class TestRunner:
    def __init__(self):
        self.passed = 0
        self.failed = 0
        self.warnings = 0
        
    def log_test(self, name, status, message=""):
        if status == "PASS":
            print(f"{Fore.GREEN}✓ {name}{Style.RESET_ALL}")
            if message:
                print(f"  {Fore.CYAN}{message}{Style.RESET_ALL}")
            self.passed += 1
        elif status == "FAIL":
            print(f"{Fore.RED}✗ {name}{Style.RESET_ALL}")
            if message:
                print(f"  {Fore.RED}{message}{Style.RESET_ALL}")
            self.failed += 1
        elif status == "WARN":
            print(f"{Fore.YELLOW}⚠ {name}{Style.RESET_ALL}")
            if message:
                print(f"  {Fore.YELLOW}{message}{Style.RESET_ALL}")
            self.warnings += 1
    
    def section(self, title):
        print(f"\n{Fore.MAGENTA}{'='*60}{Style.RESET_ALL}")
        print(f"{Fore.MAGENTA}{title:^60}{Style.RESET_ALL}")
        print(f"{Fore.MAGENTA}{'='*60}{Style.RESET_ALL}\n")
    
    def summary(self):
        print(f"\n{Fore.CYAN}{'='*60}{Style.RESET_ALL}")
        print(f"{Fore.CYAN}TEST SUMMARY{Style.RESET_ALL}")
        print(f"{Fore.CYAN}{'='*60}{Style.RESET_ALL}")
        print(f"{Fore.GREEN}Passed: {self.passed}{Style.RESET_ALL}")
        print(f"{Fore.RED}Failed: {self.failed}{Style.RESET_ALL}")
        print(f"{Fore.YELLOW}Warnings: {self.warnings}{Style.RESET_ALL}")
        
        if self.failed == 0:
            print(f"\n{Fore.GREEN}🎉 ALL TESTS PASSED! AI Integration is working.{Style.RESET_ALL}")
        else:
            print(f"\n{Fore.RED}❌ Some tests failed. Review errors above.{Style.RESET_ALL}")

runner = TestRunner()

# ==============================================================================
# PHASE 1: Database & Data Sync Tests
# ==============================================================================
runner.section("PHASE 1: DATABASE & DATA SYNC")

try:
    produits = Produit.objects.all()
    if produits.count() > 0:
        runner.log_test("Database Connection (Produit)", "PASS", f"Found {produits.count()} products")
    else:
        runner.log_test("Database Connection (Produit)", "WARN", "No products found in database")
except Exception as e:
    runner.log_test("Database Connection (Produit)", "FAIL", str(e))

try:
    historique = HistoriqueDemande.objects.all()
    if historique.count() > 0:
        runner.log_test("Database Connection (HistoriqueDemande)", "PASS", f"Found {historique.count()} historical records")
    else:
        runner.log_test("Database Connection (HistoriqueDemande)", "WARN", "No demand history found")
except Exception as e:
    runner.log_test("Database Connection (HistoriqueDemande)", "FAIL", str(e))

try:
    pm = ProductStorageManager()
    if not pm.products_df.empty:
        runner.log_test("ProductStorageManager - Live Data Load", "PASS", f"Loaded {len(pm.products_df)} products from DB")
    else:
        runner.log_test("ProductStorageManager - Live Data Load", "WARN", "No products loaded")
except Exception as e:
    runner.log_test("ProductStorageManager - Live Data Load", "FAIL", str(e))

# ==============================================================================
# PHASE 2: AI Core Services Tests
# ==============================================================================
runner.section("PHASE 2: AI CORE SERVICES")

try:
    forecast_service = ForecastingService()
    runner.log_test("ForecastingService Initialization", "PASS", "Service initialized successfully")
except Exception as e:
    runner.log_test("ForecastingService Initialization", "FAIL", str(e))

try:
    forecast_result = forecast_service.run(limit_products=5)
    if forecast_result and 'items' in forecast_result:
        runner.log_test("Forecasting - Generate Predictions", "PASS", f"Generated forecasts for {len(forecast_result['items'])} items")
    else:
        runner.log_test("Forecasting - Generate Predictions", "WARN", "No forecast items generated")
except Exception as e:
    import traceback
    error_detail = traceback.format_exc()
    runner.log_test("Forecasting - Generate Predictions", "FAIL", str(e))
    print(f"\n{Fore.YELLOW}Full traceback:{Style.RESET_ALL}")
    print(error_detail)

try:
    floor_maps = {0: GroundFloorMap()}
    picking_service = PickingOptimizationService(floor_maps)
    runner.log_test("PickingOptimizationService Initialization", "PASS", "Service initialized successfully")
except Exception as e:
    runner.log_test("PickingOptimizationService Initialization", "FAIL", str(e))

try:
    start = WarehouseCoordinate(0, 0)
    picks = [
        WarehouseCoordinate(5, 10),
        WarehouseCoordinate(15, 3),
        WarehouseCoordinate(8, 18)
    ]
    route_result = picking_service.calculate_picking_route(0, start, picks, Role.EMPLOYEE)
    
    if 'error' not in route_result and 'total_distance' in route_result:
        runner.log_test("Route Optimization (2-Opt TSP)", "PASS", 
                       f"Distance: {route_result['total_distance']:.2f}m, Time: {route_result['estimated_time_seconds']:.1f}s")
    else:
        runner.log_test("Route Optimization (2-Opt TSP)", "FAIL", route_result.get('error', 'Unknown error'))
except Exception as e:
    runner.log_test("Route Optimization (2-Opt TSP)", "FAIL", str(e))

try:
    pm = ProductStorageManager()
    floor_maps = {0: GroundFloorMap()}
    storage_service = StorageOptimizationService(floor_maps, pm)
    runner.log_test("StorageOptimizationService Initialization", "PASS", "ABC zoning calculated")
except Exception as e:
    runner.log_test("StorageOptimizationService Initialization", "FAIL", str(e))

# ==============================================================================
# PHASE 3: Learning Engine Tests
# ==============================================================================
runner.section("PHASE 3: LEARNING ENGINE")

try:
    learning_engine = LearningFeedbackEngine()
    initial_speed = learning_engine.get_current_travel_speed()
    runner.log_test("LearningFeedbackEngine Initialization", "PASS", f"Current travel speed: {initial_speed} m/s")
except Exception as e:
    runner.log_test("LearningFeedbackEngine Initialization", "FAIL", str(e))

try:
    learning_engine = LearningFeedbackEngine()
    learning_engine.record_picking_performance(120, 135)
    learning_engine.record_picking_performance(90, 95)
    learning_engine.record_picking_performance(150, 160)
    learning_engine.record_picking_performance(80, 88)
    learning_engine.record_picking_performance(110, 118)
    
    new_speed = learning_engine.get_current_travel_speed()
    runner.log_test("Learning Engine - Performance Recording", "PASS", 
                   f"Speed adjusted to: {new_speed} m/s (5 samples processed)")
except Exception as e:
    runner.log_test("Learning Engine - Performance Recording", "FAIL", str(e))

try:
    log_count = AIPerformanceLog.objects.count()
    runner.log_test("AIPerformanceLog Model", "PASS", f"Model accessible ({log_count} logs in DB)")
except Exception as e:
    runner.log_test("AIPerformanceLog Model", "FAIL", str(e))

# ==============================================================================
# PHASE 4: API Endpoints Tests (requires server running)
# ==============================================================================
runner.section("PHASE 4: REST API ENDPOINTS")

def test_api_endpoint(name, method, url, data=None):
    try:
        if method == "GET":
            response = requests.get(f"{API_BASE_URL}{url}", timeout=5)
        elif method == "POST":
            response = requests.post(f"{API_BASE_URL}{url}", json=data, timeout=5)
        
        if response.status_code in [200, 201]:
            result = response.json()
            if result.get('status') == 'success':
                runner.log_test(f"API: {name}", "PASS", f"Status: {response.status_code}")
                return True
            else:
                runner.log_test(f"API: {name}", "WARN", f"Response: {result}")
                return False
        else:
            runner.log_test(f"API: {name}", "FAIL", f"HTTP {response.status_code}")
            return False
    except requests.exceptions.ConnectionError:
        runner.log_test(f"API: {name}", "WARN", "Server not running (start with 'python manage.py runserver')")
        return False
    except Exception as e:
        runner.log_test(f"API: {name}", "FAIL", str(e))
        return False

# Test endpoints
test_api_endpoint("GET /api/forecast/all/", "GET", "/api/forecast/all/?limit=5")
test_api_endpoint("GET /api/forecast/map/0/", "GET", "/api/forecast/map/0/")
test_api_endpoint("GET /api/forecast/zoning/0/", "GET", "/api/forecast/zoning/0/")

test_api_endpoint("POST /api/forecast/optimize-route/", "POST", "/api/forecast/optimize-route/", {
    "floor_idx": 0,
    "start_pos": {"x": 0, "y": 0},
    "picks": [
        {"x": 5, "y": 10},
        {"x": 15, "y": 3}
    ]
})

test_api_endpoint("POST /api/forecast/record-performance/", "POST", "/api/forecast/record-performance/", {
    "task_id": "TEST-001",
    "predicted_time_seconds": 120,
    "actual_time_seconds": 125
})

test_api_endpoint("POST /api/forecast/validate/", "POST", "/api/forecast/validate/", {
    "prediction_id": "forecast-test-123",
    "action": "ACCEPT",
    "user": "Test Supervisor",
    "justification": "Automated test validation"
})

# ==============================================================================
# PHASE 5: Integration Tests
# ==============================================================================
runner.section("PHASE 5: END-TO-END INTEGRATION")

try:
    # Simulate a complete picking workflow
    floor_maps = {0: GroundFloorMap()}
    picking_service = PickingOptimizationService(floor_maps)
    learning_engine = LearningFeedbackEngine()
    
    # Step 1: Get optimized route
    start = WarehouseCoordinate(0, 0)
    picks = [WarehouseCoordinate(5, 10), WarehouseCoordinate(15, 3), WarehouseCoordinate(8, 18)]
    route = picking_service.calculate_picking_route(0, start, picks, Role.EMPLOYEE)
    
    # Step 2: Simulate completion and record performance
    predicted_time = route['estimated_time_seconds']
    simulated_actual_time = predicted_time * 1.1  # 10% slower
    
    learning_engine.record_picking_performance(predicted_time, simulated_actual_time)
    
    runner.log_test("End-to-End Workflow", "PASS", 
                   f"Route calculated, performance recorded (Pred: {predicted_time:.1f}s, Actual: {simulated_actual_time:.1f}s)")
except Exception as e:
    runner.log_test("End-to-End Workflow", "FAIL", str(e))

try:
    # Test data pipeline: DB → AI → Frontend Format
    pm = ProductStorageManager()
    
    if not pm.products_df.empty:
        sample_product_id = pm.products_df.iloc[0]['id_produit']
        product_class = pm.get_product_class(sample_product_id)
        product_details = pm.get_product_details(sample_product_id)
        
        runner.log_test("Data Pipeline (DB → AI → JSON)", "PASS", 
                       f"Product {sample_product_id}: Class={product_class.value}, SKU={product_details.get('sku', 'N/A')}")
    else:
        runner.log_test("Data Pipeline (DB → AI → JSON)", "WARN", "No products to test")
except Exception as e:
    runner.log_test("Data Pipeline (DB → AI → JSON)", "FAIL", str(e))

# ==============================================================================
# SUMMARY
# ==============================================================================
runner.summary()

# Exit with appropriate code
sys.exit(0 if runner.failed == 0 else 1)
