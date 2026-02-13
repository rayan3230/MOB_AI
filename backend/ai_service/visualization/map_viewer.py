from ..maps import GroundFloorMap, IntermediateFloorMap, UpperFloorMap
import matplotlib.pyplot as plt

def view_floor(floor_index: int):
    if floor_index == 0:
        warehouse_map = GroundFloorMap()
    elif floor_index in [1, 2]:
        warehouse_map = IntermediateFloorMap(floor_index=floor_index)
    elif floor_index in [3, 4]:
        warehouse_map = UpperFloorMap(floor_index=floor_index)
    else:
        print(f"Floor {floor_index} not specifically defined yet.")
        return

    print(f"Displaying Layout for Floor {floor_index}...")
    warehouse_map.visualize()

if __name__ == "__main__":
    view_floor(0) # Ground floor
    view_floor(3) # 3rd floor
