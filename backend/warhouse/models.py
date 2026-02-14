from django.db import models, transaction
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone
from Produit.models import Produit
from Users.models import Utilisateur


# ============================================================================
# SECTION 1: WAREHOUSE STRUCTURE (FR-10 → FR-17)
# ============================================================================

class Entrepot(models.Model):
    """
    Warehouse (Depot)
    FR-10, FR-11, FR-12
    Top-level warehouse entity
    """
    id_entrepot = models.CharField(max_length=10, primary_key=True, blank=True)
    code_entrepot = models.CharField(max_length=50, unique=True)
    nom_entrepot = models.CharField(max_length=255)
    ville = models.CharField(max_length=100, null=True, blank=True)
    adresse = models.CharField(max_length=255, null=True, blank=True)
    actif = models.BooleanField(default=True)
    cree_le = models.DateTimeField(auto_now_add=True, null=True, blank=True)

    def save(self, *args, **kwargs):
        is_new = not self.id_entrepot
        if not self.id_entrepot:
            # Generate a new ID like WH001, WH002...
            last_entrepot = Entrepot.objects.all().order_by('id_entrepot').last()
            if not last_entrepot:
                self.id_entrepot = 'WH001'
            else:
                try:
                    # Try to parse the last numeric part
                    import re
                    match = re.search(r'\d+', last_entrepot.id_entrepot)
                    if match:
                        num = int(match.group())
                        self.id_entrepot = f'WH{num + 1:03d}'
                    else:
                        self.id_entrepot = last_entrepot.id_entrepot + '1'
                except:
                    self.id_entrepot = 'WH' + str(Entrepot.objects.count() + 1).zfill(3)
        
        # Ensure ID doesn't exceed 10 chars
        self.id_entrepot = self.id_entrepot[:10]
        super().save(*args, **kwargs)

        if is_new:
            # Create default structure (1 Storage Floor + 1 Picking Floor)
            # This triggers the automatic rack and capacity generation in Floor models
            NiveauPicking.objects.create(
                id_entrepot=self,
                code_niveau='PICKING',
                description='Main Picking Floor (A-X)'
            )
            
            # Create the first storage floor (N1)
            NiveauStockage.objects.create(
                id_entrepot=self,
                code_niveau='N1',
                type_niveau='STOCK',
                description='Storage Floor 1'
            )

            # Create VRacks for existing products (Optimized with bulk_create)
            from Produit.models import Produit
            products = Produit.objects.all()
            vracks = []
            for produit in products:
                vracks.append(Vrack(
                    id_vrack=f"VRK_{self.id_entrepot}_{produit.id_produit}",
                    id_entrepot=self,
                    id_produit=produit,
                    quantite=0
                ))
            Vrack.objects.bulk_create(vracks, ignore_conflicts=True)

    def __str__(self):
        return f"{self.id_entrepot} - {self.nom_entrepot}"

    class Meta:
        db_table = 'entrepots'


class NiveauStockage(models.Model):
    """
    Storage Floors/Levels (For stocking only)
    """
    TYPE_CHOICES = [
        ('STOCK', 'Stocking Level'),
    ]

    id_niveau = models.CharField(max_length=100, primary_key=True, blank=True)
    id_entrepot = models.ForeignKey(Entrepot, on_delete=models.CASCADE, related_name='niveaux_stockage')
    code_niveau = models.CharField(max_length=50)  # N1, N2, N3, N4
    type_niveau = models.CharField(max_length=20, choices=TYPE_CHOICES, default='STOCK')
    description = models.CharField(max_length=255, null=True, blank=True)
    cree_le = models.DateTimeField(auto_now_add=True, null=True, blank=True)

    def save(self, *args, **kwargs):
        is_new = not self.id_niveau
        if not self.id_niveau:
            # Generate ID based on warehouse ID and code
            self.id_niveau = f"{self.id_entrepot_id}_{self.code_niveau}"
        
        # Enforce business rules: Max 4 Stocking
        stocking_count = NiveauStockage.objects.filter(
            id_entrepot=self.id_entrepot, 
            type_niveau='STOCK'
        ).exclude(id_niveau=self.id_niveau).count()
        if stocking_count >= 4:
            from django.core.exceptions import ValidationError
            raise ValidationError("A warehouse cannot have more than 4 stocking floors.")

        super().save(*args, **kwargs)

        if is_new:
            # Create 2 default locations for each stocking floor
            for i in range(1, 3):
                code = f"{self.code_niveau}-S{i}"
                Emplacement.objects.create(
                    id_entrepot=self.id_entrepot,
                    storage_floor=self,
                    code_emplacement=code,
                    type_emplacement='STORAGE',
                    statut='AVAILABLE'
                )
            
            # Create default racks based on floor number
            # N1, N2 are Floors 1-2. N3, N4 are Floors 3-4.
            racks_data = []
            
            if self.code_niveau in ['N1', 'N2']:
                # Row A (Floor 1-2)
                for i in range(1, 9): racks_data.append((f"A{i}", 4 if i==4 else (11 if i in [5,6,7] else 9)))
                # Row B (Floor 1-2)
                for i in range(1, 8): racks_data.append((f"B{i}", 13 if i==6 else 9))
                # Row C, D, E (Floor 1-2)
                for i in range(1, 10): racks_data.append((f"C{i}", 9))
                for i in range(1, 9): racks_data.append((f"D{i}", 9))
                for i in range(1, 19): racks_data.append((f"E{i}", 9))
            
            elif self.code_niveau in ['N3', 'N4']:
                # Row A (Floor 3-4): A1-A3(9), A4(5 horiz), A5(13 horiz), A6(9)
                for i in range(1, 4): racks_data.append((f"A{i}", 9))
                racks_data.append(("A4", 5))
                racks_data.append(("A5", 13))
                racks_data.append(("A6", 9))
                # Row B (Floor 3-4): B1-B4(9), B5(13 horiz), B6(9)
                for i in range(1, 5): racks_data.append((f"B{i}", 9))
                racks_data.append(("B5", 13))
                racks_data.append(("B6", 9))
                # Row C (Floor 3-4): C1-C12(9)
                for i in range(1, 13): racks_data.append((f"C{i}", 9))
                # Row D (Floor 3-4): D1-D14(9)
                for i in range(1, 15): racks_data.append((f"D{i}", 9))
                # Row E (Floor 3-4): E1-E17(9)
                for i in range(1, 18): racks_data.append((f"E{i}", 9))

            racks = []
            for code, cap in racks_data:
                rack_id = f"{self.id_entrepot_id}_{self.id_niveau}_{code}"
                racks.append(Rack(
                    id_rack=rack_id,
                    storage_floor=self,
                    code_rack=code,
                    capacity=cap,
                    description=f"Automatic Storage Rack {code}"
                ))
            Rack.objects.bulk_create(racks, ignore_conflicts=True)

    class Meta:
        db_table = 'niveaux_stockage'
        unique_together = [['id_entrepot', 'code_niveau']]

    def __str__(self):
        return f"{self.id_niveau} - {self.code_niveau}"


class NiveauPicking(models.Model):
    """
    Picking Floor Table (Separate table as requested)
    FR-13 subset
    """
    id_niveau_picking = models.CharField(max_length=100, primary_key=True, blank=True)
    id_entrepot = models.ForeignKey(Entrepot, on_delete=models.CASCADE, related_name='niveaux_picking')
    code_niveau = models.CharField(max_length=50)
    description = models.CharField(max_length=255, null=True, blank=True)
    cree_le = models.DateTimeField(auto_now_add=True, null=True, blank=True)

    def save(self, *args, **kwargs):
        is_new = not self.id_niveau_picking
        if not self.id_niveau_picking:
            self.id_niveau_picking = f"PICK_{self.id_entrepot_id}_{self.code_niveau}"
        
        # Enforce business rules: Exactly 1 Picking per warehouse
        if NiveauPicking.objects.filter(id_entrepot=self.id_entrepot).exclude(id_niveau_picking=self.id_niveau_picking).exists():
            from django.core.exceptions import ValidationError
            raise ValidationError("A warehouse can only have one picking floor.")
            
        super().save(*args, **kwargs)

        if is_new:
            # Create a "v rack" location automatically
            Emplacement.objects.create(
                id_entrepot=self.id_entrepot,
                picking_floor=self,
                code_emplacement=f"V-RACK-{self.id_entrepot_id}",
                type_emplacement='PICKING',
                statut='AVAILABLE',
                zone='Picking Area'
            )
            # Create a second default location for the picking floor
            Emplacement.objects.create(
                id_entrepot=self.id_entrepot,
                picking_floor=self,
                code_emplacement=f"{self.code_niveau}-P1",
                type_emplacement='PICKING',
                statut='AVAILABLE'
            )

            # Create default racks for the picking floor (FR-13 extension)
            racks_codes = "ABCDEFGHIKMNPQRSTVWX"
            racks = []
            for code in racks_codes:
                # Capacity logic based on code
                cap = 10  # Default
                if code in "ACEGIPR": cap = 7
                elif code in "BDFHKQS": cap = 10
                elif code == 'W': cap = 18
                elif code in 'MT': cap = 6
                elif code in 'NV': cap = 9
                elif code == 'X': cap = 17

                rack_id = f"{self.id_entrepot_id}_{self.id_niveau_picking}_{code}"
                racks.append(Rack(
                    id_rack=rack_id,
                    picking_floor=self,
                    code_rack=code,
                    capacity=cap,
                    description=f"Automatic Picking Rack {code}"
                ))
            Rack.objects.bulk_create(racks, ignore_conflicts=True)

    class Meta:
        db_table = 'niveaux_picking'
        unique_together = [['id_entrepot', 'code_niveau']]

    def __str__(self):
        return f"{self.id_niveau_picking} - {self.code_niveau}"


class Rack(models.Model):
    """
    Racks located on Floors (NiveauStockage or NiveauPicking)
    """
    id_rack = models.CharField(max_length=100, primary_key=True, blank=True)
    storage_floor = models.ForeignKey(NiveauStockage, on_delete=models.CASCADE, null=True, blank=True, related_name='racks')
    picking_floor = models.ForeignKey(NiveauPicking, on_delete=models.CASCADE, null=True, blank=True, related_name='racks')
    code_rack = models.CharField(max_length=50)
    capacity = models.IntegerField(default=100)  # Total storing capacity
    description = models.CharField(max_length=255, null=True, blank=True)
    cree_le = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        if not self.id_rack:
            # Composed ID: warehouseid + floorid + rack name
            warehouse_id = ""
            floor_id = ""
            if self.storage_floor:
                warehouse_id = self.storage_floor.id_entrepot_id
                floor_id = self.storage_floor.id_niveau
            elif self.picking_floor:
                warehouse_id = self.picking_floor.id_entrepot_id
                floor_id = self.picking_floor.id_niveau_picking
            
            self.id_rack = f"{warehouse_id}_{floor_id}_{self.code_rack}"
        super().save(*args, **kwargs)

    def __str__(self):
        floor_info = self.storage_floor.code_niveau if self.storage_floor else self.picking_floor.code_niveau
        return f"Rack {self.code_rack} - {floor_info}"

    class Meta:
        db_table = 'racks'


class RackProduct(models.Model):
    """
    Products stored in a Rack with their quantities
    """
    rack = models.ForeignKey(Rack, on_delete=models.CASCADE, related_name='rack_products')
    product = models.ForeignKey(Produit, on_delete=models.CASCADE, related_name='rack_assignments')
    quantity = models.DecimalField(max_digits=12, decimal_places=2, default=0)

    class Meta:
        db_table = 'rack_products'
        unique_together = [['rack', 'product']]

    def __str__(self):
        return f"{self.product.sku} in {self.rack.code_rack}: {self.quantity}"


class Emplacement(models.Model):
    """
    Storage & Picking Locations
    Can link to either NiveauStockage or NiveauPicking
    """
    TYPE_CHOICES = [
        ('STORAGE', 'Storage Location'),
        ('PICKING', 'Picking Location'),
    ]

    STATUS_CHOICES = [
        ('AVAILABLE', 'Available'),
        ('OCCUPIED', 'Occupied'),
        ('BLOCKED', 'Blocked'),
    ]

    id_emplacement = models.CharField(max_length=100, primary_key=True, blank=True)
    code_emplacement = models.CharField(max_length=50)  # FR-17: Unique code per location
    id_entrepot = models.ForeignKey(Entrepot, on_delete=models.CASCADE, related_name='emplacements')
    storage_floor = models.ForeignKey(NiveauStockage, on_delete=models.SET_NULL, null=True, blank=True, related_name='emplacements')
    picking_floor = models.ForeignKey(NiveauPicking, on_delete=models.SET_NULL, null=True, blank=True, related_name='emplacements')
    zone = models.CharField(max_length=50, null=True, blank=True)
    type_emplacement = models.CharField(max_length=50, choices=TYPE_CHOICES)  # STORAGE or PICKING
    statut = models.CharField(max_length=50, choices=STATUS_CHOICES, default='AVAILABLE')
    actif = models.BooleanField(default=True)
    cree_le = models.DateTimeField(auto_now_add=True, null=True, blank=True)
    mise_a_jour_le = models.DateTimeField(auto_now=True, null=True, blank=True)

    def save(self, *args, **kwargs):
        if not self.id_emplacement:
            # Generate ID based on warehouse ID and code
            self.id_emplacement = f"{self.id_entrepot_id}_{self.code_emplacement}"
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.id_emplacement} - {self.code_emplacement}"

    class Meta:
        db_table = 'emplacements'
        unique_together = [['id_entrepot', 'code_emplacement']]


# ============================================================================
# SECTION 2: INVENTORY SYSTEM (FR-23 → FR-27)
# ============================================================================

class Stock(models.Model):
    """
    Current Stock Snapshot
    FR-23, FR-24, FR-27
    Tracks quantity per SKU per location
    Prevents negative stock (FR-24)
    Composite unique key: SKU + Location + Lot
    """
    id_stock = models.CharField(max_length=30, primary_key=True)
    id_produit = models.ForeignKey(Produit, on_delete=models.CASCADE, related_name='stocks')
    id_emplacement = models.ForeignKey(Emplacement, on_delete=models.CASCADE, related_name='stocks')
    quantite = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    quantite_reservee = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    lot_serie = models.CharField(max_length=100, null=True, blank=True)
    date_expiration = models.DateField(null=True, blank=True)
    mise_a_jour_le = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'stocks'
        unique_together = [['id_produit', 'id_emplacement', 'lot_serie']]

    def __str__(self):
        return f"{self.id_produit} @ {self.id_emplacement}: {self.quantite}"


class Vrack(models.Model):
    """
    Vrack Storage System (Bulk Storage)
    FR-23 extension: Tracks quantity per SKU in the V-Rack area
    Stores different products and their cumulative quantities
    """
    id_vrack = models.CharField(max_length=50, primary_key=True, blank=True)
    id_entrepot = models.ForeignKey(Entrepot, on_delete=models.CASCADE, related_name='vracks')
    id_produit = models.ForeignKey(Produit, on_delete=models.CASCADE, related_name='vracks')
    quantite = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    mise_a_jour_le = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        if not self.id_vrack:
            # Composite ID: VRK + Warehouse ID + Product ID
            self.id_vrack = f"VRK_{self.id_entrepot_id}_{self.id_produit_id}"
        super().save(*args, **kwargs)

    class Meta:
        db_table = 'vracks'
        unique_together = [['id_entrepot', 'id_produit']]

    def __str__(self):
        return f"Vrack [{self.id_entrepot_id}] - {self.id_produit.sku}: {self.quantite}"


class MouvementStock(models.Model):
    """
    Stock Movement Ledger (IMMUTABLE)
    FR-25, FR-26, NFR-3, NFR-10
    All inventory movements logged immutably
    Every transaction creates a movement record
    """
    TYPES_MOUVEMENT = [
        ('RECEPTION', 'Reception'),
        ('TRANSFERT', 'Transfer'),
        ('PICKING', 'Picking'),
        ('LIVRAISON', 'Delivery'),
        ('AJUSTEMENT', 'Adjustment'),
        ('PERTE', 'Loss'),
    ]

    id_mouvement = models.CharField(max_length=30, primary_key=True)
    id_entrepot = models.ForeignKey(Entrepot, on_delete=models.CASCADE, null=True, blank=True, related_name='mouvements_stock')
    type_mouvement = models.CharField(max_length=50, choices=TYPES_MOUVEMENT)
    id_produit = models.ForeignKey(Produit, on_delete=models.SET_NULL, null=True, related_name='mouvements_stock')
    id_emplacement_source = models.ForeignKey(Emplacement, on_delete=models.SET_NULL, null=True, blank=True, related_name='mouvements_stock_source')
    id_emplacement_destination = models.ForeignKey(Emplacement, on_delete=models.SET_NULL, null=True, blank=True, related_name='mouvements_stock_destination')
    quantite = models.DecimalField(max_digits=12, decimal_places=2)
    lot_serie = models.CharField(max_length=100, null=True, blank=True)
    motif_code = models.CharField(max_length=50, null=True, blank=True)
    reference_transaction = models.CharField(max_length=100, null=True, blank=True)
    execute_par = models.ForeignKey(Utilisateur, on_delete=models.SET_NULL, null=True, related_name='mouvements_stock')
    date_execution = models.DateTimeField(auto_now_add=True)
    notes = models.TextField(null=True, blank=True)

    class Meta:
        db_table = 'mouvements_stock'
        ordering = ['-date_execution']
        indexes = [
            models.Index(fields=['id_produit', 'date_execution']),
            models.Index(fields=['type_mouvement', 'date_execution']),
        ]

    def __str__(self):
        return f"{self.id_mouvement} - {self.type_mouvement}"


# ============================================================================
# SECTION 3: CHARIOT SYSTEM (FR-30 → FR-34)
# ============================================================================

class Chariot(models.Model):
    """
    Trolley/Cart for picking operations
    FR-30, FR-31, FR-32, FR-33, FR-34
    """
    STATUT_CHOICES = [
        ('AVAILABLE', 'Available'),
        ('IN_USE', 'In Use'),
        ('MAINTENANCE', 'Maintenance'),
        ('INACTIVE', 'Inactive'),
    ]

    id_chariot = models.CharField(max_length=20, primary_key=True, blank=True)
    code_chariot = models.CharField(max_length=50, unique=True)
    id_entrepot = models.ForeignKey(Entrepot, on_delete=models.CASCADE, related_name='chariots')
    statut = models.CharField(max_length=50, choices=STATUT_CHOICES, default='AVAILABLE')
    id_emplacement_courant = models.ForeignKey(Emplacement, on_delete=models.SET_NULL, null=True, blank=True, related_name='chariots_courants')
    capacite = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    cree_le = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        if not self.id_chariot:
            # Generate a new ID like CH0001, CH0002...
            last_chariot = Chariot.objects.all().order_by('id_chariot').last()
            if not last_chariot:
                self.id_chariot = 'CH0001'
            else:
                try:
                    import re
                    match = re.search(r'\d+', last_chariot.id_chariot)
                    if match:
                        num = int(match.group())
                        self.id_chariot = f'CH{num + 1:04d}'
                    else:
                        self.id_chariot = last_chariot.id_chariot + '1'
                except:
                    self.id_chariot = 'CH' + str(Chariot.objects.count() + 1).zfill(4)
        super().save(*args, **kwargs)

    class Meta:
        db_table = 'chariots'

    def __str__(self):
        return f"{self.id_chariot} - {self.code_chariot}"


class ChariotOperation(models.Model):
    """
    Chariot Assignment to Operations
    FR-34: Track chariot usage in operations
    """
    id_chariot_operation = models.CharField(max_length=30, primary_key=True)
    id_chariot = models.ForeignKey(Chariot, on_delete=models.CASCADE, related_name='operations')
    id_emplacement_courant = models.ForeignKey(Emplacement, on_delete=models.SET_NULL, null=True, blank=True, related_name='chariot_operations')
    date_assignation = models.DateTimeField(auto_now_add=True)
    date_liberation = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = 'chariot_operations'

    def __str__(self):
        return f"{self.id_chariot_operation}"


# ============================================================================
# SECTION 4: ORDER SYSTEM (FR-40 → FR-47)
# ============================================================================

class Commande(models.Model):
    """
    Generic Order (Command, Preparation, Picking)
    FR-40, FR-41, FR-42, FR-43, FR-44, FR-45, FR-46, FR-47
    """
    TYPE_CHOICES = [
        ('COMMAND', 'Command Order'),
        ('PREPARATION', 'Preparation Order'),
        ('PICKING', 'Picking Order'),
    ]

    STATUS_CHOICES = [
        ('DRAFT', 'Draft'),
        ('GENERATED', 'Generated'),
        ('IN_PROGRESS', 'In Progress'),
        ('COMPLETED', 'Completed'),
        ('CANCELLED', 'Cancelled'),
    ]

    id_commande = models.CharField(max_length=30, primary_key=True)
    type_commande = models.CharField(max_length=50, choices=TYPE_CHOICES)
    statut = models.CharField(max_length=50, choices=STATUS_CHOICES, default='DRAFT')
    reference = models.CharField(max_length=100, null=True, blank=True)
    creation_le = models.DateTimeField(auto_now_add=True)
    cree_par = models.ForeignKey(Utilisateur, on_delete=models.SET_NULL, null=True, blank=True, related_name='commandes_creees')
    debut_le = models.DateTimeField(null=True, blank=True)
    fin_le = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = 'commandes'
        ordering = ['-creation_le']

    def __str__(self):
        return f"{self.id_commande} - {self.type_commande}"


class LigneCommande(models.Model):
    """
    Order Line Item
    Composite unique key: Order + Line Number
    """
    id_ligne = models.CharField(max_length=30, primary_key=True)
    id_commande = models.ForeignKey(Commande, on_delete=models.CASCADE, related_name='lignes')
    id_produit = models.ForeignKey(Produit, on_delete=models.SET_NULL, null=True, related_name='lignes_commande')
    id_emplacement_source = models.ForeignKey(Emplacement, on_delete=models.SET_NULL, null=True, blank=True, related_name='lignes_commande_source')
    id_emplacement_destination = models.ForeignKey(Emplacement, on_delete=models.SET_NULL, null=True, blank=True, related_name='lignes_commande_destination')
    quantite = models.DecimalField(max_digits=12, decimal_places=2)
    quantite_completee = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    no_ligne = models.IntegerField()

    class Meta:
        db_table = 'lignes_commande'
        unique_together = [['id_commande', 'no_ligne']]

    def __str__(self):
        return f"{self.id_commande} - Line {self.no_ligne}"


class ResultatLivraison(models.Model):
    """
    Delivery Validation Results
    FR-47: Track delivery success/failure
    """
    STATUT_CHOICES = [
        ('VALIDATED', 'Validated'),
        ('FAILED', 'Failed'),
        ('PARTIAL', 'Partial'),
    ]

    id_resultat = models.CharField(max_length=30, primary_key=True)
    id_commande = models.OneToOneField(Commande, on_delete=models.CASCADE, related_name='resultat_livraison')
    statut = models.CharField(max_length=50, choices=STATUT_CHOICES)
    valide_par = models.ForeignKey(Utilisateur, on_delete=models.SET_NULL, null=True, related_name='livraisons_validees')
    date_validation = models.DateTimeField(auto_now_add=True)
    notes = models.TextField(null=True, blank=True)

    class Meta:
        db_table = 'resultats_livraison'

    def __str__(self):
        return f"{self.id_resultat} - {self.statut}"


# ============================================================================
# SECTION 5: OPERATION EXECUTION (FR-50 → FR-57)
# ============================================================================

class Operation(models.Model):
    """
    Operation Execution Record
    FR-50: Receipt, FR-51: Transfer, FR-52: Picking, FR-53: Delivery
    Transactional execution of orders
    """
    TYPE_CHOICES = [
        ('RECEPTION', 'Reception'),
        ('TRANSFERT', 'Transfer'),
        ('PICKING', 'Picking'),
        ('LIVRAISON', 'Delivery'),
    ]

    STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('IN_PROGRESS', 'In Progress'),
        ('COMPLETED', 'Completed'),
        ('FAILED', 'Failed'),
    ]

    id_operation = models.CharField(max_length=30, primary_key=True)
    type_operation = models.CharField(max_length=50, choices=TYPE_CHOICES)
    id_commande = models.ForeignKey(Commande, on_delete=models.SET_NULL, null=True, blank=True, related_name='operations')
    statut = models.CharField(max_length=50, choices=STATUS_CHOICES, default='PENDING')
    date_debut = models.DateTimeField(auto_now_add=True)
    date_fin = models.DateTimeField(null=True, blank=True)
    execute_par = models.ForeignKey(Utilisateur, on_delete=models.SET_NULL, null=True, related_name='operations')

    class Meta:
        db_table = 'operations'
        ordering = ['-date_debut']

    def __str__(self):
        return f"{self.id_operation} - {self.type_operation}"


# ============================================================================
# SECTION 6: AI SYSTEM (FR-8, AI Order Generation)
# ============================================================================

class PrevisionIA(models.Model):
    """
    AI Forecasts for Demand Prediction
    Used for preparation order generation
    """
    id_prevision = models.CharField(max_length=30, primary_key=True)
    id_produit = models.ForeignKey(Produit, on_delete=models.CASCADE, related_name='previsions_ia')
    date_prevision = models.DateField()
    quantite_prevue = models.DecimalField(max_digits=12, decimal_places=2)
    confiance_score = models.FloatField()  # 0.0-1.0 confidence
    cree_le = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'previsions_ia'
        ordering = ['-date_prevision']

    def __str__(self):
        return f"{self.id_prevision} - {self.id_produit}"


class AssignmentStockageIA(models.Model):
    """
    AI-Generated Storage Location Assignments
    Used for optimal picking path optimization
    """
    id_assignment = models.CharField(max_length=30, primary_key=True)
    id_commande = models.ForeignKey(Commande, on_delete=models.CASCADE, related_name='assignments_ia')
    id_produit = models.ForeignKey(Produit, on_delete=models.SET_NULL, null=True, related_name='assignments_ia')
    id_emplacement_assigne = models.ForeignKey(Emplacement, on_delete=models.SET_NULL, null=True, related_name='assignments_ia')
    version_algorithme = models.CharField(max_length=50)
    cree_le = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'assignments_stockage_ia'

    def __str__(self):
        return f"{self.id_assignment}"


class RoutePickingIA(models.Model):
    """
    AI-Generated Picking Routes
    Optimized picking path for efficiency
    """
    id_route = models.CharField(max_length=30, primary_key=True)
    id_commande = models.ForeignKey(Commande, on_delete=models.CASCADE, related_name='routes_picking_ia')
    donnees_route = models.JSONField()  # Route coordinates and sequence
    distance_totale = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    temps_estime = models.IntegerField(null=True, blank=True)  # In seconds
    cree_le = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'routes_picking_ia'

    def __str__(self):
        return f"{self.id_route}"


# ============================================================================
# SECTION 7: USER OVERRIDES & AUDIT (FR-7, FR-8, FR-44, FR-45, FR-46)
# ============================================================================

class Override(models.Model):
    """
    AI Override Records
    FR-7, FR-8, FR-44, FR-45, FR-46, FR-47
    User overrides of AI-generated recommendations
    Must log justification (FR-47: Immutable audit)
    """
    TYPE_CHOICES = [
        ('PREPARATION_ORDER', 'Preparation Order Override'),
        ('PICKING_ORDER', 'Picking Order Override'),
        ('STORAGE_ASSIGNMENT', 'Storage Assignment Override'),
        ('ROUTE', 'Route Override'),
    ]

    id_override = models.CharField(max_length=30, primary_key=True)
    type_entite = models.CharField(max_length=50, choices=TYPE_CHOICES)
    id_entite = models.CharField(max_length=100)
    id_commande = models.ForeignKey(Commande, on_delete=models.SET_NULL, null=True, blank=True, related_name='overrides')
    justification = models.TextField()  # Required - why user is overriding
    override_par = models.ForeignKey(Utilisateur, on_delete=models.CASCADE, related_name='overrides')
    cree_le = models.DateTimeField(auto_now_add=True)
    ancienne_valeur = models.JSONField(null=True, blank=True)  # What AI recommended
    nouvelle_valeur = models.JSONField(null=True, blank=True)  # What user chose

    class Meta:
        db_table = 'overrides'
        ordering = ['-cree_le']

    def __str__(self):
        return f"{self.id_override} - {self.type_entite}"


class JournalAudit(models.Model):
    """
    Immutable Audit Log
    FR-9, FR-47, NFR-6, NFR-10
    All actions logged, cannot be modified/deleted
    """
    TYPES_ACTION = [
        ('CREATE', 'Create'),
        ('READ', 'Read'),
        ('UPDATE', 'Update'),
        ('DELETE', 'Delete'),
        ('OVERRIDE', 'Override'),
        ('LOGIN', 'Login'),
        ('LOGOUT', 'Logout'),
        ('EXPORT', 'Export'),
        ('IMPORT', 'Import'),
        ('SYNC', 'Sync'),
    ]

    id_audit = models.CharField(max_length=30, primary_key=True)
    id_entrepot = models.ForeignKey(Entrepot, on_delete=models.CASCADE, null=True, blank=True, related_name='journaux_audit')
    type_action = models.CharField(max_length=50, choices=TYPES_ACTION)
    type_entite = models.CharField(max_length=100)
    id_entite = models.CharField(max_length=100, null=True, blank=True)
    execute_par = models.ForeignKey(Utilisateur, on_delete=models.SET_NULL, null=True, related_name='actions_audit')
    ancienne_valeur = models.JSONField(null=True, blank=True)
    nouvelle_valeur = models.JSONField(null=True, blank=True)
    description = models.TextField(null=True, blank=True)
    adresse_ip = models.CharField(max_length=45, null=True, blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'journal_audit'
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['execute_par', 'timestamp']),
            models.Index(fields=['type_entite', 'timestamp']),
        ]

    def __str__(self):
        return f"{self.id_audit} - {self.type_action}"


# ============================================================================
# SECTION 8: OFFLINE & SYNC (FR-70, FR-71, NFR-1 → NFR-9)
# ============================================================================

class OperationOffline(models.Model):
    """
    Offline Operations Queue
    FR-70, FR-71
    Manages offline/online sync with conflict resolution
    NFR-2: Stock consistency, NFR-9: No data loss
    """
    STATUT_CHOICES = [
        ('PENDING', 'Pending'),
        ('SYNCED', 'Synced'),
        ('FAILED', 'Failed'),
        ('RESOLVED', 'Resolved'),
    ]

    id_operation = models.CharField(max_length=30, primary_key=True)
    id_utilisateur = models.ForeignKey(Utilisateur, on_delete=models.SET_NULL, null=True, related_name='operations_offline')
    type_operation = models.CharField(max_length=100)
    donnees_operation = models.JSONField()
    statut = models.CharField(max_length=50, choices=STATUT_CHOICES, default='PENDING')
    timestamp_local = models.DateTimeField()
    timestamp_sync = models.DateTimeField(null=True, blank=True)
    erreur_sync = models.TextField(null=True, blank=True)
    tentatives_sync = models.IntegerField(default=0)

    class Meta:
        db_table = 'operations_offline'
        ordering = ['-timestamp_local']

    def __str__(self):
        return f"{self.id_operation} - {self.statut}"


class AnomalieDetection(models.Model):
    """
    Anomaly Detection Records
    Detects unusual patterns and stock discrepancies
    """
    TYPES_ANOMALIE = [
        ('STOCK_NEGATIVE', 'Negative Stock Detected'),
        ('STOCK_EXCESSIF', 'Excessive Stock'),
        ('DISCREPANCY', 'Stock Discrepancy'),
        ('MOUVEMENT_SUSPECT', 'Suspicious Movement'),
        ('ACCES_NON_AUTORISE', 'Unauthorized Access'),
    ]

    SEVERITES = [
        ('CRITICAL', 'Critical'),
        ('HIGH', 'High'),
        ('MEDIUM', 'Medium'),
        ('LOW', 'Low'),
    ]

    id_anomalie = models.CharField(max_length=30, primary_key=True)
    type_anomalie = models.CharField(max_length=50, choices=TYPES_ANOMALIE)
    severite = models.CharField(max_length=50, choices=SEVERITES)
    description = models.TextField()
    id_entite_concernee = models.CharField(max_length=100, null=True, blank=True)
    type_entite = models.CharField(max_length=100, null=True, blank=True)
    detectee_le = models.DateTimeField(auto_now_add=True)
    resolue_le = models.DateTimeField(null=True, blank=True)
    statut = models.CharField(max_length=50, default='OPEN', choices=[('OPEN', 'Open'), ('INVESTIGATING', 'Investigating'), ('RESOLVED', 'Resolved')])
    note_resolution = models.TextField(null=True, blank=True)

    class Meta:
        db_table = 'anomalies_detection'
        ordering = ['-detectee_le']
        indexes = [
            models.Index(fields=['severite', 'statut']),
        ]

    def __str__(self):
        return f"{self.id_anomalie} - {self.type_anomalie}"


# ============================================================================
# SIGNALS (Automation)
# ============================================================================

@receiver(post_save, sender=MouvementStock)
def update_vrack_on_movement(sender, instance, created, **kwargs):
    """
    Automatically adjust Vrack quantity based on Stock Movements.
    If source is V-RACK, decrease. If destination is V-RACK, increase.
    """
    if not created:
        return

    # Check source
    if instance.id_emplacement_source and instance.id_emplacement_source.code_emplacement.startswith('V-RACK-'):
        warehouse = instance.id_emplacement_source.id_entrepot
        product = instance.id_produit
        if product:
            vrack, _ = Vrack.objects.get_or_create(
                id_entrepot=warehouse,
                id_produit=product
            )
            vrack.quantite -= instance.quantite
            vrack.save()

    # Check destination
    if instance.id_emplacement_destination and instance.id_emplacement_destination.code_emplacement.startswith('V-RACK-'):
        warehouse = instance.id_emplacement_destination.id_entrepot
        product = instance.id_produit
        if product:
            vrack, _ = Vrack.objects.get_or_create(
                id_entrepot=warehouse,
                id_produit=product
            )
            vrack.quantite += instance.quantite
            vrack.save()


@receiver(post_save, sender=NiveauStockage)
def create_chariot_for_stock_floor(sender, instance, created, **kwargs):
    """
    FR-30: Automatically create a chariot for each new stocking floor.
    """
    if created:
        Chariot.objects.create(
            id_entrepot=instance.id_entrepot,
            code_chariot=f"CH-STK-{instance.id_niveau}",
            statut='AVAILABLE',
            capacite=500.00  # Default capacity for stock floor chariot
        )


@receiver(post_save, sender=NiveauPicking)
def create_chariot_for_picking_floor(sender, instance, created, **kwargs):
    """
    FR-30: Automatically create a chariot for each new picking floor.
    """
    if created:
        Chariot.objects.create(
            id_entrepot=instance.id_entrepot,
            code_chariot=f"CH-PCK-{instance.id_niveau_picking}",
            statut='AVAILABLE',
            capacite=200.00  # Default capacity for picking floor chariot
        )

