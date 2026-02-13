from django.db import models


class Produit(models.Model):
    id_produit = models.CharField(max_length=10, primary_key=True, blank=True)
    sku = models.CharField(max_length=50, unique=True)
    nom_produit = models.CharField(max_length=255)
    unite_mesure = models.CharField(max_length=50)
    categorie = models.CharField(max_length=100)
    collisage_palette = models.IntegerField(default=0)
    collisage_fardeau = models.IntegerField(default=0)
    poids = models.DecimalField(max_digits=10, decimal_places=3, default=0.0)
    actif = models.BooleanField(default=True)
    
    def save(self, *args, **kwargs):
        if not self.id_produit:
            last_produit = Produit.objects.all().order_by('id_produit').last()
            if not last_produit:
                self.id_produit = 'P0001'
            else:
                last_id = last_produit.id_produit
                if last_id.startswith('P'):
                    try:
                        num = int(last_id[1:]) + 1
                        self.id_produit = f"P{num:04d}"
                    except ValueError:
                        self.id_produit = 'P0001'
                else:
                    self.id_produit = 'P0001'
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.id_produit} - {self.nom_produit}"

    class Meta:
        db_table = 'produit'


class CodeBarresProduit(models.Model):
    code_barres = models.CharField(max_length=50, primary_key=True)
    id_produit = models.ForeignKey(Produit, on_delete=models.CASCADE, related_name='codes_barres')
    type_code_barres = models.CharField(max_length=50)
    principal = models.BooleanField(default=False)
    
   

    def __str__(self):
        return f"{self.code_barres} - {self.id_produit}"

    class Meta:
        db_table = 'codes_barres_produits'


class HistoriqueDemande(models.Model):
    
    date = models.DateField()
    id_produit = models.ForeignKey(Produit, on_delete=models.CASCADE, related_name='historique_demandes')
    quantite_demande = models.DecimalField(max_digits=12, decimal_places=2)
    
    def __str__(self):
        return f"{self.id_produit} - {self.date} - qty: {self.quantite_demande}"

    class Meta:
        db_table = 'historique_demande'


class DelaisApprovisionnement(models.Model):
    id_produit = models.OneToOneField(Produit, on_delete=models.CASCADE, related_name='delai_approvisionnement')
    delai_jours = models.IntegerField()
    
    def __str__(self):
        return f"{self.id_produit} - {self.delai_jours} days"

    class Meta:
        db_table = 'delais_approvisionnement'


class PolitiqueReapprovisionnement(models.Model):
    id_produit = models.OneToOneField(Produit, on_delete=models.CASCADE, related_name='politique_reapprovisionnement')
    stock_securite = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    quantite_min_commande = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    taille_lot = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    
    def __str__(self):
        return f"Policy for {self.id_produit}"

    class Meta:
        db_table = 'politique_reapprovisionnement'




class cmd_achat_ouvertes_opt(models.Model):
    STATUT_CHOICES = [
        ('OPEN', 'Open'),
        ('PARTIALLY_RECEIVED', 'Partially Received'),
        ('COMPLETED', 'Completed'),
        ('CANCELLED', 'Cancelled'),
    ]
    
    id_commande_achat = models.CharField(max_length=20, primary_key=True)
    id_produit = models.ForeignKey(Produit, on_delete=models.CASCADE, related_name='commandes_achat')
    quantite_commandee = models.DecimalField(max_digits=12, decimal_places=2)
    date_reception_prevue = models.DateField()
    statut = models.CharField(max_length=50, choices=STATUT_CHOICES)
    


    def __str__(self):
        return f"{self.id_commande_achat} - {self.id_produit}"

    class Meta:
        db_table = 'cmd_achat_ouvertes_opt'


