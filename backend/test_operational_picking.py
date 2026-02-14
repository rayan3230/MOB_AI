from ai_service.engine.base import DepotB7Map, WarehouseCoordinate
from ai_service.core.picking_service import PickingOptimizationService

def test_operational_features():
    print("\n--- Testing Operational Route Optimization ---")
    
    # Setup Map
    rdc = DepotB7Map(width=50, height=30, floor_index=0)
    rdc._precompute_matrices()
    
    service = PickingOptimizationService({0: rdc})
    
    # 1. Multiple Chariots
    starts = [WarehouseCoordinate(5, 5), WarehouseCoordinate(40, 5)]
    picks = [
        WarehouseCoordinate(10, 10), 
        WarehouseCoordinate(15, 10),
        WarehouseCoordinate(35, 10),
        WarehouseCoordinate(45, 10)
    ]
    
    print(f"Testing Multiple Chariots (2 starts, 4 picks)...")
    routes = service.calculate_multi_chariot_routes(0, starts, picks)
    
    assert len(routes) == 2
    print(f"Chariot 1 assigned {len(routes[0]['route_sequence'])} picks.")
    print(f"Chariot 2 assigned {len(routes[1]['route_sequence'])} picks.")
    
    # 2. works for N items (e.g., 100 picks - simulated)
    large_picks = [WarehouseCoordinate(i % 50, (i // 50) + 10) for i in range(20)]
    print(f"Testing with {len(large_picks)} items...")
    route_large = service.calculate_picking_route(0, starts[0], large_picks)
    assert len(route_large['route_sequence']) == 20
    
    # 3. Caching
    print("Testing cache persistence...")
    # First call
    service._get_cached_path(0, WarehouseCoordinate(1,1), WarehouseCoordinate(2,2))
    cache_size_initial = len(service.global_path_cache)
    # Re-call with same (different order)
    service._get_cached_path(0, WarehouseCoordinate(2,2), WarehouseCoordinate(1,1))
    cache_size_after = len(service.global_path_cache)
    
    assert cache_size_initial == cache_size_after
    print(f"Cache verified: Key order normalized.")

    # 4. Re-routing
    print("Testing Re-routing...")
    current_pos = WarehouseCoordinate(12, 12)
    remaining = [WarehouseCoordinate(30, 30)]
    reroute = service.reroute_active_chariot(0, current_pos, remaining)
    assert reroute['route_sequence'][0] == WarehouseCoordinate(30, 30)

    print("\n[SUCCESS] Operational Requirements PASSED")

if __name__ == "__main__":
    test_operational_features()
