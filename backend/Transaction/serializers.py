from rest_framework import serializers
from .models import Transaction, LigneTransaction
from Produit.models import Produit
from Users.models import Utilisateur
from warhouse.models import Emplacement
from Produit.serializers import ProduitSerializer
from Users.serializers import UtilisateurSerializer
from warhouse.serializers import EmplacementSerializer


class TransactionListSerializer(serializers.ModelSerializer):
    cree_par_nom = serializers.CharField(source='cree_par_id_utilisateur.username', read_only=True)
    
    class Meta:
        model = Transaction
        fields = [
            'id_transaction', 'type_transaction', 'reference_transaction',
            'cree_le', 'cree_par_nom', 'statut'
        ]

class TransactionDetailSerializer(serializers.ModelSerializer):
    cree_par_id_utilisateur = UtilisateurSerializer(read_only=True)
    lignes = serializers.SerializerMethodField()

    class Meta:
        model = Transaction
        fields = [
            'id_transaction', 'type_transaction', 'reference_transaction',
            'cree_le', 'cree_par_id_utilisateur', 'statut', 'notes', 'lignes'
        ]

    def get_lignes(self, obj):
        lignes = obj.lignes.all()
        return LigneTransactionDetailSerializer(lignes, many=True).data

class TransactionCreateUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Transaction
        fields = [
            'id_transaction', 'type_transaction', 'reference_transaction',
            'cree_le', 'cree_par_id_utilisateur', 'statut', 'notes'
        ]

class LigneTransactionSimpleSerializer(serializers.ModelSerializer):
    class Meta:
        model = LigneTransaction
        fields = [
            'no_ligne', 'id_produit', 'quantite', 'lot_serie'
        ]

class LigneTransactionDetailSerializer(serializers.ModelSerializer):
    id_produit = ProduitSerializer(read_only=True)
    id_emplacement_source = EmplacementSerializer(read_only=True)
    id_emplacement_destination = EmplacementSerializer(read_only=True)

    class Meta:
        model = LigneTransaction
        fields = [
            'no_ligne', 'id_produit', 'quantite', 'id_emplacement_source',
            'id_emplacement_destination', 'lot_serie', 'code_motif'
        ]

class TransactionSerializer(serializers.ModelSerializer):
    cree_par_id_utilisateur = UtilisateurSerializer(read_only=True)
    cree_par_id_utilisateur_id = serializers.PrimaryKeyRelatedField(
        queryset=Utilisateur.objects.all(),
        source='cree_par_id_utilisateur',
        write_only=True,
        required=False
    )
    lignes = serializers.SerializerMethodField()

    class Meta:
        model = Transaction
        fields = [
            'id_transaction', 'type_transaction', 'reference_transaction',
            'cree_le', 'cree_par_id_utilisateur', 'cree_par_id_utilisateur_id',
            'statut', 'notes', 'lignes'
        ]

    def get_lignes(self, obj):
        lignes = obj.lignes.all()
        # Use detail serializer to avoid circular dependency
        return LigneTransactionDetailSerializer(lignes, many=True).data


class LigneTransactionSerializer(serializers.ModelSerializer):
    # Removed TransactionSerializer to prevent circular dependency
    id_transaction_id = serializers.CharField(source='id_transaction.id_transaction', read_only=True)
    id_produit = ProduitSerializer(read_only=True)
    id_produit_id = serializers.PrimaryKeyRelatedField(
        queryset=Produit.objects.all(),
        source='id_produit',
        write_only=True,
        required=False
    )
    id_emplacement_source = EmplacementSerializer(read_only=True)
    id_emplacement_source_id = serializers.PrimaryKeyRelatedField(
        queryset=Emplacement.objects.all(),
        source='id_emplacement_source',
        write_only=True,
        required=False
    )
    id_emplacement_destination = EmplacementSerializer(read_only=True)
    id_emplacement_destination_id = serializers.PrimaryKeyRelatedField(
        queryset=Emplacement.objects.all(),
        source='id_emplacement_destination',
        write_only=True,
        required=False
    )

    class Meta:
        model = LigneTransaction
        fields = [
            'id_transaction_id', 'no_ligne', 'id_produit',
            'id_produit_id', 'quantite', 'id_emplacement_source',
            'id_emplacement_source_id', 'id_emplacement_destination',
            'id_emplacement_destination_id', 'lot_serie', 'code_motif'
        ]
