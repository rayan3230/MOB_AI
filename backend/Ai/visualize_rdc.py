from initialisation_map import DepotB7Map
import matplotlib.pyplot as plt

def show_rdc_plan():
    print("Generating schema for RDC (Ground Floor)...")
    
    # Initialize Floor 0 (RDC)
    rdc = DepotB7Map(floor_index=0)
    print(f"Displaying {rdc.width}x{rdc.height} layout for RDC")
    
    # Use the industrial-grade visualization method
    rdc.visualize()
    plt.show()

if __name__ == "__main__":
    show_rdc_plan()
