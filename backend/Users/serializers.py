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
                # Try to find user by nom_complet first as requested, then by id_utilisateur
                user = Utilisateur.objects.filter(nom_complet=username).first()
                if not user:
                    user = Utilisateur.objects.filter(id_utilisateur=username).first()
                
                if not user:
                    print(f"User {username} not found")
                    raise serializers.ValidationError("Invalid username or password")

                if user.is_banned:
                    print(f"User {username} is banned")
                    raise serializers.ValidationError({"banned": "Your account has been banned. Please contact the administrator."})
                
                print(f"User found: {user.id_utilisateur} ({user.nom_complet}), checking password...")
                if not user.check_password(password):
                    print("Password check failed")
                    raise serializers.ValidationError("Invalid username or password")
                print("Password check passed")
            except Exception as e:
                print(f"Login error: {str(e)}")
                if isinstance(e, serializers.ValidationError):
                    raise e
                raise serializers.ValidationError("An error occurred during login")
        else:
            raise serializers.ValidationError("Must include 'username' and 'password'")
            
        data['user'] = user
        return data

class UtilisateurSerializer(serializers.ModelSerializer):
    class Meta:
        model = Utilisateur
        fields = ['id_utilisateur', 'nom_complet', 'role', 'email', 'telephone', 'adresse', 'actif', 'is_banned', 'password']
        extra_kwargs = {
            'password': {'write_only': True, 'required': False},
            'id_utilisateur': {'required': False}
        }

    def create(self, validated_data):
        password = validated_data.pop('password', None)
        user = Utilisateur(**validated_data)
        if password:
            user.set_password(password)
        else:
            # Default password if not provided? Maybe better to require it.
            user.set_password("123456") 
        user.save()
        return user

    def update(self, instance, validated_data):
        password = validated_data.pop('password', None)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        if password:
            instance.set_password(password)
        instance.save()
        return instance

