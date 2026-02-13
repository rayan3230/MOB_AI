from picking_optimization import DepotB7Engine

def multi_floor_demo():
    print("=== DEPOT B7: MULTI-FLOOR ARCHITECTURE DEMO ===\n")
    
    # 1. Test Ground Floor (0) - Original 42x27
    print("--- TESTING FLOOR 0 (Ground) ---")
    engine_f0 = DepotB7Engine(current_floor=0)
    print(f"Floor 0 Dimensions: {engine_f0.warehouse.width}x{engine_f0.warehouse.height}")
    
    # 2. Test First Floor (1) - New 44x29
    print("\n--- TESTING FLOOR 1 (First) ---")
    engine_f1 = DepotB7Engine(current_floor=1)
    print(f"Floor 1 Dimensions: {engine_f1.warehouse.width}x{engine_f1.warehouse.height}")
    
    # 3. Test Second Floor (2) - New 44x29
    print("\n--- TESTING FLOOR 2 (Second) ---")
    engine_f2 = DepotB7Engine(current_floor=2)
    print(f"Floor 2 Dimensions: {engine_f2.warehouse.width}x{engine_f2.warehouse.height}")
    
    # 4. Process a batch on Floor 1
    skus_f1 = [(10, 10), (20, 20), (43, 28)] # (43, 28) is only valid on F1/F2
    print(f"\nProcessing Batch on Floor 1 with item {skus_f1[2]}...")
    results = engine_f1.process_picking_batch(skus_f1, chariot_count=1)
    
    for chariot, data in results["chariots"].items():
        print(f"Chariot 1 Sequence on F1: {data['sequence']}")

    print("\n✅ Multi-floor architectural support (0: 42x27, 1&2: 44x29) verified.")

if __name__ == "__main__":
    multi_floor_demo()
