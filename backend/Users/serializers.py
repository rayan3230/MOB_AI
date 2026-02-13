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
        
        if username and password:
            try:
                user = Utilisateur.objects.get(id_utilisateur=username, actif=True)
                if not user.check_password(password):
                    raise serializers.ValidationError("Invalid username or password")
            except Utilisateur.DoesNotExist:
                raise serializers.ValidationError("Invalid username or password")
        else:
            raise serializers.ValidationError("Must include 'username' and 'password'")
            
        data['user'] = user
        return data

