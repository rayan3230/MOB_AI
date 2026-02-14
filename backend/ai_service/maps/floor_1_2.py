from ..engine.base import DepotB7Map, WarehouseCoordinate, ZoneType
from typing import List

class IntermediateFloorMap(DepotB7Map):
    def __init__(self, floor_index: int = 1):
        # Floors 1 and 2 are 44x29 in the legacy logic
        super().__init__(width=44, height=29, floor_index=floor_index)
        
        self.zones = {
            "Monte Charge 1": (31, 20, 34, 24),
            "Monte Charge 2": (28, 20, 31, 24),
            "A1": (42.5, 20, 43.5, 28.5),
            "A2": (39, 20, 41.2, 28.5),
            "A3": (36.1, 20, 38.5, 28.5),
            "C1": (42.5, 10.5, 43.5, 17.9),
            "C2": (39, 10.5, 41.2, 17.9),
            "C3": (36.1, 10.5, 38.5, 17.9),
            "E1": (42.5, 0.5, 43.5, 8),
            "E2": (39, 0.5, 41.2, 8),
            "E3": (36.6, 0.5, 38.8, 8),
            "E4": (35, 0.5, 36, 8),
            "E5": (32, 0.5, 34, 8),
            "E6": (29.3, 0.5, 31.5, 8),
            "E7": (27.8, 0.5, 28.8, 8),
            "E8": (25, 0.5, 27, 8),
            "E9": (22.1, 0.5, 24.3, 8),
            "E10": (20.5, 0.5, 21.5, 8),
            "E11": (17, 0.5, 19, 8),
            "C7": (25, 10.5, 27, 17.9),
            "C8": (22.1, 10.5, 24.3, 17.9),
            "C9": (20.5, 10.5, 21.5, 17.9),
            "D1": (17, 10.5, 19, 17.9),
            "B1": (17, 20, 19, 28.5),
            "E12": (14.1, 0.5, 16.1, 8),
            "D2": (14.1, 10.5, 16.1, 17.9),
            "B2": (14.1, 20, 16.1, 28.5),
            "E13": (12.6, 0.5, 13.6, 8),
            "D3": (12.6, 10.5, 13.6, 17.9),
            "B3": (12.6, 20.1, 13.6, 28.5),
            "A8": (21.0, 20.0, 23.0, 28.5),
            "E14": (9.5, 0.5, 11.5, 8),
            "D4": (9.5, 10.5, 11.5, 17.9),
            "B4": (9.5, 20.0, 11.5, 28.5),
            "B5": (8, 20.0, 9, 28.5),
            "B6": (1.5, 27, 7, 28),
            "B7": (0.5, 20.0, 1.5, 28.5),
            "E15": (7, 0.5, 9, 8),
            "D5": (7, 10.5, 9, 17.9),
            "E16": (5.2, 0.5, 6.2, 8),
            "D6": (5.2, 10.5, 6.2, 17.9),
            "E17": (2.5, 0.5, 3.5, 8),
            "D7": (2.5, 10.5, 4.5, 17.9),
            "E18": (0.5, 0.5, 1.5, 8),
            "D8": (0.5, 10.5, 1.5, 17.9),
            "A4": [
                (35, 26, 36, 28.5),
                (33.5, 27.5, 35, 28.5)
            ],
            "A5": (23.3, 27, 32, 28),
            "A6": (27.5, 25.5, 31.3, 26.7),
            "A7": (27.5, 24, 31.3, 25.2),
            "C4": (33, 10.5, 35.1, 17.9),
            "C5": (30.5, 10.5, 32.6, 17.9),
            "C6": (27.8, 10.5, 28.8, 17.9),
            "Assenseur": (2, 20.0, 7, 22.5),
        }

        # Explicitly define zone types (REQ: All zones defined explicitly)
        self.zone_types = {}
        for name in self.zones:
            if any(k in name for k in ["Monte Charge", "Assenseur"]):
                self.zone_types[name] = ZoneType.TRANSITION
            else:
                # In floors 1 and 2, almost all zones are storage
                self.zone_types[name] = ZoneType.STORAGE

        self.landmarks = {}
        self.pillars: List[WarehouseCoordinate] = [
            # Line 1 (Y: 26.2 - 27)
            WarehouseCoordinate(12, 26), WarehouseCoordinate(19, 26), WarehouseCoordinate(20, 26), WarehouseCoordinate(27, 26), WarehouseCoordinate(34, 26), WarehouseCoordinate(41, 26),
            # Line 2 (Y: 19.5 - 20.5)
            WarehouseCoordinate(12, 19), WarehouseCoordinate(19, 19), WarehouseCoordinate(20, 19), WarehouseCoordinate(27, 19), WarehouseCoordinate(34, 19), WarehouseCoordinate(41, 19),
            # Line 3 (Y: 13 - 14)
            WarehouseCoordinate(12, 13), WarehouseCoordinate(19, 13), WarehouseCoordinate(20, 13), WarehouseCoordinate(27, 13), WarehouseCoordinate(34, 13), WarehouseCoordinate(41, 13), WarehouseCoordinate(2, 13), WarehouseCoordinate(6, 13),
            # Line 4 (Y: 6.3 - 7.3)
            WarehouseCoordinate(12, 6), WarehouseCoordinate(19, 6), WarehouseCoordinate(20, 6), WarehouseCoordinate(27, 6), WarehouseCoordinate(34, 6), WarehouseCoordinate(41, 6), WarehouseCoordinate(2, 6), WarehouseCoordinate(6, 6)
        ]
        self.special_walls = []
        self._precompute_matrices()
        self.walkable_graph = self.build_walkable_graph()

if __name__ == "__main__":
    import matplotlib.pyplot as plt
    # Test Floor 1
    map_obj = IntermediateFloorMap(floor_index=1)
    print("Visualizing Floor 1...")
    map_obj.visualize()
