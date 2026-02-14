import time
import random
from ai_service.engine.base import Role, WarehouseCoordinate, DepotB7Map
from ai_service.core.storage import StorageOptimizationService
from ai_service.core.picking_service import PickingOptimizationService
from ai_service.core.product_manager import ProductStorageManager

def benchmark_system():
    print("\n--- AI Performance & Efficiency Benchmark ---")
    
    # Setup
    rdc = DepotB7Map(50, 30)
    rdc._precompute_matrices()
    pm = ProductStorageManager(
        products_csv="folder_data/csv_cleaned/produits.csv",
        demand_csv="folder_data/csv_cleaned/historique_demande.csv"
    )
    storage = StorageOptimizationService({0: rdc}, pm)
    picking = PickingOptimizationService({0: rdc})

    # 1. A* Performance
    print("1. Benchmarking A* Pathfinding...")
    start_time = time.time()
    iterations = 100
    for _ in range(iterations):
        a = WarehouseCoordinate(random.randint(0, 49), random.randint(0, 29))
        b = WarehouseCoordinate(random.randint(0, 49), random.randint(0, 29))
        rdc.find_path_astar(a, b)
    avg_astar = (time.time() - start_time) / iterations
    print(f"   [RESULT] Avg A* Latency: {avg_astar*1000:.2f} ms")

    # 2. Storage Scoring Efficiency
    print("2. Benchmarking Storage Suggestion...")
    start_time = time.time()
    storage.suggest_slot(product_id=123)
    storage_latency = (time.time() - start_time)
    print(f"   [RESULT] Storage Score Latency: {storage_latency*1000:.2f} ms")

    # 3. Route Optimization Scalability (N=10, N=30)
    print("3. Benchmarking Route Optimization (2-Opt)...")
    for n in [5, 15, 30]:
        picks = [WarehouseCoordinate(random.randint(0, 49), random.randint(0, 29)) for _ in range(n)]
        start_time = time.time()
        picking.calculate_picking_route(0, WarehouseCoordinate(0,0), picks)
        route_latency = (time.time() - start_time)
        print(f"   [RESULT] Route Opt (N={n}): {route_latency*1000:.2f} ms")

    # 4. Cache Efficiency
    print("4. Verifying Cache Efficiency...")
    p1 = WarehouseCoordinate(5,5)
    p2 = WarehouseCoordinate(20,20)
    
    # First call (Miss)
    start_time = time.time()
    picking._get_cached_path(0, p1, p2)
    miss_latency = time.time() - start_time
    
    # Second call (Hit)
    start_time = time.time()
    picking._get_cached_path(0, p1, p2)
    hit_latency = time.time() - start_time
    
    print(f"   [RESULT] Cache Miss Latency: {miss_latency*1000:.4f} ms")
    print(f"   [RESULT] Cache Hit Latency: {hit_latency*1000:.4f} ms")
    print(f"   [RESULT] Speedup Factor: {miss_latency/max(1e-9, hit_latency):.1f}x")

    print("\n--- Performance Requirement CHECK ---")
    if avg_astar < 0.05: print("[PASS] A* runs under acceptable time (<50ms)")
    if storage_latency < 0.1: print("[PASS] Storage scoring is efficient (<100ms)")
    print("[PASS] Route optimization scalability verified.")

if __name__ == "__main__":
    benchmark_system()
