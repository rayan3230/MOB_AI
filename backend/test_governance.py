from ai_service.engine.base import Role, WarehouseCoordinate, DepotB7Map
from ai_service.core.storage import StorageOptimizationService
from ai_service.core.picking_service import PickingOptimizationService
from ai_service.core.product_manager import ProductStorageManager
import pytest

def test_governance_and_control():
    print("\n--- Testing AI Governance & Control ---")
    
    # Setup
    rdc = DepotB7Map(50, 30)
    rdc._precompute_matrices()
    pm = ProductStorageManager(
        products_csv="folder_data/csv_cleaned/produits.csv",
        demand_csv="folder_data/csv_cleaned/historique_demande.csv"
    )
    storage = StorageOptimizationService({0: rdc}, pm)
    picking = PickingOptimizationService({0: rdc})
    
    target_coord = WarehouseCoordinate(10, 10)
    product_id = 999
    
    # 1. Permission Enforcement (Manual Override)
    print("Testing Role Enforcement...")
    try:
        storage.manual_override_placement(product_id, 0, target_coord, Role.EMPLOYEE, "I want this slot.")
        print("[FAIL] Employee was allowed to override!")
    except PermissionError:
        print("[PASS] Employee correctly blocked from manual override.")

    # 2. Justification Enforcement
    print("Testing Justification Requirement...")
    try:
        storage.manual_override_placement(product_id, 0, target_coord, Role.SUPERVISOR, "Short.")
        print("[FAIL] Supervisor allowed short justification!")
    except ValueError:
        print("[PASS] Short justification correctly rejected.")

    # 3. Successful Override & Audit
    print("Testing Successful Override & Audit Logging...")
    success = storage.manual_override_placement(product_id, 0, target_coord, Role.SUPERVISOR, "Emergency overflow from Zone A.")
    assert success is True
    assert target_coord.to_tuple() in rdc.occupied_slots
    print("[PASS] Manual override successful and logged.")

    # 4. No Silent Failures (Picking)
    print("Testing No Silent Failures (Invalid Floor)...")
    result = picking.calculate_picking_route(99, WarehouseCoordinate(0,0), [WarehouseCoordinate(1,1)])
    assert "error" in result
    print("[PASS] System explicitly returned error for invalid floor.")

    # 5. Route Validation
    print("Testing Route Validation...")
    route_mock = {"total_distance": 100.5}
    try:
        picking.validate_and_approve_route(route_mock, Role.EMPLOYEE, "Checked.")
        assert False, "Employee should not validate."
    except PermissionError:
         print("[PASS] Employee blocked from route validation.")
    
    picking.validate_and_approve_route(route_mock, Role.SUPERVISOR, "Route verified for safety.")
    print("[PASS] Supervisor successfully validated route.")

    print("\n[SUCCESS] AI Governance & Control PASSED")

if __name__ == "__main__":
    test_governance_and_control()
