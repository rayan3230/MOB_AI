import sys
import os
import random

# Ensure imports work from backend root
sys.path.append(os.getcwd())

from ai_service.engine.base import WarehouseCoordinate, AuditTrail, Role
from ai_service.core.picking_service import PickingOptimizationService
from ai_service.maps import GroundFloorMap

def run_bench():
    rdc = GroundFloorMap()
    rdc._precompute_matrices()
    service = PickingOptimizationService({0: rdc})
    
    start = WarehouseCoordinate(35, 10)
    # Generate 15 random pick nodes in storage zones
    storage_nodes = []
    # Force some spread to see optimization effects
    for _ in range(15):
        found = False
        while not found:
            x, y = random.randint(0, 41), random.randint(0, 26)
            if rdc.storage_matrix[x][y]:
                storage_nodes.append(WarehouseCoordinate(x, y))
                found = True
            
    # 1. Optimized Route (The real one)
    opt_route = service.calculate_picking_route(0, start, storage_nodes)
    opt_dist = opt_route['total_distance']
    
    # 2. Naive Route (FIFO / Random Order)
    naive_dist = 0
    curr = start
    for p in storage_nodes:
        dist, _ = service._get_cached_path(0, curr, p)
        naive_dist += dist
        curr = p
        
    improvement = ((naive_dist - opt_dist) / naive_dist) * 100
    print(f"--- ROUTE OPTIMIZATION BENCHMARK ---")
    print(f"Nodes Picked: {len(storage_nodes)}")
    print(f"Naive Distance: {naive_dist:.2f}m")
    print(f"Optimized (2-Opt) Distance: {opt_dist:.2f}m")
    print(f"Measured Improvement: {improvement:.2f}%")

if __name__ == "__main__":
    run_bench()
