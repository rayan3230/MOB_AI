import os
import django
import random
from decimal import Decimal

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')
django.setup()

from warhouse.models import Stock, Emplacement
from Produit.models import Produit

def seed_stocks():
    products = list(Produit.objects.all()[:50])
    # Pick emplacements that are likely in "SLOW" zones (Q, R, S, T)
    empls = list(Emplacement.objects.filter(code_emplacement__regex=r'^0[QRST]'))
    
    if not empls:
        empls = list(Emplacement.objects.all()[:100])
        
    print(f"Seeding {len(products)} stocks into {len(empls)} emplacements...")
    
    for i, p in enumerate(products):
        e = empls[i % len(empls)]
        Stock.objects.update_or_create(
            id_stock=f"STK-{p.id_produit}",
            defaults={
                'id_produit': p,
                'id_emplacement': e,
                'quantite': Decimal('100.00'),
                'quantite_reservee': Decimal('0.00')
            }
        )
    print("Seeding complete.")

if __name__ == "__main__":
    seed_stocks()
