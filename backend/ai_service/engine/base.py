import datetime
from typing import List, Tuple, Dict, Optional, Union
import enum
import matplotlib.pyplot as plt
import matplotlib.patches as patches

class Role(enum.Enum):
    ADMIN = "ADMIN"
    SUPERVISOR = "SUPERVISOR"
    EMPLOYEE = "EMPLOYEE"
    SYSTEM = "SYSTEM"

class ZoneType(enum.Enum):
    STORAGE = "STORAGE"
    OBSTACLE = "OBSTACLE"
    TRANSITION = "TRANSITION"
    WALKABLE = "WALKABLE"

class StorageClass(enum.Enum):
    FAST = "FAST-MOVING"    # Near expedition, ground level
    MEDIUM = "MEDIUM-MOVING" # Mid distance
    SLOW = "SLOW-MOVING"     # Far distance, upper floors

class WarehouseCoordinate:
    def __init__(self, x: float, y: float, z: float = 0):
        self.x = int(x)
        self.y = int(y)
        self.z = int(z)

    def __repr__(self):
        return f"({self.x}, {self.y}, {self.z})"

    def __hash__(self):
        return hash((self.x, self.y, self.z))

    def __eq__(self, other):
        if not isinstance(other, WarehouseCoordinate):
            return False
        return self.x == other.x and self.y == other.y and self.z == other.z

    def to_tuple(self) -> Tuple[int, int]:
        return (self.x, self.y)

    def to_3d_tuple(self) -> Tuple[int, int, int]:
        return (self.x, self.y, self.z)

class DepotB7Map:
    def __init__(self, width: int, height: int, floor_index: int = 0):
        self.floor_index = floor_index
        self.width = width
        self.height = height
        
        # To be populated by specific map definitions
        self.zones: Dict[str, Union[Tuple, List[Tuple]]] = {}
        self.zone_types: Dict[str, ZoneType] = {}
        self.landmarks: Dict[str, WarehouseCoordinate] = {}
        self.pillars: List[WarehouseCoordinate] = []
        self.special_walls: List[Tuple] = []
        self.occupied_slots: set[Tuple[int, int]] = set()

    def _precompute_matrices(self):
        """Precomputes boolean matrices and graph for O(1) lookups."""
        self.pillar_matrix = [[False for _ in range(self.height)] for _ in range(self.width)]
        for p in self.pillars:
            if 0 <= p.x < self.width and 0 <= p.y < self.height:
                self.pillar_matrix[int(p.x)][int(p.y)] = True

        self.storage_matrix = [[False for _ in range(self.height)] for _ in range(self.width)]
        for name, coords in self.zones.items():
            if self.zone_types.get(name) == ZoneType.STORAGE:
                if "Reserved" in name: continue 
                segments = coords if isinstance(coords, list) else [coords]
                for (x1, y1, x2, y2) in segments:
                    for x in range(int(x1), int(x2)):
                        for y in range(int(y1), int(y2)):
                            if 0 <= x < self.width and 0 <= y < self.height:
                                self.storage_matrix[x][y] = True

        self.walkable_matrix = [[False for _ in range(self.height)] for _ in range(self.width)]
        for x in range(self.width):
            for y in range(self.height):
                self.walkable_matrix[x][y] = self._calculate_walkable(WarehouseCoordinate(x, y))
        
        # Build graph for A*
        self.walkable_graph = self.build_walkable_graph()

    def is_slot_available(self, coord: WarehouseCoordinate) -> bool:
        """Requirement 8.2: Robust Slot Availability Check."""
        x, y = int(coord.x), int(coord.y)
        if not (0 <= x < self.width and 0 <= y < self.height):
            return False
        
        # 1. Rack-only storage respected
        if not self.storage_matrix[x][y]:
            return False
            
        # 2. Pillars & Walls excluded
        if self.pillar_matrix[x][y]:
            return False
            
        # 3. Availability checked (Occupancy)
        if (x, y) in self.occupied_slots:
            return False
            
        return True

    def _calculate_walkable(self, coord: WarehouseCoordinate) -> bool:
        if not (0 <= coord.x < self.width and 0 <= coord.y < self.height):
            return False
        if self.pillar_matrix[int(coord.x)][int(coord.y)]:
            return False
            
        # Use explicit zone types for walkability
        for name, coords in self.zones.items():
            z_type = self.zone_types.get(name, ZoneType.WALKABLE)
            if z_type in [ZoneType.STORAGE, ZoneType.OBSTACLE, ZoneType.TRANSITION]:
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

    def find_path_astar(self, start: WarehouseCoordinate, end: WarehouseCoordinate) -> Optional[List[Tuple[int, int]]]:
        """
        Requirement 8.3: A* Pathfinding Algorithm.
        Guarantees shortest path while respecting obstacles (Is_walkable).
        """
        import heapq

        def heuristic(a, b):
            return abs(a[0] - b[0]) + abs(a[1] - b[1])

        start_node = (int(start.x), int(start.y))
        end_node = (int(end.x), int(end.y))

        # Check if end is reachable (might be inside a rack)
        if not self.is_walkable(end):
            # Find nearest walkable neighbor to the rack (Search up to 5m)
            neighbors = []
            for radius in range(1, 6):
                for dx in range(-radius, radius + 1):
                    for dy in range(-radius, radius + 1):
                        if dx == 0 and dy == 0: continue
                        nx, ny = end_node[0] + dx, end_node[1] + dy
                        if self.is_walkable(WarehouseCoordinate(nx, ny)):
                            neighbors.append((nx, ny))
                if neighbors: break
            
            if not neighbors:
                return None # Truly blocked
            # Pick neighbor closest to start
            end_node = min(neighbors, key=lambda n: heuristic(n, start_node))

        open_set = []
        heapq.heappush(open_set, (0, start_node))
        came_from = {}
        g_score = {start_node: 0}
        f_score = {start_node: heuristic(start_node, end_node)}

        while open_set:
            current = heapq.heappop(open_set)[1]

            if current == end_node:
                path = []
                while current in came_from:
                    path.append(current)
                    current = came_from[current]
                path.append(start_node)
                return path[::-1]

            for neighbor in self.walkable_graph.get(current, []):
                tentative_g_score = g_score[current] + 1
                if tentative_g_score < g_score.get(neighbor, float('inf')):
                    came_from[neighbor] = current
                    g_score[neighbor] = tentative_g_score
                    f_score[neighbor] = tentative_g_score + heuristic(neighbor, end_node)
                    if neighbor not in [i[1] for i in open_set]:
                        heapq.heappush(open_set, (f_score[neighbor], neighbor))

        return None # No path found

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
