import os
import sys

# Add current path for module resolution
sys.path.append(os.getcwd())

from ai_service.maps import GroundFloorMap
from ai_service.core.product_manager import ProductStorageManager
from ai_service.engine.manager import WMSOperationManager
from ai_service.engine.base import WarehouseCoordinate, Role

def test_override_handling():
    print("=== STEP 8.4: OVERRIDE HANDLING TEST ===\n")
    
    # 1. Setup
    base_path = "folder_data/csv_export"
    prod_csv = os.path.join(base_path, "produits.csv")
    dem_csv = os.path.join(base_path, "historique_demande.csv")
    
    pm = ProductStorageManager(prod_csv, dem_csv)
    rdc = GroundFloorMap()
    manager = WMSOperationManager({0: rdc}, pm)

    pid = 31336
    
    # 2. Process SKU (AI Suggestion)
    print(f"1. AI Suggesting placement for SKU {pid}...")
    task_id = manager.process_incoming_sku(pid)
    print(f"   Task Created: {task_id}")
    print(f"   Current Status: {manager.tasks[task_id]['status']}")

    # 3. Employee attempts to execute BEFORE validation
    print(f"\n2. Employee trying to execute unvalidated task...")
    try:
        success = manager.execute_task(task_id, Role.EMPLOYEE)
        if not success:
            print("   ✅ Success: Employee blocked from executing unvalidated task.")
    except Exception as e:
        print(f"   ❌ Unexpected Error: {e}")

    # 4. Supervisor Overrides with Justification
    print(f"\n3. Supervisor Overriding AI decision...")
    new_coord = WarehouseCoordinate(10, 10) # Manual choice
    justification = "Manual override: This aisle is currently reserved for a large incoming shipment."
    
    manager.override_task(task_id, Role.SUPERVISOR, 0, new_coord, justification)
    print(f"   Task Status after Override: {manager.tasks[task_id]['status']}")
    print(f"   Is Overridden: {manager.tasks[task_id]['overridden']}")
    print(f"   Justification Logged: {manager.tasks[task_id]['justification']}")

    # 5. Employee executes VALIDATED/OVERRIDDEN task
    print(f"\n4. Employee executing validated task...")
    final_success = manager.execute_task(task_id, Role.EMPLOYEE)
    if final_success:
        print("   ✅ Success: Employee executed validated task.")
        print(f"   Task Status: {manager.tasks[task_id]['status']}")

if __name__ == "__main__":
    test_override_handling()
