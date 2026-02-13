import datetime
from typing import List, Tuple, Dict, Optional, Union
import enum
import matplotlib.pyplot as plt
import matplotlib.patches as patches

class Role(enum.Enum):
    ADMIN = "ADMIN"
    SUPERVISOR = "SUPERVISOR"
    EMPLOYEE = "EMPLOYEE"

class StorageClass(enum.Enum):
    FAST = "FAST-MOVING"    # Near expedition, ground level
    MEDIUM = "MEDIUM-MOVING" # Mid distance
    SLOW = "SLOW-MOVING"     # Far distance, upper floors

class WarehouseCoordinate:
    def __init__(self, x: float, y: float, z: float = 0):
        self.x = x
        self.y = y
        self.z = z

    def __repr__(self):
        return f"({self.x}, {self.y}, {self.z})"

    def to_tuple(self) -> Tuple[float, float]:
        return (self.x, self.y)

    def to_3d_tuple(self) -> Tuple[float, float, float]:
        return (self.x, self.y, self.z)

class DepotB7Map:
    def __init__(self, width: int, height: int, floor_index: int = 0):
        self.floor_index = floor_index
        self.width = width
        self.height = height
        
        # To be populated by specific map definitions
        self.zones: Dict[str, Union[Tuple, List[Tuple]]] = {}
        self.landmarks: Dict[str, WarehouseCoordinate] = {}
        self.pillars: List[WarehouseCoordinate] = []
        self.special_walls: List[Tuple] = []
        self.occupied_slots: set[Tuple[int, int]] = set()

    def _precompute_matrices(self):
        """Precomputes boolean matrices for O(1) lookups."""
        self.pillar_matrix = [[False for _ in range(self.height)] for _ in range(self.width)]
        for p in self.pillars:
            if 0 <= p.x < self.width and 0 <= p.y < self.height:
                self.pillar_matrix[int(p.x)][int(p.y)] = True

        self.walkable_matrix = [[False for _ in range(self.height)] for _ in range(self.width)]
        for x in range(self.width):
            for y in range(self.height):
                self.walkable_matrix[x][y] = self._calculate_walkable(WarehouseCoordinate(x, y))

    def is_slot_available(self, coord: WarehouseCoordinate) -> bool:
        if not (0 <= coord.x < self.width and 0 <= coord.y < self.height):
            return False
        if self.pillar_matrix[int(coord.x)][int(coord.y)]:
            return False
        if (int(coord.x), int(coord.y)) in self.occupied_slots:
            return False
        return True

    def _calculate_walkable(self, coord: WarehouseCoordinate) -> bool:
        if not (0 <= coord.x < self.width and 0 <= coord.y < self.height):
            return False
        if self.pillar_matrix[int(coord.x)][int(coord.y)]:
            return False
        blocked_keywords = ["Rack", "Bureau", "Black object", "Monte Charge", "Assenseur"]
        for name, coords in self.zones.items():
            is_blocked_zone = (len(name) <= 2) or any(k in name for k in blocked_keywords) # Updated to include short names like 'A1'
            if is_blocked_zone:
                segments = coords if isinstance(coords, list) else [coords]
                for (x1, y1, x2, y2) in segments:
                    if x1 <= coord.x < x2 and y1 <= coord.y < y2:
                        return False
        return True

    def is_walkable(self, coord: WarehouseCoordinate) -> bool:
        if not (0 <= coord.x < self.width and 0 <= coord.y < self.height):
            return False
        return self.walkable_matrix[int(coord.x)][int(coord.y)]

    def build_walkable_graph(self) -> Dict[Tuple[int, int], List[Tuple[int, int]]]:
        graph = {}
        for x in range(self.width):
            for y in range(self.height):
                coord = WarehouseCoordinate(x, y)
                if self.is_walkable(coord):
                    node = (x, y)
                    graph[node] = []
                    for dx, dy in [(0, 1), (0, -1), (1, 0), (-1, 0)]:
                        nx, ny = x + dx, y + dy
                        if self.is_walkable(WarehouseCoordinate(nx, ny)):
                            graph[node].append((nx, ny))
        return graph

    def get_slot_name(self, coord: WarehouseCoordinate) -> str:
        return f"B7-L{self.floor_index}-{int(coord.x):02d}-{int(coord.y):02d}"

    def calculate_distance(self, start: WarehouseCoordinate, end: WarehouseCoordinate) -> float:
        return float(abs(start.x - end.x) + abs(start.y - end.y))

    def get_path_distance_map(self, target_points: List[WarehouseCoordinate]) -> Dict[Tuple[int, int], float]:
        """
        Calculates the shortest walking distance from all points to the nearest target point.
        Uses BFS for uniform cost grid travel.
        """
        import collections
        
        dist_map = {}
        queue = collections.deque()
        
        # Initialize queue with target points
        for tp in target_points:
            target_node = (int(tp.x), int(tp.y))
            if target_node in self.walkable_graph or self.is_walkable(tp):
                dist_map[target_node] = 0.0
                queue.append(target_node)
        
        # Breadth-First Search
        while queue:
            current_node = queue.popleft()
            current_dist = dist_map[current_node]
            
            # Use neighbors from precomputed walkable graph
            neighbors = self.walkable_graph.get(current_node, [])
            for neighbor in neighbors:
                if neighbor not in dist_map:
                    dist_map[neighbor] = current_dist + 1.0 # 1m per relative cell
                    queue.append(neighbor)
        
        return dist_map

    def visualize(self):
        fig, ax = plt.subplots(figsize=(12, 8))
        rect = patches.Rectangle((0, 0), self.width, self.height, linewidth=2, edgecolor='black', facecolor='none', label='Warehouse')
        ax.add_patch(rect)
        for p in self.pillars:
            ax.add_patch(patches.Rectangle((p.x, p.y), 1, 1, color='salmon', alpha=0.9))
        for xw, yw, ww, hw in self.special_walls:
            ax.add_patch(patches.Rectangle((xw, yw), ww, hw, color='black', alpha=1.0))
        for name, coords in self.zones.items():
            segments = coords if isinstance(coords, list) else [coords]
            for i, (x1, y1, x2, y2) in enumerate(segments):
                color, edge = 'tan', 'brown'
                if name == "Bureau": color, edge = 'lavender', 'purple'
                elif "Expédition" in name: color, edge = 'orange', 'darkorange'
                elif name == "Reserved": color, edge = 'lightgray', 'gray'
                elif name == "Assenseur": color, edge = 'lightsteelblue', 'blue'
                elif "Monte Charge" in name: color, edge = 'lightskyblue', 'deepskyblue'
                elif "Rack" in name or len(name) <= 3: color, edge = 'plum', 'purple'
                
                ax.add_patch(patches.Rectangle((x1, y1), x2-x1, y2-y1, linewidth=1, edgecolor=edge, facecolor=color, alpha=0.5))
                if i == 0 and name != "Reserved":
                    ax.text((x1 + x2)/2, (y1 + y2)/2, name, color=edge, fontsize=8, ha='center', va='center')
        
        ax.set_xlim(-2, self.width + 2)
        ax.set_ylim(-2, self.height + 2)
        ax.set_aspect('equal')
        ax.set_title(f"Depot B7 - Floor {self.floor_index} Layout")
        plt.grid(True, linestyle=':', alpha=0.4)
        plt.show()

class AuditTrail:
    @staticmethod
    def log(user_role: Role, action: str, justification: Optional[str] = None):
        print(f"AUDIT LOG: [{datetime.datetime.now().isoformat()}] Role: {user_role.value} | Action: {action}" + (f" | Justification: {justification}" if justification else ""))
