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

username = "testuser"
password = "testpassword"
user_id = "testuser"
full_name = "Test User"
role = "ADMIN"

# Check if model has password field. Based on attachment, it doesn't.
# If the user wants to login, they might need a password field or standard Django auth.
# However, the user mentioned 'password' in request.

def create_test_user():
    user, created = Utilisateur.objects.get_or_create(
        id_utilisateur=user_id,
        defaults={
            'nom_complet': full_name,
            'role': role,
            'email': 'test@example.com',
            'actif': True
        }
    )
    user.set_password(password)
    user.nom_complet = full_name
    user.role = role
    user.save()
    print(f"User {username} ({user_id}) created/updated with hashed password and role {role}")

if __name__ == "__main__":
    create_test_user()
