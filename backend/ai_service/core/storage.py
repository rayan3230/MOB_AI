from typing import List, Dict, Tuple, Optional
import enum
import random
from ..engine.base import DepotB7Map, WarehouseCoordinate, StorageClass
from .product_manager import ProductStorageManager

class StorageOptimizationService:
    def __init__(self, floors: Dict[int, DepotB7Map], product_manager: ProductStorageManager):
        """
        :param floors: Dictionary mapping floor_index to DepotB7Map instance
        :param product_manager: Instance of ProductStorageManager for product scoring
        """
        self.floors = floors
        self.product_manager = product_manager
        self.storage_zoning: Dict[int, Dict[Tuple[int, int], StorageClass]] = {}
        self.slot_distance_scores: Dict[int, Dict[Tuple[int, int], float]] = {}
        
        # --- STEP 8: Dynamic Heatmap Tracker ---
        # Maps (floor, x, y) to a traffic counter
        self.traffic_heatmap: Dict[int, Dict[Tuple[int, int], int]] = {}
        
        # --- STEP 8.1: Predictive Forecasting Integration ---
        self.predictive_high_demand_skus = set()

        # --- REBALANCING: Mapping of occupied slots to products ---
        self.slot_to_product: Dict[Tuple[int, int, int], int] = {} # (floor, x, y) -> product_id
        
        # --- STEP 3: Weights for Multi-Factor Scoring ---
        self.weights = {
            "distance": 1.0,
            "weight": 2.5,     # High penalty for heavy items far away
            "frequency": 1.0,  # Multiplier applied directly to distance
            "congestion": 5.0, # Significant penalty to avoid bottleneck
            "traffic": 0.2     # Adjustment for zone heat
        }
        
        self._classify_all_floors()

    def apply_forecast_data(self, high_demand_skus: List[int]):
        """
        Integrates forecasting data (Step 8.1).
        SKUs with high predicted demand will be prioritized for slots closer to expedition.
        """
        self.predictive_high_demand_skus = set(high_demand_skus)

    def calculate_slot_score(self, floor_idx: int, coord: WarehouseCoordinate, product_id: int) -> float:
        """
        Multi-factor scoring: α*Dist + β*WeightPen + γ*FreqPri + δ*CongPen
        Returns lower score for better candidates.
        """
        dist_score = self.slot_distance_scores.get(floor_idx, {}).get((int(coord.x), int(coord.y)), 100.0)
        p_class = self.product_manager.get_product_class(product_id)
        p_details = self.product_manager.get_product_details(product_id)
        weight = p_details.get('poidsu', 0.0)
        
        # 1. Frequency Priority (Multiplier)
        freq_multiplier = 1.0
        if p_class == StorageClass.FAST: freq_multiplier = 0.5
        elif p_class == StorageClass.SLOW: freq_multiplier = 1.2

        # --- STEP 8.1: Predictive Boost ---
        if product_id in self.predictive_high_demand_skus:
            # Upgrade even if it's currently SLOW, give it a "Super-Fast" boost (0.3)
            # This forces it towards the expedition areas
            freq_multiplier = 0.3 
        
        # --- STEP 8: Dynamic Alpha Adjustment (Heatmap) ---
        # Get traffic load for the specific zone (x,y)
        traffic_load = self.traffic_heatmap.get(floor_idx, {}).get((int(coord.x), int(coord.y)), 0)
        # If a zone is 'Hot' (high traffic), alpha increases to discourage more placement there
        # alpha = baseline + (traffic * factor)
        dynamic_alpha = self.weights["distance"] + (traffic_load * self.weights["traffic"])
        
        score = (dist_score * freq_multiplier) * dynamic_alpha
        
        # 2. Weight Penalty
        weight_penalty = 0.0
        if weight > 15.0: # Threshold for heavy items
            # Penalty increases drastically if heavy item is placed on upper floor or far away
            floor_penalty = floor_idx * 50.0
            dist_penalty = max(0, dist_score - 15) * 2.0
            weight_penalty = (floor_penalty + dist_penalty) * self.weights["weight"]
        
        score += weight_penalty
        
        # 3. Congestion Penalty
        congestion_penalty = 0.0
        occupied_count = 0
        # Check 3x3 surrounding
        for dx in [-1, 0, 1]:
            for dy in [-1, 0, 1]:
                if (int(coord.x) + dx, int(coord.y) + dy) in self.floors[floor_idx].occupied_slots:
                    occupied_count += 1
        
        congestion_penalty = occupied_count * self.weights["congestion"]
        score += congestion_penalty
        
        return score

    def suggest_slot(self, product_id: int) -> Optional[Dict]:
        """
        STEP 6: Rank all feasible slots by score and return the best one.
        Returns: Dict with floor_index, coordinate, score, and formatted slot name.
        """
        p_class = self.product_manager.get_product_class(product_id)
        
        candidate_slots = []

        # Collect ALL feasible slots across all floors
        for floor_idx, zones in self.storage_zoning.items():
            warehouse_map = self.floors[floor_idx]
            
            for (x, y), s_class in zones.items():
                coord = WarehouseCoordinate(x, y)
                
                # Apply Filters (Step 4 / Requirement 8.2)
                # This checks bound, storage_matrix, pillar_matrix, and occupancy
                if not warehouse_map.is_slot_available(coord):
                    continue
                    
                # Apply Business Constraints (Step 5)
                if not self._satisfies_business_constraints(product_id, floor_idx, coord):
                    continue

                # Compute Multi-Factor Score (Step 3)
                score = self.calculate_slot_score(floor_idx, coord, product_id)
                
                candidate_slots.append({
                    "floor_idx": floor_idx,
                    "coord": coord,
                    "score": score,
                    "class": s_class
                })

        if not candidate_slots:
            return None

        # Sort slots by score (ascending: lower score is better)
        candidate_slots.sort(key=lambda x: x["score"])

        # Select the best feasible slot
        best = candidate_slots[0]
        
        # Format mapping output: B7-L0-XX-YY
        warehouse_map = self.floors[best["floor_idx"]]
        best["slot_name"] = warehouse_map.get_slot_name(best["coord"])
        
        return best

    def assign_slot(self, product_id: int, floor_idx: int, coord: WarehouseCoordinate) -> bool:
        """
        STEP 7: Officially mark a slot as occupied in the warehouse map.
        This prevents the slot from being suggested for future placements.
        """
        if floor_idx in self.floors:
            self.floors[floor_idx].occupied_slots.add((int(coord.x), int(coord.y)))
            self.slot_to_product[(floor_idx, int(coord.x), int(coord.y))] = product_id
            return True
        return False

    def record_picking_event(self, floor_idx: int, coord: WarehouseCoordinate):
        """
        STEP 8: Dynamic Heatmap Update.
        Increments the traffic count for a specific coordinate.
        This increases the cost (alpha) for this area to prevent over-congestion.
        """
        if floor_idx not in self.traffic_heatmap:
            self.traffic_heatmap[floor_idx] = {}
        
        node = (int(coord.x), int(coord.y))
        self.traffic_heatmap[floor_idx][node] = self.traffic_heatmap[floor_idx].get(node, 0) + 1

    def release_slot(self, floor_idx: int, coord: WarehouseCoordinate):
        """Removes a slot from occupied_slots (e.g., after picking/shipping)."""
        if floor_idx in self.floors:
            self.floors[floor_idx].occupied_slots.discard((int(coord.x), int(coord.y)))
            self.slot_to_product.pop((floor_idx, int(coord.x), int(coord.y)), None)
            return True
        return False

    def check_for_rebalancing(self, traffic_threshold: int = 15) -> List[Dict]:
        """
        Slot Rebalancing Engine. 
        Detects if a zone is overcrowded (traffic > threshold) and suggests relocations.
        """
        relocation_suggestions = []
        
        # 1. Identify hotspots from the heatmap
        for floor_idx, heatmap in self.traffic_heatmap.items():
            for coord_tuple, traffic_count in heatmap.items():
                if traffic_count >= traffic_threshold:
                    # Zone is overcrowded!
                    # 2. Check which product is in this slot
                    product_id = self.slot_to_product.get((floor_idx, coord_tuple[0], coord_tuple[1]))
                    if product_id:
                        # 3. Find a better (lower score) slot for this product in a low-traffic area
                        current_coord = WarehouseCoordinate(coord_tuple[0], coord_tuple[1])
                        current_score = self.calculate_slot_score(floor_idx, current_coord, product_id)
                        
                        # Temporarily release the slot to find alternative suggestions
                        self.floors[floor_idx].occupied_slots.discard(coord_tuple)
                        new_suggestion = self.suggest_slot(product_id)
                        self.floors[floor_idx].occupied_slots.add(coord_tuple) # Restore state
                        
                        if new_suggestion and new_suggestion['score'] < current_score * 0.8:
                            # If we found a slot at least 20% better
                            relocation_suggestions.append({
                                "product_id": product_id,
                                "from_floor": floor_idx,
                                "from_coord": coord_tuple,
                                "to_floor": new_suggestion['floor_idx'],
                                "to_coord": (new_suggestion['coord'].x, new_suggestion['coord'].y),
                                "reason": f"Overcrowded zone (Traffic: {traffic_count})"
                            })
                            
        return relocation_suggestions

    def _is_rack_compatible(self, product_id: int, floor_idx: int, coord: WarehouseCoordinate) -> bool:
        """
        Placeholder for rack compatibility logic.
        Example: Chemical products only in specific fire-safe racks.
        """
        # For now, all racks are compatible with all products
        return True

    def _satisfies_business_constraints(self, product_id: int, floor_idx: int, coord: WarehouseCoordinate) -> bool:
        """
        Hard business constraints that MUST be met.
        Returns False if the coordinate should be eliminated.
        """
        is_haz = self.product_manager.is_hazardous(product_id)
        is_fragile = self.product_manager.is_fragile(product_id)
        
        # 1. Hazardous Item Constraint:
        # Must be in 'Zone Spec' or 'Rack X' if on ground floor
        if is_haz:
            warehouse_map = self.floors[floor_idx]
            allowed_zones = ["Zone Spec", "Rack X"]
            in_safe_zone = False
            for name, coords in warehouse_map.zones.items():
                if any(k in name for k in allowed_zones):
                    segments = coords if isinstance(coords, list) else [coords]
                    for (x1, y1, x2, y2) in segments:
                        if x1 <= coord.x < x2 and y1 <= coord.y < y2:
                            in_safe_zone = True
                            break
            if not in_safe_zone:
                return False

        # 2. Fragile Item Constraint:
        # Avoid high-traffic areas (within 15m path distance from Expedition)
        if is_fragile:
            dist = self.slot_distance_scores.get(floor_idx, {}).get((int(coord.x), int(coord.y)), 100.0)
            if floor_idx == 0 and dist < 15.0:
                return False

        return True

    def _is_storage_zone(self, warehouse_map: DepotB7Map, name: str) -> bool:
        """Determines if a zone name represents a storage area using explicit map metadata."""
        from ..engine.base import ZoneType
        return warehouse_map.zone_types.get(name) == ZoneType.STORAGE

    def _classify_all_floors(self):
        """Initial classification of all available slots into FAST, MEDIUM, SLOW."""
        for floor_index, warehouse_map in self.floors.items():
            self.storage_zoning[floor_index] = {}
            self.slot_distance_scores[floor_index] = {}
            
            # Find Expedition Zones or Entry Points
            entry_points = []
            if floor_index == 0:
                for name, coords in warehouse_map.zones.items():
                    # REQ: Explicitly find Walkable zones related to Shipping
                    if "Expédition" in name:
                        segments = coords if isinstance(coords, list) else [coords]
                        for (x1, y1, x2, y2) in segments:
                            entry_points.append(WarehouseCoordinate((x1 + x2) / 2, (y1 + y2) / 2))
            
            if not entry_points:
                from ..engine.base import ZoneType
                for name, coords in warehouse_map.zones.items():
                    if warehouse_map.zone_types.get(name) == ZoneType.TRANSITION:
                        segments = coords if isinstance(coords, list) else [coords]
                        for (x1, y1, x2, y2) in segments:
                            entry_points.append(WarehouseCoordinate((x1 + x2) / 2, (y1 + y2) / 2))

            if not entry_points:
                entry_points.append(WarehouseCoordinate(0, 0))
            
            # --- STEP 2: Precompute Distance Map using Pathfinding ---
            path_dist_map = warehouse_map.get_path_distance_map(entry_points)
            self.slot_distance_scores[floor_index] = path_dist_map

            # Iterate through all storage zones (Racks)
            for name, coords in warehouse_map.zones.items():
                if not self._is_storage_zone(warehouse_map, name):
                    continue
                    
                # Requirement 8.2: Reserved zones excluded
                if "Reserved" in name:
                    continue

                segments = coords if isinstance(coords, list) else [coords]
                for (x1, y1, x2, y2) in segments:
                    for x in range(int(x1), int(x2)):
                        for y in range(int(y1), int(y2)):
                            coord = WarehouseCoordinate(x, y)
                            
                            # Requirement 8.2: Pillars and Walls excluded from classification
                            if warehouse_map.pillar_matrix[x][y]:
                                continue
                            
                            # Get shortest walking distance from nearest walkable neighbor
                            # (Since the slot itself is occupied by a rack and not walkable)
                            min_p_dist = float('inf')
                            for dx, dy in [(0, 1), (0, -1), (1, 0), (-1, 0), (1, 1), (-1, -1), (1, -1), (-1, 1)]:
                                nx, ny = x + dx, y + dy
                                if (nx, ny) in path_dist_map:
                                    min_p_dist = min(min_p_dist, path_dist_map[(nx, ny)])
                            
                            if min_p_dist == float('inf'):
                                # Fallback to Manhattan if path not found (e.g. isolated slot)
                                min_p_dist = min(warehouse_map.calculate_distance(coord, ep) for ep in entry_points)
                            
                            # Update score with the best found path distance
                            self.slot_distance_scores[floor_index][(x, y)] = min_p_dist

                            # Classification Logic using path distance
                            if floor_index == 0 and min_p_dist < 20:
                                s_class = StorageClass.FAST
                            elif floor_index == 0 and min_p_dist < 40:
                                s_class = StorageClass.MEDIUM
                            elif floor_index > 0 and min_p_dist < 20:
                                s_class = StorageClass.MEDIUM
                            else:
                                s_class = StorageClass.SLOW
                                
                            self.storage_zoning[floor_index][(x, y)] = s_class

    def get_zone_class(self, floor_index: int, x: int, y: int) -> Optional[StorageClass]:
        return self.storage_zoning.get(floor_index, {}).get((x, y))

    def get_summary(self):
        summary = {StorageClass.FAST: 0, StorageClass.MEDIUM: 0, StorageClass.SLOW: 0}
        for floor in self.storage_zoning.values():
            for s_class in floor.values():
                summary[s_class] += 1
        return summary

    def visualize_zoning(self, floor_index: int):
        """Visualizes the classified storage zones in the warehouse."""
        import matplotlib.pyplot as plt
        import matplotlib.patches as patches
        
        if floor_index not in self.floors:
            print(f"Floor {floor_index} not loaded.")
            return

        warehouse_map = self.floors[floor_index]
        fig, ax = plt.subplots(figsize=(12, 8))
        
        # Base warehouse map visualization logic
        rect = patches.Rectangle((0, 0), warehouse_map.width, warehouse_map.height, linewidth=2, edgecolor='black', facecolor='none')
        ax.add_patch(rect)

        # Color mapping for storage classes
        colors = {
            StorageClass.FAST: 'green',
            StorageClass.MEDIUM: 'yellow',
            StorageClass.SLOW: 'salmon'
        }

        # Draw zoning
        zoning = self.storage_zoning.get(floor_index, {})
        for (x, y), s_class in zoning.items():
            rect = patches.Rectangle((x, y), 1, 1, facecolor=colors[s_class], alpha=0.3)
            ax.add_patch(rect)

        # Draw original zones for context
        for name, coords in warehouse_map.zones.items():
            segments = coords if isinstance(coords, list) else [coords]
            for (x1, y1, x2, y2) in segments:
                edge = 'blue' if self._is_storage_zone(warehouse_map, name) else 'gray'
                rect = patches.Rectangle((x1, y1), x2-x1, y2-y1, linewidth=1, edgecolor=edge, facecolor='none', alpha=0.5)
                ax.add_patch(rect)
                ax.text((x1 + x2)/2, (y1 + y2)/2, name, color=edge, fontsize=8, ha='center', va='center')

        ax.set_title(f"Storage Zoning - Floor {floor_index} (Step 1: Classification)")
        ax.set_xlabel("X (m)")
        ax.set_ylabel("Y (m)")
        ax.set_aspect('equal')
        plt.show()
