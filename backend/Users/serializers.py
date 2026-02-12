from rest_framework import serializers
from django.contrib.auth import authenticate

from Users.models import CustomUser

class UserLoginSerializer(serializers.Serializer):
    """Serializer for user login"""
    username = serializers.CharField()
    password = serializers.CharField(write_only=True)
    
    def validate(self, data):
        username = data.get('username')
        password = data.get('password')
        
        if username and password:
            # Note: CustomUser uses 'username' from AbstractUser as unique identifier
            # or if the user specifically wants 'user_name' field to be the login field:
            user = authenticate(username=username, password=password)
            
            if not user:
                raise serializers.ValidationError("Invalid username or password")
        else:
            raise serializers.ValidationError("Must include 'username' and 'password'")
            
        data['user'] = user
        return data

