from django.db import models
from Users.models import Utilisateur
from Produit.models import Produit
from warhouse.models import Emplacement


class Transaction(models.Model):
    STATUT_CHOICES = [
        ('PENDING', 'Pending'),
        ('CONFIRMED', 'Confirmed'),
        ('COMPLETED', 'Completed'),
        ('CANCELLED', 'Cancelled'),
    ]
    
    TYPE_CHOICES = [
        ('RECEIPT', 'Receipt'),
        ('TRANSFER', 'Transfer'),
        ('ISSUE', 'Issue'),
        ('ADJUSTMENT', 'Adjustment'),
    ]
    
    id_transaction = models.CharField(max_length=20, primary_key=True)
    type_transaction = models.CharField(max_length=50, choices=TYPE_CHOICES)
    reference_transaction = models.CharField(max_length=100)
    cree_le = models.DateTimeField()
    cree_par_id_utilisateur = models.ForeignKey(Utilisateur, on_delete=models.SET_NULL, null=True, related_name='transactions', db_column='cree_par_id_utilisateur')
    statut = models.CharField(max_length=50, choices=STATUT_CHOICES)
    notes = models.TextField(null=True, blank=True)
    

    def __str__(self):
        return f"{self.id_transaction} - {self.type_transaction}"

    class Meta:
        db_table = 'transactions'


class LigneTransaction(models.Model):
    id_transaction = models.ForeignKey(Transaction, on_delete=models.CASCADE, related_name='lignes', db_column='id_transaction')
    no_ligne = models.IntegerField()
    id_produit = models.ForeignKey(Produit, on_delete=models.SET_NULL, null=True, related_name='lignes_transactions', db_column='id_produit')
    quantite = models.DecimalField(max_digits=12, decimal_places=2)
    id_emplacement_source = models.ForeignKey(
        Emplacement, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        related_name='lignes_source',
        db_column='id_emplacement_source'
    )
    id_emplacement_destination = models.ForeignKey(
        Emplacement, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        related_name='lignes_destination',
        db_column='id_emplacement_destination'
    )
    lot_serie = models.CharField(max_length=100, null=True, blank=True)
    code_motif = models.CharField(max_length=50, null=True, blank=True)
    

    def __str__(self):
        return f"{self.id_transaction} - Line {self.no_ligne}"

    class Meta:
        db_table = 'lignes_transaction'
        unique_together = ('id_transaction', 'no_ligne')