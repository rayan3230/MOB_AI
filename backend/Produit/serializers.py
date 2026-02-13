from rest_framework import serializers
from .models import Produit, CodeBarresProduit, HistoriqueDemande, DelaisApprovisionnement, PolitiqueReapprovisionnement, cmd_achat_ouvertes_opt


class ProduitSerializer(serializers.ModelSerializer):
    rack_placements = serializers.SerializerMethodField()

    class Meta:
        model = Produit
        fields = [
            'id_produit', 'sku', 'nom_produit', 'unite_mesure', 
            'categorie', 'collisage_palette', 'collisage_fardeau', 
            'poids', 'actif', 'id_rack', 'rack_placements'
        ]

    def get_rack_placements(self, obj):
        # We import here to avoid circular dependencies
        from warhouse.models import RackProduct
        placements = RackProduct.objects.filter(product=obj)
        return [{
            'rack_id': p.rack.id_rack,
            'rack_code': p.rack.code_rack,
            'quantity': p.quantity
        } for p in placements]


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
