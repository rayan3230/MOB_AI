from rest_framework import serializers
from .models import Transaction, LigneTransaction
from Produit.serializers import ProduitSerializer
from Users.serializers import UtilisateurSerializer
from warhouse.serializers import EmplacementSerializer


class TransactionSerializer(serializers.ModelSerializer):
    cree_par_id_utilisateur = UtilisateurSerializer(read_only=True)
    cree_par_id_utilisateur_id = serializers.PrimaryKeyRelatedField(
        queryset=None,  # Will be set in __init__
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

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        from Users.models import Utilisateur
        self.fields['cree_par_id_utilisateur_id'].child_relation.queryset = Utilisateur.objects.all()

    def get_lignes(self, obj):
        lignes = obj.lignes.all()
        return LigneTransactionSerializer(lignes, many=True).data


class LigneTransactionSerializer(serializers.ModelSerializer):
    id_transaction = TransactionSerializer(read_only=True)
    id_transaction_id = serializers.PrimaryKeyRelatedField(
        queryset=Transaction.objects.all(),
        source='id_transaction',
        write_only=True
    )
    id_produit = ProduitSerializer(read_only=True)
    id_produit_id = serializers.PrimaryKeyRelatedField(
        queryset=None,  # Will be set in __init__
        source='id_produit',
        write_only=True,
        required=False
    )
    id_emplacement_source = EmplacementSerializer(read_only=True)
    id_emplacement_source_id = serializers.PrimaryKeyRelatedField(
        queryset=None,  # Will be set in __init__
        source='id_emplacement_source',
        write_only=True,
        required=False
    )
    id_emplacement_destination = EmplacementSerializer(read_only=True)
    id_emplacement_destination_id = serializers.PrimaryKeyRelatedField(
        queryset=None,  # Will be set in __init__
        source='id_emplacement_destination',
        write_only=True,
        required=False
    )

    class Meta:
        model = LigneTransaction
        fields = [
            'id_transaction', 'id_transaction_id', 'no_ligne', 'id_produit',
            'id_produit_id', 'quantite', 'id_emplacement_source',
            'id_emplacement_source_id', 'id_emplacement_destination',
            'id_emplacement_destination_id', 'lot_serie', 'code_motif'
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        from Produit.models import Produit
        from warhouse.models import Emplacement
        self.fields['id_produit_id'].child_relation.queryset = Produit.objects.all()
        self.fields['id_emplacement_source_id'].child_relation.queryset = Emplacement.objects.all()
        self.fields['id_emplacement_destination_id'].child_relation.queryset = Emplacement.objects.all()
