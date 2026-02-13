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
    def __init__(self, x: int, y: int, z: int = 0):
        self.x = x
        self.y = y
        self.z = z

    def __repr__(self):
        return f"({self.x}, {self.y}, {self.z})"

    def to_tuple(self) -> Tuple[int, int]:
        return (self.x, self.y)

    def to_3d_tuple(self) -> Tuple[int, int, int]:
        return (self.x, self.y, self.z)

class DepotB7Map:
    def __init__(self, width: int = 44, height: int = 29, floor_index: int = 0):
        self.floor_index = floor_index
        # Floor 0 is 42x27 (legacy/original)
        # Floors 1 and 2 are 44x29
        if floor_index == 0:
            self.width = 46
            self.height = 31
        else:
            self.width = 46
            self.height = 30
        
        # Rectangular Zones (e.g., Racks/Storage Blocks): (name, x_min, y_min, x_max, y_max)
        self.zones = {
           "Assenseur": (2, 21, 7.3, 23.5),
           "Montre de charge 1": (29.5, 20.8, 33, 25),
           "Montre de charge 2": (33, 20.8, 36.4, 25),
           "A1":(44,22.5,45.5,30),
           "A2":(40.8,22.5,43.3,30),
           "A3":[
               (38.7 , 22.5, 40, 30),
               (37.2 , 27.4 , 38.7, 30),
               (36 , 28 , 37.2, 30)
           ],
           "A4":(29.5 , 25 , 33.1 ,27.7),
           "A5":(25.2 , 28.3 , 33 , 30),
           "A6":(22.6 , 22.5 , 25.2 , 30),
           "B1":(18.2 , 22.5 , 21 , 30),
           "B2":(14.5 , 22.5 , 17.2 , 30),
           "B3":(11.1 , 22.5 , 13.8 , 30),
           "B5":(1.7 , 28.3 , 7.1 , 30),
           "B6":(0 , 22.5 , 1.7 , 30),

           "E1":(43 , 0 , 45.7 , 4.5),
           "E2":(40.5 , 0 , 43 , 4.5),
           "E3":(38 , 0 , 40.5 , 4.5),
           "E4":(35.1 , 0 , 38 , 4.5),
           "E5":(32.6 , 0 , 35.1 , 4.5),
           "E6":(30 , 0 , 32.6 , 4.5),
           "E7":(27.5 , 0 , 30 , 4.5),
           "E8":(25 , 0 , 27.5 , 4.5),
           "E9":(22.1 , 0 , 25 , 4.5),
           "E10":(19.7 , 0 , 22.1 , 4.5),
           "E11":(17 , 0 , 19.7 , 4.5),
           "E12":(14.5 , 0 , 17 , 4.5),
           "E13":(12 , 0 , 14.5 , 4.5),
           "E14":(9.2 , 0 , 12 , 4.5),
           "E15":(6.6 , 0 , 9.2 , 4.5),
           "E16":(4 , 0 , 6.6 , 4.5),
           "E17":(0 , 0 , 2.6 , 4.5),

           "C1":(44 , 13 , 45.5 , 18),
           "C7":(44 , 8.1 , 45.5 , 13),
           "C2":(40.7 , 13 , 43.2 , 18),
           "C8":(40.7 , 8.1 , 43.2 , 13),
           "C3":[
               (37.1 , 13 , 40 , 18),
               (36 , 11.5 , 37.1 , 18),
           ],
           "C9":(37.1,8.1 , 40 , 13),
           "C4":(31.9 , 13 , 34.5 , 18),
           "C10":(31.9 , 8.1 , 34.5 , 13),
           "C5":[
               (30 , 13 , 31.1 , 18),
               (28.5 , 11.5 ,30, 18),
               ],
           "C11":(30, 8.1 , 31.1 , 13),
           "C6":(25.1 , 13 , 28 , 18) ,
           "C12":[(25.1 , 8.1 , 26.5 , 13),(26.5 , 10.9 , 28 , 13 )],

            "D1":[(21 , 14.9 , 22.1 , 18), (19.5 , 13 , 21 , 18)],
            "D2":[(19.5 , 13 , 21 , 18), (21 , 8.1 , 21.1 , 11.1 )],
            # "D3":(44 , 4.5 , 45.5 , 7.1),
            # "D4":(44 , 4.5 , 45.5 , 7.1),
            # "D5":(44 , 4.5 , 45.5 , 7.1),
            # "D6":(44 , 4.5 , 45.5 , 7.1),
            # "D7":(44 , 4.5 , 45.5 , 7.1),
            # "D8":(44 , 4.5 , 45.5 , 7.1),
            # "D9":(44 , 4.5 , 45.5 , 7.1),
            # "D10":(44 , 4.5 , 45.5 , 7.1),
            # "D11":(44 , 4.5 , 45.5 , 7.1),
            # "D12":(40,22,30,30),



        }

        # Landmarks: (x, y)
        self.landmarks = {
        }

        # Pillars (Impassable obstacles)
        self.pillars: List[WarehouseCoordinate] = [
            #First row
            WarehouseCoordinate(2,8),
            WarehouseCoordinate(7.5,8),
            WarehouseCoordinate(14,8),
            WarehouseCoordinate(21,8),
            WarehouseCoordinate(23,8),
            WarehouseCoordinate(29,8),
            WarehouseCoordinate(36,8),
            WarehouseCoordinate(43,8),
            #second row
            WarehouseCoordinate(2,15),
            WarehouseCoordinate(7.5,15),
            WarehouseCoordinate(14,15),
            WarehouseCoordinate(21,15),
            WarehouseCoordinate(23,15),
            WarehouseCoordinate(29,15),
            WarehouseCoordinate(36,15),
            WarehouseCoordinate(43,15),
            #Third row
            WarehouseCoordinate(14,20.5),
            WarehouseCoordinate(21,20.5),
            WarehouseCoordinate(23,20.5),
            WarehouseCoordinate(43,20.5),
            #Fourth row
            WarehouseCoordinate(14,27),
            WarehouseCoordinate(36,27),
            WarehouseCoordinate(43,27),


        ]
        
        # Special thin walls: (x, y, width, height)
        self.special_walls = [
        ]
        # Block movement for special walls
        for (xw, yw, ww, hw) in self.special_walls:
            for y_step in range(int(yw), int(yw + hw)):
                self.pillars.append(WarehouseCoordinate(int(xw), y_step))
        
        # Track occupied slots (for items/stock)
        self.occupied_slots: set[Tuple[int, int]] = set()

        # STEP 10: Performance Optimization - Precompute Matrices
        self._precompute_matrices()
        
        # Step 8.3: Build Walkable Grid Graph G(V, E)
        self.walkable_graph = self.build_walkable_graph()

    def _precompute_matrices(self):
        """
        Step 10: Precomputes boolean matrices for O(1) lookups of 
        walls, pillars, and walkable zones.
        """
        self.pillar_matrix = [[False for _ in range(self.height)] for _ in range(self.width)]
        for p in self.pillars:
            if 0 <= p.x < self.width and 0 <= p.y < self.height:
                self.pillar_matrix[int(p.x)][int(p.y)] = True

        self.walkable_matrix = [[False for _ in range(self.height)] for _ in range(self.width)]
        for x in range(self.width):
            for y in range(self.height):
                self.walkable_matrix[x][y] = self._calculate_walkable(WarehouseCoordinate(x, y))

    def is_slot_available(self, coord: WarehouseCoordinate) -> bool:
        """Check if a coordinate is neither a pillar nor occupied by stock."""
        if not (0 <= coord.x < self.width and 0 <= coord.y < self.height):
            return False
            
        # 1. Check pillar matrix (O(1))
        if self.pillar_matrix[int(coord.x)][int(coord.y)]:
            return False
        # 2. Check if it's occupied by stock (O(1) in set)
        if coord.to_tuple() in self.occupied_slots:
            return False
        return True

    def _calculate_walkable(self, coord: WarehouseCoordinate) -> bool:
        """Original logic for is_walkable, used for precomputation."""
        if not (0 <= coord.x < self.width and 0 <= coord.y < self.height):
            return False
            
        if self.pillar_matrix[int(coord.x)][int(coord.y)]:
            return False
            
        blocked_keywords = ["Rack", "Bureau", "Black object", "Monte Charge", "Assenseur"]
        for name, coords in self.zones.items():
            is_blocked_zone = (len(name) == 1) or any(k in name for k in blocked_keywords)
            
            if is_blocked_zone:
                segments = coords if isinstance(coords, list) else [coords]
                for (x1, y1, x2, y2) in segments:
                    if x1 <= coord.x < x2 and y1 <= coord.y < y2:
                        return False
        return True

    def is_walkable(self, coord: WarehouseCoordinate) -> bool:
        """
        Step 10: Optimized O(1) check using precomputed matrix.
        """
        if not (0 <= coord.x < self.width and 0 <= coord.y < self.height):
            return False
        return self.walkable_matrix[coord.x][coord.y]

    def build_walkable_graph(self) -> Dict[Tuple[int, int], List[Tuple[int, int]]]:
        """
        Converts Floor to Walkable Grid Graph G(V, E) (Step 8.3).
        Edges = valid 4-direction moves between walkable nodes.
        """
        graph = {}
        for x in range(self.width):
            for y in range(self.height):
                if self.is_walkable(WarehouseCoordinate(x, y)):
                    node = (x, y)
                    graph[node] = []
                    # 4-direction moves (Up, Down, Left, Right)
                    for dx, dy in [(0, 1), (0, -1), (1, 0), (-1, 0)]:
                        nx, ny = x + dx, y + dy
                        if self.is_walkable(WarehouseCoordinate(nx, ny)):
                            graph[node].append((nx, ny))
        return graph

    def get_slot_name(self, coord: WarehouseCoordinate) -> str:
        return f"B7-L0-{coord.x:02d}-{coord.y:02d}"

    def calculate_distance(self, start: WarehouseCoordinate, end: WarehouseCoordinate) -> float:
        """
        Calculates Manhattan distance (Heuristic).
        For Step 8.3 Step 2, use AdvancedPickingService for True Shortest Path.
        """
        return float(abs(start.x - end.x) + abs(start.y - end.y))

    def get_path_cost(self, start: Tuple[int, int], end: Tuple[int, int]) -> float:
        """
        Uses BFS to find shortest path cost in a uniform grid as a fallback or 
        helper for A*.
        """
        if start == end: return 0.0
        queue = [(start, 0)]
        visited = {start}
        while queue:
            (curr_x, curr_y), dist = queue.pop(0)
            if (curr_x, curr_y) == end:
                return float(dist)
            for nx, ny in self.walkable_graph.get((curr_x, curr_y), []):
                if (nx, ny) not in visited:
                    visited.add((nx, ny))
                    queue.append(((nx, ny), dist + 1))
        return float('inf')

    def visualize(self):
        """
        Visualize the warehouse map using matplotlib.
        """
        fig, ax = plt.subplots(figsize=(12, 8))
        
        # Draw Warehouse boundary
        rect = patches.Rectangle((0, 0), self.width, self.height, linewidth=2, edgecolor='black', facecolor='none', label='Warehouse')
        ax.add_patch(rect)

        # Draw Pillars
        for p in self.pillars:
            pillar_patch = patches.Rectangle((p.x, p.y), 1, 1, color='salmon', alpha=0.9, label='Pillar' if p == self.pillars[0] else "")
            ax.add_patch(pillar_patch)

        # Draw Special Walls
        for xw, yw, ww, hw in self.special_walls:
            wall_patch = patches.Rectangle((xw, yw), ww, hw, color='black', alpha=1.0, label='Special Wall' if xw == self.special_walls[0][0] else "")
            ax.add_patch(wall_patch)

        # Draw Zones (Racks/Bureau/Expedition/Reserved/Monte Charge)
        for name, coords in self.zones.items():
            # Convert single tuple to list for uniform handling
            segments = coords if isinstance(coords, list) else [coords]
            
            for i, (x1, y1, x2, y2) in enumerate(segments):
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
                elif name == "Black object":
                    color, edge = 'black', 'black'
                elif "Monte Charge" in name:
                    color, edge = 'lightskyblue', 'deepskyblue'
                elif "Rack X" in name:
                    color, edge = 'plum', 'purple'
                else:
                    color, edge = 'tan', 'brown'
                    
                # Only add label to the first segment to avoid clutter
                label = f'Zone {name}' if i == 0 else ""
                zone_patch = patches.Rectangle((x1, y1), x2-x1, y2-y1, linewidth=1, edgecolor=edge, facecolor=color, alpha=0.5, label=label)
                ax.add_patch(zone_patch)
                
                # Only draw text for the first segment or if it's not Reserved
                if name != "Reserved" and i == 0:
                    ax.text((x1 + x2)/2, (y1 + y2)/2, name, color=edge, fontsize=10, fontweight='bold', ha='center', va='center')
            
        # Draw Landmarks
        landmark_colors = {
            "Assenseur": "blue",
            "Montre de charge 1": "cyan",
            "Montre de charge 2": "cyan",
            "Receipt Zone": "green",
            "Expedition Zone 1": "orange",
            "Expedition Zone 2": "orange",
            "Bureau": "purple",
            "Chariot Start 1": "red",
            "Chariot Start 2": "red"
        }
        
        for name, coord in self.landmarks.items():
            color = landmark_colors.get(name, "gray")
            ax.scatter(coord.x, coord.y, c=color, s=100, marker='s', label=name)
            ax.text(coord.x + 0.5, coord.y + 0.5, name, fontsize=8, fontweight='bold')

        ax.set_xlim(-2, self.width + 2)
        ax.set_ylim(-2, self.height + 2)
        ax.set_aspect('equal')
        floor_name = "RDC" if self.floor_index == 0 else f"Etage {self.floor_index}"
        ax.set_title(f"Depot B7 - Digital Twin Layout ({floor_name}) - {self.width}x{self.height}")
        ax.set_xlabel("X (meters)")
        ax.set_ylabel("Y (meters)")
        
        # Grid every 1 meter
        ax.set_xticks(range(0, self.width + 1))
        ax.set_yticks(range(0, self.height + 1))
        ax.tick_params(axis='both', which='major', labelsize=7)
        ax.grid(True, linestyle=':', alpha=0.4)
        
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

    def is_slot_available(self, coord: WarehouseCoordinate) -> bool:
        return self.warehouse_map.is_slot_available(coord)

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
                # Handle potential list of segments for expedition zones
                segments = coords if isinstance(coords, list) else [coords]
                for (x1, y1, x2, y2) in segments:
                    center = WarehouseCoordinate((x1 + x2) // 2, (y1 + y2) // 2)
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
                dist_to_exp = min(self.warehouse_map.calculate_distance(coord, ec) for ec in exp_centers) if exp_centers else 0.0
                
                # Heuristic score
                score = dist_to_exp
                
                if turnover_frequency == "HIGH":
                    score = dist_to_exp * 0.5 # Prioritize closeness for high turnover
                    
                if score < min_score:
                    min_score = score
                    best_coord = coord
        
        return best_coord

class PickingOptimizationService(OptimizationService):
    def optimize_picking_path(self, items_coords: List[WarehouseCoordinate], chariot_id: int = 1) -> List[WarehouseCoordinate]:
        """
        TSP-like optimization for picking path.
        """
        # Simple greedy approach starting from assigned chariot position
        start_key = f"Chariot Start {chariot_id}"
        current_pos = self.warehouse_map.landmarks.get(start_key, self.warehouse_map.landmarks.get("Bureau"))
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
            # Final safety check: ensuring the suggested slot is not a pillar
            if not self.map.is_slot_available(suggestion):
                print(f"ERROR: AI suggested a blocked slot {suggestion}. Blockage confirmed.")
                return None
            print(f"AI Suggestion: Place at {self.map.get_slot_name(suggestion)}")
        return suggestion

    def request_pick(self, coord: WarehouseCoordinate) -> bool:
        """
        Validate if an item can be picked from a location.
        Forbidden if the location is blocked by a pillar.
        """
        if not self.storage_service.is_slot_available(coord):
            print(f"ACCESS DENIED: Slot {self.map.get_slot_name(coord)} is blocked by a pillar.")
            return False
        print(f"Pick initialized for {self.map.get_slot_name(coord)}.")
        return True

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
