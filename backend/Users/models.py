from django.db import models
from django.contrib.auth.hashers import make_password, check_password as django_check_password

class Utilisateur(models.Model):
    ROLE_CHOICES = [
        ('EMPLOYEE', 'Employee'),
        ('SUPERVISOR', 'Supervisor'),
        ('ADMIN', 'Administrator'),
    ]
    
    id_utilisateur = models.CharField(max_length=10, primary_key=True)
    password = models.CharField(max_length=128)
    nom_complet = models.CharField(max_length=255)
    role = models.CharField(max_length=50, choices=ROLE_CHOICES)
    email = models.EmailField(null=True, blank=True)
    telephone = models.CharField(max_length=20, null=True, blank=True)
    adresse = models.TextField(null=True, blank=True)
    actif = models.BooleanField(default=True)
    is_banned = models.BooleanField(default=False)

    def set_password(self, raw_password):
        self.password = make_password(raw_password)

    def check_password(self, raw_password):
        return django_check_password(raw_password, self.password)

    def save(self, *args, **kwargs):
        if not self.id_utilisateur:
            last_user = Utilisateur.objects.all().order_by('id_utilisateur').last()
            if not last_user:
                new_id = "U0001"
            else:
                last_id = last_user.id_utilisateur
                # Check if it matches our pattern Uxxxx
                try:
                    if last_id.startswith('U') and last_id[1:].isdigit():
                        number = int(last_id[1:]) + 1
                        new_id = f"U{number:04d}"
                    else:
                        # If the last ID doesn't follow the pattern, find the highest numeric one or just count
                        import re
                        all_ids = Utilisateur.objects.values_list('id_utilisateur', flat=True)
                        numeric_ids = []
                        for uid in all_ids:
                            match = re.search(r'\d+', uid)
                            if match:
                                numeric_ids.append(int(match.group()))
                        
                        next_num = (max(numeric_ids) if numeric_ids else 0) + 1
                        new_id = f"U{next_num:04d}"
                except:
                    new_id = "U0001"
            self.id_utilisateur = new_id
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.id_utilisateur} - {self.nom_complet}"

    class Meta:
        db_table = 'utilisateurs'
