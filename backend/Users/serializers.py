from rest_framework import serializers
from django.contrib.auth import authenticate

from Users.models import Utilisateur

class UserLoginSerializer(serializers.Serializer):
    """Serializer for user login"""
    email = serializers.EmailField(required=False)
    username = serializers.CharField(required=False)
    password = serializers.CharField(write_only=True)
    
    def validate(self, data):
        email = data.get('email')
        username = data.get('username')
        password = data.get('password')
        
        # Check either email or username field
        identifier = email or username
        
        print(f"Validating login for: {identifier}")
        if identifier and password:
            try:
                # Try finding by email first, then by name or ID if it wasn't an email
                user = Utilisateur.objects.filter(email=identifier).first()
                if not user:
                    user = Utilisateur.objects.filter(nom_complet=identifier).first()
                if not user:
                    user = Utilisateur.objects.filter(id_utilisateur=identifier).first()
                
                if not user:
                    print(f"User with identifier {identifier} not found")
                    raise serializers.ValidationError("Invalid credentials")

                if user.is_banned:
                    print(f"User {identifier} is banned")
                    raise serializers.ValidationError({"banned": "Your account has been banned. Please contact the administrator."})
                
                print(f"User found: {user.id_utilisateur} ({user.nom_complet}), checking password...")
                if not user.check_password(password):
                    print("Password check failed")
                    raise serializers.ValidationError("Invalid credentials")
                print("Password check passed")
            except Exception as e:
                print(f"Login error: {str(e)}")
                if isinstance(e, serializers.ValidationError):
                    raise e
                raise serializers.ValidationError("An error occurred during login")
        else:
            raise serializers.ValidationError("Must provide email/username and password")
            
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

