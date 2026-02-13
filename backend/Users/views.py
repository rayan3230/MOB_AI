from django.shortcuts import render
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.authtoken.models import Token
from rest_framework import status

from .serializers import UserLoginSerializer

@api_view(['POST'])
@permission_classes([AllowAny])
def Login(request):
    print("Login request data:", request.data)
    serializer = UserLoginSerializer(data=request.data)
    if serializer.is_valid():
        user = serializer.validated_data['user']
        # For our custom Utilisateur model, we skip Token for now unless specifically needed,
        # or we return a dummy token to keep frontend happy.
        return Response({
            'token': 'dummy-token-for-dev',
            'user': {
                'id': user.id_utilisateur,
                'user_name': user.nom_complet,
                'user_role': user.role,
                'email': user.email,
                'telephone': user.telephone,
                'adresse': user.adresse,
            }
                         
                         }, status=status.HTTP_200_OK)
    
    print("Login validation failed:", serializer.errors)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

from .models import Utilisateur

@api_view(['PUT'])
@permission_classes([AllowAny]) # In a real app use IsAuthenticated
def update_profile(request, pk):
    try:
        user = Utilisateur.objects.get(pk=pk)
    except Utilisateur.DoesNotExist:
        return Response({'error': 'User not found'}, status=status.HTTP_404_NOT_FOUND)

    data = request.data
    user.nom_complet = data.get('user_name', user.nom_complet)
    user.email = data.get('email', user.email)
    user.telephone = data.get('telephone', user.telephone)
    user.adresse = data.get('adresse', user.adresse)
    
    if 'password' in data and data['password']:
        user.set_password(data['password'])
        
    user.save()
    
    return Response({
        'message': 'Profile updated successfully',
        'user': {
            'id': user.id_utilisateur,
            'user_name': user.nom_complet,
            'user_role': user.role,
            'email': user.email,
            'telephone': user.telephone,
            'adresse': user.adresse,
        }
    })
