import sys
import os
sys.path.append(os.getcwd())

def verify_digital_twin():
    print("Verifying Digital Twin Map Integrity...")
    from ai_service.maps import GroundFloorMap, IntermediateFloorMap, UpperFloorMap
    
    # 1. Verify RDC
    print("- RDC Map...")
    rdc = GroundFloorMap()
    assert rdc.width == 42 and rdc.height == 27
    assert len(rdc.pillars) > 0
    assert "Bureau" in rdc.zones
    
    # 2. Verify Floor 1 & 2
    print("- Intermediate Floor Map (Floor 1 & 2)...")
    f1 = IntermediateFloorMap(1)
    print(f"  Dimensions: {f1.width}x{f1.height}")
    print(f"  Pillars: {len(f1.pillars)}")
    assert f1.width == 44 and f1.height == 29
    assert len(f1.pillars) >= 28
    
    # 3. Verify Floor 3 & 4
    print("- Upper Floor Map (Floor 3 & 4)...")
    f3 = UpperFloorMap(3)
    print(f"  Dimensions: {f3.width}x{f3.height}")
    print(f"  Pillars: {len(f3.pillars)}")
    assert f3.width == 46 and f3.height == 31
    assert "A1" in f3.zones
    
    print("\n[SUCCESS] Digital Twin Integrity Verified: Dimensions, Zones, and Obstacles are consistent.")

if __name__ == "__main__":
    try:
        verify_digital_twin()
    except Exception as e:
        print(f"\n[FAILURE] Digital Twin Check failed: {e}")
        sys.exit(1)
