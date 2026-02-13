import os
import django
from django.db import connection

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')
django.setup()

from Users.models import Utilisateur
from django.contrib.auth.hashers import make_password

# Since Utilisateur is not a standard Django AbstractUser (based on previous edits),
# we need to ensure it handles passwords if used for authentication, 
# or use the Nom Complet/ID as requested.

# Utilisateur model details:
# id_utilisateur (PK), password, nom_complet, role, email, telephone, adresse, actif, is_banned

username = "ADMIN001" # Matches the Uxxxx or similar pattern if desired, but CharField(10) allows this
password = "testpassword"
user_id = "ADMIN001"
full_name = "Admin User"
role = "ADMIN"

def create_test_user():
    user, created = Utilisateur.objects.update_or_create(
        id_utilisateur=user_id,
        defaults={
            'nom_complet': full_name,
            'role': role,
            'email': 'admin@example.com',
            'actif': True,
            'is_banned': False
        }
    )
    user.set_password(password)
    user.save()
    
    if created:
        print(f"User {user_id} created successfully.")
    else:
        print(f"User {user_id} updated successfully.")
    
    print(f"Credentials: ID={user_id}, Password={password}, Role={role}")

if __name__ == "__main__":
    create_test_user()
