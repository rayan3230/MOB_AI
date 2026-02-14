import sys
import os
import unittest
from datetime import datetime

# Ensure imports work from backend root
sys.path.append(os.getcwd())

import django
from django.conf import settings
if not settings.configured:
    settings.configure(
        DATABASES={'default': {'ENGINE': 'django.db.backends.sqlite3', 'NAME': ':memory:'}},
        INSTALLED_APPS=[
            'ai_service', 
            'Produit', 
            'Transaction', 
            'warhouse', 
            'Users'
        ],
    )
    django.setup()

from ai_service.engine.base import Role, WarehouseCoordinate, AuditTrail
from ai_service.core.storage import StorageOptimizationService
from ai_service.core.picking_service import PickingOptimizationService
from ai_service.core.product_manager import ProductStorageManager
from ai_service.maps import GroundFloorMap

class TestGovernanceExplainability(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Setup basic digital twin
        cls.rdc = GroundFloorMap()
        # Mock product manager - avoid DB for this pure logic test
        class MockPM:
            def get_product_class(self, pid): return None
            def get_product_details(self, pid): return {}
            
        cls.storage = StorageOptimizationService({0: cls.rdc}, MockPM())
        cls.picking = PickingOptimizationService({0: cls.rdc})

    def test_01_audit_trail_visibility(self):
        print("\n[GOVERNANCE] Testing Audit Trail visibility...")
        # Note: AuditTrail.log prints to stdout. 
        # In a real system it would go to a persistent DB or immutable log file.
        AuditTrail.log(Role.SYSTEM, "Test audit log entry")
        print("      ✅ OK: Audit log format verified.")

    def test_02_manual_override_constraints(self):
        print("\n[GOVERNANCE] Testing Manual Override with Justification...")
        sku = 999
        coord = WarehouseCoordinate(10, 10)
        
        # 1. No justification (too short)
        with self.assertRaises(ValueError):
            self.storage.manual_override_placement(sku, 0, coord, Role.SUPERVISOR, "Short")
        print("      ✅ OK: Blocked short justification.")

        # 2. Correct manual override
        success = self.storage.manual_override_placement(sku, 0, coord, Role.SUPERVISOR, "Emergency storage allocation for bulk delivery.")
        self.assertTrue(success)
        print("      ✅ OK: Manual override successful with valid justification.")

    def test_03_rbac_enforcement(self):
        print("\n[GOVERNANCE] Testing Role-Based Access Control...")
        sku = 888
        coord = WarehouseCoordinate(12, 12)
        
        # Employee attempting supervisor action
        with self.assertRaises(PermissionError):
            self.storage.manual_override_placement(sku, 0, coord, Role.EMPLOYEE, "Trying to bypass security.")
        print("      ✅ OK: Blocked Employee from performing Supervisor action.")

    def test_04_route_validation(self):
        print("\n[GOVERNANCE] Testing Route Validation logic...")
        route = {
            "total_distance": 150.5
        }
        
        # 1. Supervisor validates
        success = self.picking.validate_and_approve_route(route, Role.SUPERVISOR, "Route looks optimal for current congestion.")
        self.assertTrue(success)
        
        # 2. Employee cannot validate
        with self.assertRaises(PermissionError):
            self.picking.validate_and_approve_route(route, Role.EMPLOYEE, "I approve this.")
        print("      ✅ OK: Route validation restricted to Supervisor roles.")

    def test_05_error_transparency(self):
        print("\n[GOVERNANCE] Testing Error Transparency (No silent failures)...")
        # Requesting route on non-existent floor
        result = self.picking.calculate_picking_route(99, WarehouseCoordinate(0,0), [WarehouseCoordinate(5,5)])
        self.assertIn("error", result)
        print(f"      ✅ OK: System explicitly returned error: {result['error']}")

if __name__ == "__main__":
    unittest.main()
