from ..engine.base import DepotB7Map, WarehouseCoordinate

class GroundFloorMap(DepotB7Map):
    def __init__(self):
        super().__init__(width=42, height=27, floor_index=0)
        self.zones = {
            "V": (4, 1, 5, 11), "S": (5, 1, 6, 11), "Bureau": (28, 0, 42, 7),
            "Expédition 1": (35, 7, 42, 13), "Expédition 2": (35, 13, 42, 20),
            "VRAC": (28, 20, 42, 27), "Monte Charge 1": (31, 20, 34, 24),
            "Monte Charge 2": (28, 20, 31, 24), "B": (25, 1, 26, 11),
            "F": (20, 1, 21, 11), "D": (21, 1, 22, 11), "K": (15, 1, 16, 11),
            "H": (16, 1, 17, 11), "Q": (10, 1, 11, 11), "N": (11, 1, 12, 11),
            "W": (1, 2, 2, 20), "Assenseur": (0, 20, 5, 22), "Zone Spec": (0, 20, 9, 27),
            "Black object": (29, 7, 35, 9), "T": (4, 13, 5, 20), "R": (5, 13, 6, 20),
            "P": (10, 13, 11, 20), "M": (11, 13, 12, 20), "I": (15, 13, 16, 20),
            "G": (16, 13, 17, 20), "E": (20, 13, 21, 20), "C": (24, 13, 25, 20),
            "A": (25, 13, 26, 20), "Rack X": [(9, 22, 10, 25), (10, 25, 17, 26), (14, 20, 17, 21), (17, 21, 18, 24)],
            "Reserved": (24, 20, 28, 27)
        }
        self.landmarks = {
            "Chariot Start 1": WarehouseCoordinate(34, 10),
            "Chariot Start 2": WarehouseCoordinate(34, 16)
        }
        self.pillars = [
            WarehouseCoordinate(11, 7), WarehouseCoordinate(4, 7), WarehouseCoordinate(20, 7),
            WarehouseCoordinate(19, 7), WarehouseCoordinate(18, 7), WarehouseCoordinate(11, 13),
            WarehouseCoordinate(20, 13), WarehouseCoordinate(19, 13), WarehouseCoordinate(18, 13),
            WarehouseCoordinate(25, 13), WarehouseCoordinate(26, 13), WarehouseCoordinate(4, 13),
            WarehouseCoordinate(11, 20)
        ]
        for x_wall in range(35, 43): self.pillars.append(WarehouseCoordinate(x_wall, 13))
        self.special_walls = [(18, 21, 0.1, 6)]
        for (xw, yw, ww, hw) in self.special_walls:
            for y_step in range(int(yw), int(yw + hw)): self.pillars.append(WarehouseCoordinate(int(xw), y_step))
        
        self._precompute_matrices()
        self.walkable_graph = self.build_walkable_graph()

if __name__ == "__main__":
    import matplotlib.pyplot as plt
    map_obj = GroundFloorMap()
    print("Visualizing Ground Floor (RDC)...")
    map_obj.visualize()
