import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')
django.setup()

from Users.models import Utilisateur
from django.contrib.auth.hashers import check_password

try:
    user = Utilisateur.objects.get(id_utilisateur='testuser')
    print(f"User found: {user.id_utilisateur}")
    print(f"Stored Hash: {user.password}")
    is_correct = check_password("testpassword", user.password)
    print(f"Password 'testpassword' matches stored hash? {is_correct}")
except Utilisateur.DoesNotExist:
    print("User 'testuser' not found in database.")
except Exception as e:
    print(f"Error: {e}")
