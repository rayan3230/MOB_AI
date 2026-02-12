from django.db import models
from Produit.models import Produit


class Entrepot(models.Model):
    id_entrepot = models.CharField(max_length=10, primary_key=True)
    code_entrepot = models.CharField(max_length=50, unique=True)
    nom_entrepot = models.CharField(max_length=255)
    ville = models.CharField(max_length=100, null=True, blank=True)
    actif = models.BooleanField(default=True)
    
    

    def __str__(self):
        return f"{self.id_entrepot} - {self.nom_entrepot}"

    class Meta:
        db_table = 'entrepots'


class Emplacement(models.Model):
    id_emplacement = models.CharField(max_length=20, primary_key=True)
    code_emplacement = models.CharField(max_length=50, unique=True)
    id_entrepot = models.ForeignKey(Entrepot, on_delete=models.CASCADE, related_name='emplacements')
    zone = models.CharField(max_length=50, null=True, blank=True)
    type_emplacement = models.CharField(max_length=50)
    actif = models.BooleanField(default=True)
    


    def __str__(self):
        return f"{self.id_emplacement} - {self.code_emplacement}"

    class Meta:
        db_table = 'emplacements'


