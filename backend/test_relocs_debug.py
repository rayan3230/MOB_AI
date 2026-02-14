import os
import django
import pandas as pd

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')
django.setup()

from ai_service.api.views import forecast_service, storage_service, floor_maps

def test_relocations():
    print("Loading data...")
    forecast_service.loader.load_and_clean_wrapper()
    print(f"Emplacements in loader: {len(forecast_service.loader.emplacements)}")
    
    print("Syncing physical state...")
    storage_service.sync_physical_state(forecast_service.loader.emplacements)
    print(f"Occupied slots in twin: {len(storage_service.floors[0].occupied_slots)}")
    print(f"Products in map: {len(storage_service.slot_to_product)}")
    
    print("Checking for rebalancing...")
    relocs = storage_service.check_for_rebalancing(traffic_threshold=100)
    print(f"Relocations suggested: {len(relocs)}")
    
    for r in relocs[:5]:
        from_code = storage_service.slot_to_code.get((r['from_floor'], r['from_coord'][0], r['from_coord'][1]))
        to_name = floor_maps[r['to_floor']].get_slot_name(r['to_coord']) # typo fixed later if needed
        print(f"MOVE Product {r['product_id']} from {from_code} to {to_name} (Reason: {r['reason']})")

if __name__ == "__main__":
    test_relocations()
