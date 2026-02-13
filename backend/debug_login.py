import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')
django.setup()

from Users.models import Utilisateur

def verify_user(identifier, password):
    print(f"\nTesting login for identifier: '{identifier}'")
    try:
        user = Utilisateur.objects.filter(nom_complet=identifier).first()
        if not user:
            user = Utilisateur.objects.filter(id_utilisateur=identifier).first()
            
        if user:
            print(f"User found: ID={user.id_utilisateur}, Name={user.nom_complet}")
            is_correct = user.check_password(password)
            print(f"Password '{password}' matches? {is_correct}")
        else:
            print(f"User '{identifier}' not found in database.")
    except Exception as e:
        print(f"Error during verification: {e}")

if __name__ == "__main__":
    verify_user('ADMIN001', 'testpassword')
    verify_user('Admin User', 'testpassword')
