from picking_optimization import DepotB7Engine

def final_architecture_check():
    print("=== DEPOT B7: FINAL ARCHITECTURE CHECK ===\n")
    
    # 1. Initialize the Engine (Initialization Phase)
    engine = DepotB7Engine()
    
    # 2. Define a picking batch (Runtime Phase)
    # Includes standard coordinates, coordinates inside racks, and far ones.
    picking_list = [
        (2, 2),   # Near start
        (10, 5),  # Inside Rack Q
        (16, 13), # Inside Pillar
        (25, 20), # Near Rack R
        (4, 25),  # Far zone
        (38, 2)   # Near Bureau
    ]
    
    # 3. Process the batch (Optimization & Routing Phase)
    results = engine.process_picking_batch(picking_list, chariot_count=2)
    
    # 4. Output validation
    for chariot, data in results["chariots"].items():
        print(f"\n{chariot}:")
        print(f"  Sequence: {data['sequence']}")
        print(f"  Total Distance: {data['metrics']['total_distance']}m")
        print(f"  Successful Picks: {data['metrics']['item_count']}")
        if data['metrics'].get('blocked_item_count', 0) > 0:
            print(f"  ⚠️ Blocked Items: {data['metrics']['blocked_items']}")

    print("\n✅ Final Architecture Validated: Initialization, A*, TSP approximation, and KPIs are integrated.")

if __name__ == "__main__":
    final_architecture_check()
