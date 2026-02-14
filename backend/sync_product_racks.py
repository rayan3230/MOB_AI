import os
import django
import sys

# Set up Django environment
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(current_dir)
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')
django.setup()

from Produit.models import Produit
from warhouse.models import RackProduct

def run():
    print("Starting update...")
    # Map product_id to a rack from RackProduct table
    mapping = {rp.product_id: rp.rack for rp in RackProduct.objects.all()}
    count = len(mapping)
    print(f"Found {count} assignments.")
    
    products_to_update = []
    for p in Produit.objects.filter(id_produit__in=mapping.keys()):
        p.id_rack = mapping[p.id_produit]
        products_to_update.append(p)
    
    if products_to_update:
        Produit.objects.bulk_update(products_to_update, ['id_rack'])
        print(f"Successfully updated {len(products_to_update)} products.")
    else:
        print("No products found to update.")

if __name__ == "__main__":
    run()
