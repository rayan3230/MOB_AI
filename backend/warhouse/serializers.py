from rest_framework import serializers
from .models import Entrepot, Emplacement, CommandeAchat
from Produit.serializers import ProduitSerializer


class EntrepotSerializer(serializers.ModelSerializer):
    class Meta:
        model = Entrepot
        fields = ['id_entrepot', 'code_entrepot', 'nom_entrepot', 'ville', 'actif']


class EmplacementSerializer(serializers.ModelSerializer):
    id_entrepot = EntrepotSerializer(read_only=True)
    id_entrepot_id = serializers.PrimaryKeyRelatedField(
        queryset=Entrepot.objects.all(),
        source='id_entrepot',
        write_only=True
    )

    class Meta:
        model = Emplacement
        fields = ['id_emplacement', 'code_emplacement', 'id_entrepot', 'id_entrepot_id', 'zone', 'type_emplacement', 'actif', ]


class CommandeAchatSerializer(serializers.ModelSerializer):
    id_produit = ProduitSerializer(read_only=True)
    id_produit_id = serializers.PrimaryKeyRelatedField(
        queryset=None,  # Will be set in __init__
        source='id_produit',
        write_only=True
    )

    class Meta:
        model = CommandeAchat
        fields = ['id_commande_achat', 'id_produit', 'id_produit_id', 'quantite_commandee', 'date_reception_prevue', 'statut']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        from Produit.models import Produit
        self.fields['id_produit_id'].child_relation.queryset = Produit.objects.all()
