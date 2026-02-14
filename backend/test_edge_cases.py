import sys
import os
import unittest
from datetime import datetime

# Ensure imports work from backend root
sys.path.append(os.getcwd())

from ai_service.engine.base import Role, WarehouseCoordinate, DepotB7Map, AuditTrail, ZoneType
from ai_service.core.forecasting_service import ForecastingService
from ai_service.core.storage import StorageOptimizationService
from ai_service.core.picking_service import PickingOptimizationService
from ai_service.core.product_manager import ProductStorageManager
from ai_service.maps import GroundFloorMap

class TestWarehouseEdgeCases(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Setup basic digital twin
        cls.rdc = GroundFloorMap()
        cls.pm = ProductStorageManager(
            products_csv="folder_data/csv_cleaned/produits.csv",
            demand_csv="folder_data/csv_cleaned/historique_demande.csv"
        )
        cls.storage = StorageOptimizationService({0: cls.rdc}, cls.pm)
        cls.picking = PickingOptimizationService({0: cls.rdc})

    def test_01_all_skus_high_demand(self):
        print("\n[TEST] Scenario: All SKUs High Demand")
        all_skus = list(range(1, 100))
        self.storage.apply_forecast_data(all_skus)
        
        # Suggest for a random SKU
        sku = 50
        suggestion = self.storage.suggest_slot(sku)
        self.assertIsNotNone(suggestion, "Failed to suggest slot when all SKUs are high demand")
        print(f"      ✅ OK: Suggested {suggestion['slot_id']} with score {suggestion['score']:.2f}")

    def test_02_all_skus_low_demand(self):
        print("\n[TEST] Scenario: All SKUs Low Demand")
        self.storage.apply_forecast_data([])
        
        sku = 50
        suggestion = self.storage.suggest_slot(sku)
        self.assertIsNotNone(suggestion, "Failed to suggest slot when all SKUs are low demand")
        print(f"      ✅ OK: Suggested {suggestion['slot_id']} with score {suggestion['score']:.2f}")

    def test_03_no_valid_slot_scenario(self):
        print("\n[TEST] Scenario: No Valid Slot (Full Warehouse)")
        # Create a tiny map and fill it
        tiny_map = DepotB7Map(5, 5, floor_index=99)
        # Add a storage zone
        tiny_map.zones = {"Small Rack": (0, 0, 5, 5)}
        tiny_map.zone_types = {"Small Rack": ZoneType.STORAGE}
        tiny_map._precompute_matrices()
        
        tiny_storage = StorageOptimizationService({99: tiny_map}, self.pm)
        
        # Fill all 25 slots
        for x in range(5):
            for y in range(5):
                tiny_storage.assign_slot(100, 99, WarehouseCoordinate(x, y))
        
        # Try to suggest one more
        suggestion = tiny_storage.suggest_slot(101)
        self.assertIsNone(suggestion, "Should not return a slot for a full warehouse")
        print("      ✅ OK: System gracefully returned None for full warehouse.")

    def test_04_blocked_path_scenario(self):
        print("\n[TEST] Scenario: Blocked Path (Coord in Pillar)")
        start = WarehouseCoordinate(34, 10) # Expedition
        # Coordinate (11, 7) is a pillar in GroundFloorMap
        blocked_target = WarehouseCoordinate(11, 7) 
        
        route = self.picking.calculate_picking_route(0, start, [blocked_target], user_role=Role.SYSTEM)
        
        # Requirement: System finds nearest walkable edge or falls back to Manhattan
        self.assertGreater(route['total_distance'], 0, "Distance should be calculated via fallback or nearest neighbor")
        self.assertIn(blocked_target, route['route_sequence'], "The target should still be in sequence (as a logical destination)")
        print(f"      ✅ OK: System handled blocked target at {blocked_target} with distance {route['total_distance']}m")

    def test_05_invalid_coordinate_scenario(self):
        print("\n[TEST] Scenario: Invalid Coordinates (Out of Bounds)")
        start = WarehouseCoordinate(34, 10)
        out_of_bounds = WarehouseCoordinate(500, 500)
        
        route = self.picking.calculate_picking_route(0, start, [out_of_bounds], user_role=Role.SYSTEM)
        self.assertGreater(route['total_distance'], 0)
        self.assertEqual(len(route['route_sequence']), 1)
        print(f"      ✅ OK: System handled out-of-bounds coordinate with Manhattan fallback (Dist: {route['total_distance']}m).")

    def test_06_manual_override_governance(self):
        print("\n[TEST] Scenario: Manual Override RBAC")
        sku = 12345
        coord = WarehouseCoordinate(10, 10)
        
        # 1. Employee tries (should fail)
        print("      Testing Employee override (Expected: PermissionError)...")
        with self.assertRaises(PermissionError):
            self.storage.manual_override_placement(sku, 0, coord, Role.EMPLOYEE, "I want this here.")
        
        # 2. Supervisor tries with short justification (should fail)
        print("      Testing Supervisor with short justification (Expected: ValueError)...")
        with self.assertRaises(ValueError):
            self.storage.manual_override_placement(sku, 0, coord, Role.SUPERVISOR, "Short.")
            
        # 3. Supervisor tries with valid justification (should succeed)
        print("      Testing Supervisor with valid justification (Expected: Success)...")
        success = self.storage.manual_override_placement(sku, 0, coord, Role.SUPERVISOR, "Valid longer justification for override.")
        self.assertTrue(success)
        print("      ✅ OK: Governance controls enforced correctly.")

if __name__ == "__main__":
    unittest.main()
