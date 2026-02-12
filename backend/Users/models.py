from django.db import models






class Utilisateur(models.Model):
    ROLE_CHOICES = [
        ('OPERATOR', 'Operator'),
        ('MANAGER', 'Manager'),
        ('ADMIN', 'Administrator'),
        ('VIEWER', 'Viewer'),
    ]
    
    id_utilisateur = models.CharField(max_length=10, primary_key=True)
    nom_complet = models.CharField(max_length=255)
    role = models.CharField(max_length=50, choices=ROLE_CHOICES)
    email = models.EmailField(null=True, blank=True)
    actif = models.BooleanField(default=True)
    

    def __str__(self):
        return f"{self.id_utilisateur} - {self.nom_complet}"

    class Meta:
        db_table = 'utilisateurs'
