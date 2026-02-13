from rest_framework import serializers
from .models import Produit, CodeBarresProduit, HistoriqueDemande, DelaisApprovisionnement, PolitiqueReapprovisionnement, cmd_achat_ouvertes_opt


class ProduitSerializer(serializers.ModelSerializer):
    class Meta:
        model = Produit
        fields = [
            'id_produit', 'sku', 'nom_produit', 'unite_mesure', 
            'categorie', 'collisage_palette', 'collisage_fardeau', 
            'poids', 'actif'
        ]


class CodeBarresProduitSerializer(serializers.ModelSerializer):
    id_produit = ProduitSerializer(read_only=True)
    id_produit_id = serializers.PrimaryKeyRelatedField(
        queryset=Produit.objects.all(),
        source='id_produit',
        write_only=True
    )

    class Meta:
        model = CodeBarresProduit
        fields = ['code_barres', 'id_produit', 'id_produit_id', 'type_code_barres', 'principal']


class HistoriqueDemandeSerializer(serializers.ModelSerializer):
    id_produit = ProduitSerializer(read_only=True)
    id_produit_id = serializers.PrimaryKeyRelatedField(
        queryset=Produit.objects.all(),
        source='id_produit',
        write_only=True
    )

    class Meta:
        model = HistoriqueDemande
        fields = ['id', 'date', 'id_produit', 'id_produit_id', 'quantite_demande']


class DelaisApprovisionnementSerializer(serializers.ModelSerializer):
    id_produit = ProduitSerializer(read_only=True)
    id_produit_id = serializers.PrimaryKeyRelatedField(
        queryset=Produit.objects.all(),
        source='id_produit',
        write_only=True
    )

    class Meta:
        model = DelaisApprovisionnement
        fields = ['id_produit', 'id_produit_id', 'delai_jours']


class PolitiqueReapprovisionnementSerializer(serializers.ModelSerializer):
    id_produit = ProduitSerializer(read_only=True)
    id_produit_id = serializers.PrimaryKeyRelatedField(
        queryset=Produit.objects.all(),
        source='id_produit',
        write_only=True
    )

    class Meta:
        model = PolitiqueReapprovisionnement
        fields = ['id_produit', 'id_produit_id', 'stock_securite', 'quantite_min_commande', 'taille_lot']


class CmdAchatSerializer(serializers.ModelSerializer):
    id_produit = ProduitSerializer(read_only=True)
    id_produit_id = serializers.PrimaryKeyRelatedField(
        queryset=Produit.objects.all(),
        source='id_produit',
        write_only=True
    )

    class Meta:
        model = cmd_achat_ouvertes_opt
        fields = ['id_commande_achat', 'id_produit', 'id_produit_id', 'quantite_commandee', 'date_reception_prevue', 'statut']
