import datetime
from typing import List, Tuple, Dict, Optional, Union
import enum
import matplotlib.pyplot as plt
import matplotlib.patches as patches

class Role(enum.Enum):
    ADMIN = "ADMIN"
    SUPERVISOR = "SUPERVISOR"
    EMPLOYEE = "EMPLOYEE"

class WarehouseCoordinate:
    def __init__(self, x: int, y: int):
        self.x = x
        self.y = y

    def __repr__(self):
        return f"({self.x}, {self.y})"

    def to_tuple(self) -> Tuple[int, int]:
        return (self.x, self.y)

class DepotB7Map:
    def __init__(self, width: int = 42, height: int = 27):
        self.width = width
        self.height = height
        
        # Rectangular Zones (e.g., Racks/Storage Blocks): (name, x_min, y_min, x_max, y_max)
        self.zones = {
            "V,S": (4, 1, 7, 12),  # Specified: Left-Down (4,1), High-Right (7,12)
            "Bureau": (29, 0, 42, 7),
            "Expédition 1": (35, 7, 42, 13),
            "Expédition 2": (35, 13, 42, 20),
            "Reserved": (28, 20, 42, 27),
            "Monte Charge 1": (31, 20, 34, 24),
            "Monte Charge 2": (28, 20, 31, 24),
            "Rack B": (25, 1, 26, 11),
            "Rack FD": (20, 1, 22, 11),
            "Rack QN": (15, 1, 17, 11),
            "Rack W": (1, 2, 2, 20),
            "Assenseur": (0, 20, 5, 22),
            "Zone Spec": (0, 20, 9, 27)
        }

        # Landmarks: (x, y)
        self.landmarks = {}

    def get_slot_name(self, coord: WarehouseCoordinate) -> str:
        return f"B7-L0-{coord.x:02d}-{coord.y:02d}"

    def calculate_distance(self, start: WarehouseCoordinate, end: WarehouseCoordinate) -> float:
        """
        Calculate shortest distance using Manhattan distance for 2D floor-level travel.
        """
        return abs(start.x - end.x) + abs(start.y - end.y)

    def visualize(self):
        """
        Visualize the warehouse map using matplotlib.
        """
        fig, ax = plt.subplots(figsize=(12, 8))
        
        # Draw Warehouse boundary
        rect = patches.Rectangle((0, 0), self.width, self.height, linewidth=2, edgecolor='black', facecolor='none', label='Warehouse')
        ax.add_patch(rect)

        # Draw Zones (Racks/Bureau/Expedition/Reserved/Monte Charge)
        for name, (x1, y1, x2, y2) in self.zones.items():
            if name == "Bureau":
                color, edge = 'lavender', 'purple'
            elif "Expédition" in name:
                color, edge = 'orange', 'darkorange'
            elif name == "Reserved":
                color, edge = 'lightgray', 'gray'
            elif name == "Assenseur":
                color, edge = 'lightsteelblue', 'blue'
            elif name == "Zone Spec":
                color, edge = 'none', 'black'
            elif "Monte Charge" in name:
                color, edge = 'lightskyblue', 'deepskyblue'
            else:
                color, edge = 'tan', 'brown'
                
            zone_patch = patches.Rectangle((x1, y1), x2-x1, y2-y1, linewidth=1, edgecolor=edge, facecolor=color, alpha=0.5, label=f'Zone {name}')
            ax.add_patch(zone_patch)
            ax.text((x1 + x2)/2, (y1 + y2)/2, name, color=edge, fontsize=10, fontweight='bold', ha='center', va='center')
            
        # Draw Landmarks
        landmark_colors = {
            "Assenseur": "blue",
            "Montre de charge 1": "cyan",
            "Montre de charge 2": "cyan",
            "Receipt Zone": "green",
            "Expedition Zone 1": "orange",
            "Expedition Zone 2": "orange",
            "Bureau": "purple"
        }
        
        for name, coord in self.landmarks.items():
            color = landmark_colors.get(name, "gray")
            ax.scatter(coord.x, coord.y, c=color, s=100, marker='s', label=name)
            ax.text(coord.x + 0.5, coord.y + 0.5, name, fontsize=8, fontweight='bold')

        ax.set_xlim(-2, self.width + 5)
        ax.set_ylim(-2, self.height + 5)
        ax.set_aspect('equal')
        ax.set_title("Depot B7 - Digital Twin Layout (2D)")
        ax.set_xlabel("X (meters)")
        ax.set_ylabel("Y (meters)")
        ax.grid(True, linestyle=':', alpha=0.6)
        
        # Clean up legend (remove duplicates)
        handles, labels = ax.get_legend_handles_labels()
        by_label = dict(zip(labels, handles))
        ax.legend(by_label.values(), by_label.keys(), loc='upper left', bbox_to_anchor=(1, 1))
        
        plt.tight_layout()
        plt.show()

class AuditTrail:
    @staticmethod
    def log(user_role: Role, action: str, justification: Optional[str] = None):
        timestamp = datetime.datetime.now().isoformat()
        log_entry = f"[{timestamp}] Role: {user_role.value} | Action: {action}"
        if justification:
            log_entry += f" | Justification: {justification}"
        print(f"AUDIT LOG: {log_entry}")
        # In a real app, this would write to a database table

class OptimizationService:
    def __init__(self, warehouse_map: DepotB7Map):
        self.warehouse_map = warehouse_map
        # Slot availability map: (x, y) -> bool (True if free)
        self.slots_availability: Dict[Tuple[int, int], bool] = {}

    def is_slot_available(self, coord: WarehouseCoordinate) -> bool:
        return self.slots_availability.get(coord.to_tuple(), True)

class StorageOptimizationService(OptimizationService):
    def suggest_placement(self, weight_kg: float, turnover_frequency: str) -> WarehouseCoordinate:
        """
        Logic: 
        - High-turnover closer to expedition zones.
        """
        # Suggest relative to the center of the nearest Expedition Zone
        exp_centers = []
        for name, coords in self.warehouse_map.zones.items():
            if "Expédition" in name:
                center = WarehouseCoordinate((coords[0] + coords[2]) // 2, (coords[1] + coords[3]) // 2)
                exp_centers.append(center)
        
        best_coord = None
        min_score = float('inf')

        # Iterate through sample slots (in a real scenario, this would be more optimized)
        for x in range(0, self.warehouse_map.width):
            for y in range(0, self.warehouse_map.height):
                coord = WarehouseCoordinate(x, y)
                if not self.is_slot_available(coord):
                    continue
                    
                # Distance to nearest expedition zone center
                dist_to_exp = min(self.warehouse_map.calculate_distance(coord, ec) for ec in exp_centers)
                
                # Heuristic score
                score = dist_to_exp
                
                if turnover_frequency == "HIGH":
                    score = dist_to_exp * 0.5 # Prioritize closeness for high turnover
                    
                if score < min_score:
                    min_score = score
                    best_coord = coord
        
        return best_coord

class PickingOptimizationService(OptimizationService):
    def optimize_picking_path(self, items_coords: List[WarehouseCoordinate]) -> List[WarehouseCoordinate]:
        """
        TSP-like optimization for picking path.
        """
        # Simple greedy approach for demonstration
        current_pos = self.warehouse_map.landmarks["Bureau"]
        path = []
        remaining = list(items_coords)
        
        while remaining:
            next_item = min(remaining, key=lambda c: self.warehouse_map.calculate_distance(current_pos, c))
            path.append(next_item)
            remaining.remove(next_item)
            current_pos = next_item
            
        return path

class WMSOperationManager:
    def __init__(self, role: Role):
        self.user_role = role
        self.map = DepotB7Map()
        self.storage_service = StorageOptimizationService(self.map)
        self.picking_service = PickingOptimizationService(self.map)

    def request_placement(self, weight: float, frequency: str) -> Optional[WarehouseCoordinate]:
        suggestion = self.storage_service.suggest_placement(weight, frequency)
        if suggestion:
            print(f"AI Suggestion: Place at {self.map.get_slot_name(suggestion)}")
        return suggestion

    def validate_order(self, supervisor_role: Role, order_id: str):
        if supervisor_role != Role.SUPERVISOR and supervisor_role != Role.ADMIN:
            raise PermissionError("Only SUPERVISORS can validate orders.")
        
        AuditTrail.log(supervisor_role, f"Validated Order {order_id}")
        return True

    def manual_override(self, justification: str, action: str):
        if not justification:
            raise ValueError("Justification is mandatory for manual overrides.")
        AuditTrail.log(self.user_role, f"OVERRIDE: {action}", justification)

# Sample Initialization and Usage
if __name__ == "__main__":
    print("--- Initializing Depot B7 Digital Twin (2D) ---")
    wms = WMSOperationManager(Role.ADMIN)
    
    # 1. Coordinate Grid & Landmarks
    print(f"Warehouse Dimensions: {wms.map.width}m x {wms.map.height}m")
    
    # 2. AI Optimization Check
    print("\n--- AI Suggestion Test ---")
    item_slot = wms.request_placement(weight=500, frequency="HIGH")
    
    # 3. Operational Requirements Test
    print("\n--- Validation Flow Test ---")
    wms.validate_order(Role.SUPERVISOR, "ORD-123")
    
    # 4. Audit Trail Test
    print("\n--- Audit Trail Test ---")
    wms.manual_override("Urgent restocking requirement", "Moved SKU-88 to Zone B7-L0-10-10")

    # 5. Visualization
    print("\n--- Generating Map Visualization ---")
    wms.map.visualize()
