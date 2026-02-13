from rest_framework import serializers
from django.contrib.auth import authenticate

from Users.models import Utilisateur

class UserLoginSerializer(serializers.Serializer):
    """Serializer for user login"""
    username = serializers.CharField()
    password = serializers.CharField(write_only=True)
    
    def validate(self, data):
        username = data.get('username')
        password = data.get('password')
        
        print(f"Validating login for: {username}")
        if username and password:
            try:
                user = Utilisateur.objects.get(id_utilisateur=username, actif=True)
                print(f"User found: {user.id_utilisateur}, checking password...")
                print(f"Provided password: '{password}'")
                print(f"Stored hash: '{user.password}'")
                if not user.check_password(password):
                    print("Password check failed")
                    raise serializers.ValidationError("Invalid username or password")
                print("Password check passed")
            except Utilisateur.DoesNotExist:
                print(f"User {username} not found")
                raise serializers.ValidationError("Invalid username or password")
        else:
            raise serializers.ValidationError("Must include 'username' and 'password'")
            
        data['user'] = user
        return data

