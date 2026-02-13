from django.db import models
from django.contrib.auth.hashers import make_password, check_password

class Utilisateur(models.Model):
    ROLE_CHOICES = [
        ('OPERATOR', 'Operator'),
        ('MANAGER', 'Manager'),
        ('ADMIN', 'Administrator'),
        ('VIEWER', 'Viewer'),
    ]
    
    id_utilisateur = models.CharField(max_length=10, primary_key=True)
    password = models.CharField(max_length=128)
    nom_complet = models.CharField(max_length=255)
    role = models.CharField(max_length=50, choices=ROLE_CHOICES)
    email = models.EmailField(null=True, blank=True)
    actif = models.BooleanField(default=True)

    def set_password(self, raw_password):
        self.password = make_password(raw_password)

    def check_password(self, raw_password):
        return check_password(raw_password, self.password)

    def __str__(self):
        return f"{self.id_utilisateur} - {self.nom_complet}"

    class Meta:
        db_table = 'utilisateurs'
