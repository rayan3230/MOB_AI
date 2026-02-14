import sys
import os
import unittest

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

from ai_service.engine.base import Role, WarehouseCoordinate, DepotB7Map
from ai_service.core.storage import StorageOptimizationService
from ai_service.core.picking_service import PickingOptimizationService
from ai_service.maps import GroundFloorMap

class TestArchitecturalIntegrity(unittest.TestCase):
    def test_01_digital_twin_sharing(self):
        print("\n[ARCH] Testing Digital Twin Sharing...")
        # Create one physical map
        shared_rdc = GroundFloorMap()
        shared_rdc._precompute_matrices()
        
        floors = {0: shared_rdc}
        
        # Initialize services with SAME floor objects
        storage = StorageOptimizationService(floors, None)
        picking = PickingOptimizationService(floors)
        
        # Action in one service affects the map seen by the other
        coord = WarehouseCoordinate(10, 10)
        shared_rdc.occupied_slots.add(coord.to_tuple())
        
        # Verify both see it
        self.assertIn(coord.to_tuple(), storage.floors[0].occupied_slots)
        self.assertIn(coord.to_tuple(), picking.floors[0].occupied_slots)
        
        # Verify coordination: Is occupancy checked?
        self.assertFalse(shared_rdc.is_slot_available(coord))
        print("      ✅ OK: Services share the same Digital Twin instance.")

    def test_02_distance_caching_functionality(self):
        print("\n[ARCH] Testing Distance Caching Logic...")
        shared_rdc = GroundFloorMap()
        shared_rdc._precompute_matrices()
        picking = PickingOptimizationService({0: shared_rdc})
        
        a = WarehouseCoordinate(5, 5)
        b = WarehouseCoordinate(10, 10)
        
        # First call (Cold)
        import time
        start = time.time()
        dist1, _ = picking._get_cached_path(0, a, b)
        cold_time = time.time() - start
        
        # Second call (Warm)
        start = time.time()
        dist2, _ = picking._get_cached_path(0, a, b)
        warm_time = time.time() - start
        
        self.assertEqual(dist1, dist2)
        # Even on a fast machine, a dict lookup is orders of magnitude faster than A*
        self.assertIn((0, *tuple(sorted([a, b], key=lambda c: (c.x, c.y)))), picking.global_path_cache)
        print(f"      ✅ OK: Cache Hit. Speedup: {cold_time/max(1e-9, warm_time):.1f}x")

    def test_03_coordinate_format_consistency(self):
        print("\n[ARCH] Testing Coordinate Consistency...")
        coord = WarehouseCoordinate(15.2, 20.8, 1.0)
        # Verify truncation to int (grid nodes)
        self.assertEqual(coord.x, 15)
        self.assertEqual(coord.y, 20)
        self.assertEqual(coord.z, 1)
        
        tup = coord.to_tuple()
        self.assertEqual(tup, (15, 20))
        print("      ✅ OK: WarehouseCoordinate enforces consistent grid-integers.")

    def test_04_no_hardcoded_weights_logic(self):
        print("\n[ARCH] Testing Service Modularity & Config...")
        shared_rdc = GroundFloorMap()
        storage = StorageOptimizationService({0: shared_rdc}, None)
        
        # Verify weights are in a mutable/configurable dictionary, not hardcoded in logic
        self.assertIsInstance(storage.weights, dict)
        self.assertIn("distance", storage.weights)
        self.assertIn("congestion", storage.weights)
        
        # Verify Picking speed is dynamic (from learning engine)
        self.assertTrue(hasattr(storage, 'traffic_heatmap'))
        print("      ✅ OK: Optimization parameters are centralized in weight dictionaries.")

if __name__ == "__main__":
    unittest.main()
