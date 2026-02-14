import os
import pandas as pd
from django.core.management.base import BaseCommand
from django.conf import settings
from django.utils import timezone
from Users.models import Utilisateur
from Produit.models import Produit
from warhouse.models import Entrepot, Emplacement, NiveauPicking, NiveauStockage
from Transaction.models import Transaction, LigneTransaction

class Command(BaseCommand):
    help = 'Import WMS data from cleaned CSV files into Django database'

    def handle(self, *args, **options):
        csv_dir = os.path.join(settings.BASE_DIR, 'folder_data', 'csv_cleaned')
        
        if not os.path.exists(csv_dir):
            self.stdout.write(self.style.ERROR(f"CSV directory not found at {csv_dir}"))
            return

        def get_path(filename):
            return os.path.join(csv_dir, filename)

        # 1. Import Utilisateurs
        self.stdout.write("Importing Utilisateurs...")
        users_df = pd.read_csv(get_path('utilisateurs.csv'))
        for _, row in users_df.iterrows():
            Utilisateur.objects.update_or_create(
                id_utilisateur=row['id_utilisateur'],
                defaults={
                    'nom_complet': row['nom_complet'],
                    'role': row['role'].upper() if pd.notna(row['role']) else 'EMPLOYEE',
                    'email': row.get('email', '') if pd.notna(row.get('email')) else '',
                    'telephone': row.get('telephone', '') if pd.notna(row.get('telephone')) else '',
                    'adresse': row.get('adresse', '') if pd.notna(row.get('adresse')) else '',
                    'actif': str(row.get('actif', 'True')).lower() == 'true',
                    'password': row.get('password', 'pbkdf2_sha256$260000$defaultpassword'),
                    'is_banned': str(row.get('is_banned', 'False')).lower() == 'true'
                }
            )

        # 2. Import Produits
        self.stdout.write("Importing Produits...")
        products_df = pd.read_csv(get_path('produits.csv'))
        for _, row in products_df.iterrows():
            Produit.objects.update_or_create(
                id_produit=str(row['id_produit']),
                defaults={
                    'sku': str(row['sku']),
                    'nom_produit': row['nom_produit'],
                    'unite_mesure': row.get('unite_mesure', 'PCS'),
                    'categorie': row.get('categorie', 'MISC'),
                    'actif': str(row.get('actif', 'True')).lower() == 'true',
                    # Use .get with default if column might be missing or renamed
                    'poids': float(row.get('Poids(kg)', row.get('poids', 0.0)))
                }
            )

        # 3. Import Entrepots
        self.stdout.write("Importing Entrepots...")
        warehouses_df = pd.read_csv(get_path('entrepots.csv'))
        for _, row in warehouses_df.iterrows():
            Entrepot.objects.update_or_create(
                id_entrepot=row['id_entrepot'],
                defaults={
                    'code_entrepot': row['code_entrepot'],
                    'nom_entrepot': row['nom_entrepot'],
                    'ville': row.get('ville', '') if pd.notna(row.get('ville')) else '',
                    'adresse': row.get('adresse', '') if pd.notna(row.get('adresse')) else '',
                    'actif': str(row.get('actif', 'True')).lower() == 'true'
                }
            )

        # 4. Import Emplacements
        self.stdout.write("Importing Emplacements...")
        locations_df = pd.read_csv(get_path('emplacements.csv'))
        for _, row in locations_df.iterrows():
            try:
                wh = Entrepot.objects.get(id_entrepot=row['id_entrepot'])
                
                # Ensure picking level exists
                picking_level, _ = NiveauPicking.objects.get_or_create(
                    id_entrepot=wh,
                    code_niveau='PICKING',
                    defaults={'description': 'Main Picking Floor'}
                )
                
                Emplacement.objects.update_or_create(
                    id_emplacement=row['id_emplacement'],
                    defaults={
                        'code_emplacement': row['code_emplacement'],
                        'id_entrepot': wh,
                        'zone': row.get('zone', '') if pd.notna(row.get('zone')) else '',
                        'type_emplacement': row.get('type_emplacement', 'STORAGE').upper(),
                        'statut': row.get('statut', 'AVAILABLE').upper(),
                        'actif': str(row.get('actif', 'True')).lower() == 'true',
                        'picking_floor': picking_level if row.get('type_emplacement') == 'PICKING' else None
                    }
                )
            except Entrepot.DoesNotExist:
                continue

        # 5. Import Transactions
        self.stdout.write("Importing Transactions...")
        trans_df = pd.read_csv(get_path('transactions.csv'))
        for _, row in trans_df.iterrows():
            user = None
            if pd.notna(row['cree_par_id_utilisateur']):
                user = Utilisateur.objects.filter(id_utilisateur=row['cree_par_id_utilisateur']).first()
            
            Transaction.objects.update_or_create(
                id_transaction=row['id_transaction'],
                defaults={
                    'type_transaction': row['type_transaction'].upper(),
                    'reference_transaction': row['reference_transaction'],
                    'cree_le': pd.to_datetime(row['cree_le']),
                    'cree_par_id_utilisateur': user,
                    'statut': row['statut'].upper(),
                    'notes': row.get('notes', '') if pd.notna(row.get('notes')) else ''
                }
            )

        # 6. Import Lignes Transaction
        self.stdout.write("Importing Lignes Transaction...")
        lines_df = pd.read_csv(get_path('lignes_transaction.csv'))
        LigneTransaction.objects.all().delete()
        for _, row in lines_df.iterrows():
            try:
                trans = Transaction.objects.get(id_transaction=row['id_transaction'])
                prod = Produit.objects.get(id_produit=str(row['id_produit']))
                
                LigneTransaction.objects.create(
                    id_transaction=trans,
                    no_ligne=int(row['no_ligne']),
                    id_produit=prod,
                    quantite=float(row['quantite']),
                    id_emplacement_source_id=row['id_emplacement_source'] if pd.notna(row['id_emplacement_source']) else None,
                    id_emplacement_destination_id=row['id_emplacement_destination'] if pd.notna(row['id_emplacement_destination']) else None
                )
            except Exception as e:
                pass

        self.stdout.write(self.style.SUCCESS("Successfully imported WMS data from cleaned CSVs!"))
        # Clear existing lines to avoid duplicates on re-import since id_transaction + no_ligne is not the PK
        LigneTransaction.objects.all().delete()
        for _, row in lines_df.iterrows():
            try:
                trans = Transaction.objects.get(id_transaction=row['id_transaction'])
                prod = Produit.objects.get(id_produit=row['id_produit'])
                
                LigneTransaction.objects.create(
                    id_transaction=trans,
                    no_ligne=int(row['no_ligne']),
                    id_produit=prod,
                    quantite=float(row['quantite']),
                    id_emplacement_source_id=row['id_emplacement_source'] if pd.notna(row['id_emplacement_source']) else None,
                    id_emplacement_destination_id=row['id_emplacement_destination'] if pd.notna(row['id_emplacement_destination']) else None
                )
            except Exception as e:
                self.stdout.write(self.style.WARNING(f"Skipping line: {e}"))

        self.stdout.write(self.style.SUCCESS("Successfully imported WMS data!"))
