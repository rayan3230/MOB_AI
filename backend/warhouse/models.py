from django.db import models
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

    def __str__(self):
        return f"{self.id_entrepot} - {self.nom_entrepot}"

    class Meta:
        db_table = 'entrepots'


class NiveauStockage(models.Model):
    """
    Storage Floors/Levels
    FR-13: Each warehouse has multiple floors (N1, N2, N3, N4)
    Unique per warehouse + level_code
    """
    id_niveau = models.CharField(max_length=20, primary_key=True)
    id_entrepot = models.ForeignKey(Entrepot, on_delete=models.CASCADE, related_name='niveaux_stockage')
    code_niveau = models.CharField(max_length=50)  # N1, N2, N3, N4
    description = models.CharField(max_length=255, null=True, blank=True)
    cree_le = models.DateTimeField(auto_now_add=True, null=True, blank=True)

    class Meta:
        db_table = 'niveaux_stockage'
        unique_together = [['id_entrepot', 'code_niveau']]

    def __str__(self):
        return f"{self.id_niveau} - {self.code_niveau}"


class Emplacement(models.Model):
    """
    Storage & Picking Locations
    FR-14, FR-15, FR-16, FR-17
    Represents both STORAGE and PICKING locations
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

    id_emplacement = models.CharField(max_length=20, primary_key=True)
    code_emplacement = models.CharField(max_length=50, unique=True)  # FR-17: Unique code per location
    id_entrepot = models.ForeignKey(Entrepot, on_delete=models.CASCADE, related_name='emplacements')
    id_niveau = models.ForeignKey(NiveauStockage, on_delete=models.SET_NULL, null=True, blank=True, related_name='emplacements')
    zone = models.CharField(max_length=50, null=True, blank=True)
    type_emplacement = models.CharField(max_length=50, choices=TYPE_CHOICES)  # STORAGE or PICKING
    statut = models.CharField(max_length=50, choices=STATUS_CHOICES, default='AVAILABLE')
    actif = models.BooleanField(default=True)
    cree_le = models.DateTimeField(auto_now_add=True, null=True, blank=True)
    mise_a_jour_le = models.DateTimeField(auto_now=True, null=True, blank=True)

    def __str__(self):
        return f"{self.id_emplacement} - {self.code_emplacement}"

    class Meta:
        db_table = 'emplacements'


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

    id_chariot = models.CharField(max_length=20, primary_key=True)
    code_chariot = models.CharField(max_length=50, unique=True)
    id_entrepot = models.ForeignKey(Entrepot, on_delete=models.CASCADE, related_name='chariots')
    statut = models.CharField(max_length=50, choices=STATUT_CHOICES, default='AVAILABLE')
    id_emplacement_courant = models.ForeignKey(Emplacement, on_delete=models.SET_NULL, null=True, blank=True, related_name='chariots_courants')
    capacite = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    cree_le = models.DateTimeField(auto_now_add=True)

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

