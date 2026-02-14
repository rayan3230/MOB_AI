import datetime
import pandas as pd
from .base import Role, DepotB7Map, WarehouseCoordinate, AuditTrail
from ..core.storage import StorageOptimizationService
from ..core.product_manager import ProductStorageManager
from ..core.picking import PickingOptimizationService
from typing import Optional, Dict, List

class WMSOperationManager:
    def __init__(self, floors: Dict[int, DepotB7Map], product_manager: ProductStorageManager, emplacements_df: Optional[pd.DataFrame] = None):
        """
        Final Architecture: WMS Manager
        Orchestrates storage placement, forecasting, picking routes, and OVERRIDES.
        """
        self.floors = floors
        self.product_manager = product_manager
        self.storage_service = StorageOptimizationService(floors, product_manager)
        self.picking_service = PickingOptimizationService(floors)
        
        # Sync physical state if provided
        if emplacements_df is not None:
            self.storage_service.sync_physical_state(emplacements_df)
        
        # --- REQ 8.4: Task Management ---
        # Task mapping: task_id -> {product_id, suggested_coord, status, user_override, justification}
        self.tasks: Dict[str, Dict] = {}

    def process_incoming_sku(self, product_id: int) -> str:
        """
        AI-First Suggestion Phase. 
        Creates a task that requires validation.
        """
        suggestion = self.storage_service.suggest_slot(product_id)
        
        task_id = f"TASK-{product_id}-{int(datetime.datetime.now().timestamp())}"
        
        if suggestion:
            self.tasks[task_id] = {
                "task_id": task_id,
                "type": "PLACEMENT",
                "product_id": product_id,
                "suggested_floor": suggestion['floor_idx'],
                "suggested_coord": suggestion['coord'],
                "suggested_slot_name": suggestion['slot_name'],
                "status": "PENDING_VALIDATION",
                "overridden": False,
                "justification": None,
                "assigned_to": None
            }
            AuditTrail.log(Role.ADMIN, f"Created AI placement task {task_id} for slot {suggestion['slot_name']}")
            return task_id
        return None

    def override_task(self, task_id: str, supervisor_role: Role, new_floor: int, new_coord: WarehouseCoordinate, justification: str):
        """
        REQ 8.4: Supervisor/Admin override logic.
        """
        if supervisor_role not in [Role.SUPERVISOR, Role.ADMIN]:
            raise PermissionError("Only Supervisors and Admins can override AI decisions.")
        
        if not justification or len(justification) < 5:
            raise ValueError("Justification is mandatory for overrides.")

        if task_id in self.tasks:
            task = self.tasks[task_id]
            task["suggested_floor"] = new_floor
            task["suggested_coord"] = new_coord
            task["overridden"] = True
            task["justification"] = justification
            task["status"] = "VALIDATED" # Overriding automatically validates
            
            AuditTrail.log(supervisor_role, f"OVERRIDE task {task_id}", justification)
            return True
        return False

    def validate_task(self, task_id: str, supervisor_role: Role):
        """Validates an AI suggestion without changing it."""
        if supervisor_role not in [Role.SUPERVISOR, Role.ADMIN]:
            raise PermissionError("Validation requires Supervisor role.")
            
        if task_id in self.tasks:
            self.tasks[task_id]["status"] = "VALIDATED"
            AuditTrail.log(supervisor_role, f"Validated task {task_id}")
            return True
        return False

    def execute_task(self, task_id: str, employee_role: Role):
        """
        REQ 8.4: Employees execute VALIDATED decisions only.
        """
        if task_id not in self.tasks:
            return False
            
        task = self.tasks[task_id]
        
        if task["status"] != "VALIDATED" and employee_role == Role.EMPLOYEE:
            print(f"[ERROR] Employee cannot execute unvalidated task {task_id}")
            return False

        # Finalize assignment in storage engine (Step 7 logic)
        success = self.storage_service.assign_slot(
            task["product_id"], 
            task["suggested_floor"], 
            task["suggested_coord"]
        )
        
        if success:
            task["status"] = "COMPLETED"
            task["assigned_to"] = employee_role.value
            AuditTrail.log(employee_role, f"COMPLETED task {task_id}")
            return True
        return False

    def generate_picking_order(self, product_ids: List[int]) -> Dict:
        """
        REQ 8.3: Generates optimized Picking Orders.
        1. Find product locations (Digital Twin)
        2. Compute shortest route
        3. Minimize travel time
        """
        # Step 1: Find locations of these products
        items_to_pick = []
        for pid in product_ids:
            # Find in slot_to_product mapping (Step 7 logic)
            found = False
            for (f_idx, x, y), stored_pid in self.storage_service.slot_to_product.items():
                if stored_pid == pid:
                    items_to_pick.append({
                        "product_id": pid,
                        "floor_idx": f_idx,
                        "coord": (x, y)
                    })
                    found = True
                    break
            if not found:
                 print(f"[WARN] SKU {pid} not found in storage state.")

        # Step 2: Optimize route
        if not items_to_pick:
            return {"error": "No items found in stock"}

        route_data = self.picking_service.optimize_picking_route(items_to_pick)
        return route_data

    def generate_batched_picking_orders(self, product_ids: List[int], max_per_picker: int = 5) -> List[Dict]:
        """
        Creates multiple optimized picking routes for a large order.
        """
        batches = self.picking_service.generate_batch_picking(product_ids, max_per_picker)
        
        final_orders = []
        for b in batches:
            route = self.generate_picking_order(b['product_ids'])
            final_orders.append({
                "batch_id": b['batch_id'],
                "route_details": route
            })
        return final_orders
