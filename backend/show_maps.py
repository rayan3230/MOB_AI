import sys
import os

# Add the current directory to path so we can import ai_service
sys.path.append(os.getcwd())

try:
    from ai_service.maps import GroundFloorMap, IntermediateFloorMap, UpperFloorMap
    import matplotlib.pyplot as plt
except ImportError as e:
    print(f"Error: {e}")
    print("Ensure you are running this from the 'backend' directory.")
    sys.exit(1)

def main():
    print("--- Warehouse Floor Viewer ---")
    print("0: Ground Floor (RDC)")
    print("1: Floor 1")
    print("2: Floor 2")
    print("3: Floor 3")
    print("4: Floor 4")
    
    choice = input("\nEnter floor number to view (0-4): ")
    
    try:
        floor = int(choice)
        if floor == 0:
            m = GroundFloorMap()
        elif floor in [1, 2]:
            m = IntermediateFloorMap(floor_index=floor)
        elif floor in [3, 4]:
            m = UpperFloorMap(floor_index=floor)
        else:
            print("Invalid floor number.")
            return
            
        print(f"Opening Floor {floor} map...")
        m.visualize()
    except ValueError:
        print("Please enter a valid number.")

if __name__ == "__main__":
    main()
