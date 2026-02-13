from initialisation_map import DepotB7Map
import matplotlib.pyplot as plt

def show_upper_floors():
    print("Generating schemas for Floor 1 and Floor 2...")
    
    # Floor 1
    floor1 = DepotB7Map(floor_index=1)
    print(f"Displaying {floor1.width}x{floor1.height} layout for Etage 1")
    floor1.visualize()
    
    # Floor 2
    floor2 = DepotB7Map(floor_index=2)
    print(f"Displaying {floor2.width}x{floor2.height} layout for Etage 2")
    floor2.visualize()

if __name__ == "__main__":
    show_upper_floors()
