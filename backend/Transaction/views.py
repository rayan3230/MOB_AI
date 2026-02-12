from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import Transaction, LigneTransaction
from .serializers import (
    TransactionListSerializer,
    TransactionDetailSerializer,
    TransactionCreateUpdateSerializer,
    LigneTransactionDetailSerializer,
    LigneTransactionSimpleSerializer
)


class TransactionViewSet(viewsets.ModelViewSet):
    """
    ViewSet for Transaction model
    - GET /transactions/ - List all transactions (with nested user data)
    - GET /transactions/{id}/ - Detail view (with all nested data and line items)
    - POST /transactions/ - Create new transaction
    - PUT /transactions/{id}/ - Update transaction
    - DELETE /transactions/{id}/ - Delete transaction
    """
    queryset = Transaction.objects.all()
    lookup_field = 'id_transaction'
    
    def get_serializer_class(self):
        """Use different serializers based on action"""
        if self.action == 'retrieve':
            return TransactionDetailSerializer
        elif self.action == 'list':
            return TransactionListSerializer
        elif self.action in ['create', 'update', 'partial_update']:
            return TransactionCreateUpdateSerializer
        return TransactionDetailSerializer
    
    @action(detail=True, methods=['get'])
    def lignes(self, request, id_transaction=None):
        """
        GET /transactions/{id}/lignes/
        Returns all line items for a transaction with nested foreign key data
        """
        transaction = self.get_object()
        lignes = transaction.lignes.all()
        serializer = LigneTransactionDetailSerializer(lignes, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'])
    def utilisateur_details(self, request, id_transaction=None):
        """
        GET /transactions/{id}/utilisateur_details/
        Returns details of the user who created this transaction
        """
        transaction = self.get_object()
        if transaction.cree_par_id_utilisateur:
            return Response({
                'id_utilisateur': transaction.cree_par_id_utilisateur.id_utilisateur,
                'nom_complet': transaction.cree_par_id_utilisateur.nom_complet,
                'role': transaction.cree_par_id_utilisateur.role,
                'email': transaction.cree_par_id_utilisateur.email,
                'actif': transaction.cree_par_id_utilisateur.actif,
            })
        return Response({'message': 'No user associated with this transaction'}, status=status.HTTP_404_NOT_FOUND)


class LigneTransactionViewSet(viewsets.ModelViewSet):
    """
    ViewSet for LigneTransaction model
    - GET /lignes_transactions/ - List all line items (with nested product and location data)
    - GET /lignes_transactions/{id}/ - Detail view (with all nested data)
    - POST /lignes_transactions/ - Create new line item
    - PUT /lignes_transactions/{id}/ - Update line item
    - DELETE /lignes_transactions/{id}/ - Delete line item
    """
    queryset = LigneTransaction.objects.all()
    
    def get_serializer_class(self):
        """Use different serializers based on action"""
        if self.action in ['create', 'update', 'partial_update']:
            return LigneTransactionSimpleSerializer
        return LigneTransactionDetailSerializer
    
    @action(detail=True, methods=['get'])
    def produit_details(self, request, pk=None):
        """
        GET /lignes_transactions/{id}/produit_details/
        Returns details of the product in this line item
        """
        ligne = self.get_object()
        if ligne.id_produit:
            return Response({
                'id_produit': ligne.id_produit.id_produit,
                'sku': ligne.id_produit.sku,
                'nom_produit': ligne.id_produit.nom_produit,
                'unite_mesure': ligne.id_produit.unite_mesure,
                'categorie': ligne.id_produit.categorie,
            })
        return Response({'message': 'No product associated with this line'}, status=status.HTTP_404_NOT_FOUND)
    
    @action(detail=True, methods=['get'])
    def emplacement_details(self, request, pk=None):
        """
        GET /lignes_transactions/{id}/emplacement_details/
        Returns details of both source and destination locations
        """
        ligne = self.get_object()
        data = {}
        
        if ligne.id_emplacement_source:
            data['source'] = {
                'id_emplacement': ligne.id_emplacement_source.id_emplacement,
                'code_emplacement': ligne.id_emplacement_source.code_emplacement,
                'zone': ligne.id_emplacement_source.zone,
                'type_emplacement': ligne.id_emplacement_source.type_emplacement,
            }
        
        if ligne.id_emplacement_destination:
            data['destination'] = {
                'id_emplacement': ligne.id_emplacement_destination.id_emplacement,
                'code_emplacement': ligne.id_emplacement_destination.code_emplacement,
                'zone': ligne.id_emplacement_destination.zone,
                'type_emplacement': ligne.id_emplacement_destination.type_emplacement,
            }
        
        if not data:
            return Response({'message': 'No emplacements associated with this line'}, status=status.HTTP_404_NOT_FOUND)
        
        return Response(data)
