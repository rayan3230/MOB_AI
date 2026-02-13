from rest_framework import serializers
from .models import (
    Entrepot, NiveauStockage, Emplacement, Stock, MouvementStock,
    Chariot, ChariotOperation, Commande, LigneCommande, ResultatLivraison,
    Operation, PrevisionIA, AssignmentStockageIA, RoutePickingIA,
    Override, JournalAudit, OperationOffline, AnomalieDetection
)
from Produit.models import Produit
from Users.models import Utilisateur
from Produit.serializers import ProduitSerializer
from Users.serializers import UtilisateurSerializer


# ============================================================================
# WAREHOUSE STRUCTURE SERIALIZERS
# ============================================================================

class EntrepotSerializer(serializers.ModelSerializer):
    """Warehouse/Depot serializer"""
    class Meta:
        model = Entrepot
        fields = [
            'id_entrepot', 'code_entrepot', 'nom_entrepot', 'ville',
            'adresse', 'actif', 'cree_le'
        ]
        read_only_fields = ['id_entrepot', 'cree_le']


class NiveauStockageSerializer(serializers.ModelSerializer):
    """Storage Floor/Level serializer"""
    id_entrepot = EntrepotSerializer(read_only=True)
    id_entrepot_id = serializers.PrimaryKeyRelatedField(
        queryset=Entrepot.objects.all(),
        source='id_entrepot',
        write_only=True
    )

    class Meta:
        model = NiveauStockage
        fields = [
            'id_niveau', 'code_niveau', 'description',
            'id_entrepot', 'id_entrepot_id', 'cree_le'
        ]
        read_only_fields = ['cree_le']


class EmplacementSerializer(serializers.ModelSerializer):
    """Location (Storage/Picking) serializer"""
    id_entrepot = EntrepotSerializer(read_only=True)
    id_entrepot_id = serializers.PrimaryKeyRelatedField(
        queryset=Entrepot.objects.all(),
        source='id_entrepot',
        write_only=True
    )
    id_niveau = NiveauStockageSerializer(read_only=True)
    id_niveau_id = serializers.PrimaryKeyRelatedField(
        queryset=NiveauStockage.objects.all(),
        source='id_niveau',
        write_only=True,
        required=False
    )

    class Meta:
        model = Emplacement
        fields = [
            'id_emplacement', 'code_emplacement', 'zone', 'type_emplacement',
            'statut', 'actif', 'cree_le', 'mise_a_jour_le',
            'id_entrepot', 'id_entrepot_id', 'id_niveau', 'id_niveau_id'
        ]
        read_only_fields = ['cree_le', 'mise_a_jour_le']


# ============================================================================
# INVENTORY SYSTEM SERIALIZERS
# ============================================================================

class StockSerializer(serializers.ModelSerializer):
    """Current Stock snapshot serializer"""
    id_produit = ProduitSerializer(read_only=True)
    id_produit_id = serializers.PrimaryKeyRelatedField(
        queryset=Produit.objects.all(),
        source='id_produit',
        write_only=True
    )
    id_emplacement = EmplacementSerializer(read_only=True)
    id_emplacement_id = serializers.PrimaryKeyRelatedField(
        queryset=Emplacement.objects.all(),
        source='id_emplacement',
        write_only=True
    )

    class Meta:
        model = Stock
        fields = [
            'id_stock', 'quantite', 'quantite_reservee', 'lot_serie',
            'date_expiration', 'mise_a_jour_le',
            'id_produit', 'id_produit_id', 'id_emplacement', 'id_emplacement_id'
        ]
        read_only_fields = ['mise_a_jour_le']


class MouvementStockSerializer(serializers.ModelSerializer):
    """Stock Movement Ledger (IMMUTABLE) serializer"""
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
    execute_par = UtilisateurSerializer(read_only=True)
    execute_par_id = serializers.PrimaryKeyRelatedField(
        queryset=Utilisateur.objects.all(),
        source='execute_par',
        write_only=True,
        required=False
    )

    class Meta:
        model = MouvementStock
        fields = [
            'id_mouvement', 'type_mouvement', 'quantite', 'lot_serie',
            'motif_code', 'reference_transaction', 'date_execution', 'notes',
            'id_produit', 'id_produit_id',
            'id_emplacement_source', 'id_emplacement_source_id',
            'id_emplacement_destination', 'id_emplacement_destination_id',
            'execute_par', 'execute_par_id'
        ]
        read_only_fields = ['date_execution']


# ============================================================================
# CHARIOT SYSTEM SERIALIZERS
# ============================================================================

class ChariotSerializer(serializers.ModelSerializer):
    """Chariot/Trolley serializer"""
    id_entrepot = EntrepotSerializer(read_only=True)
    id_entrepot_id = serializers.PrimaryKeyRelatedField(
        queryset=Entrepot.objects.all(),
        source='id_entrepot',
        write_only=True
    )
    id_emplacement_courant = EmplacementSerializer(read_only=True)
    id_emplacement_courant_id = serializers.PrimaryKeyRelatedField(
        queryset=Emplacement.objects.all(),
        source='id_emplacement_courant',
        write_only=True,
        required=False
    )

    class Meta:
        model = Chariot
        fields = [
            'id_chariot', 'code_chariot', 'statut', 'capacite', 'cree_le',
            'id_entrepot', 'id_entrepot_id',
            'id_emplacement_courant', 'id_emplacement_courant_id'
        ]
        read_only_fields = ['cree_le']


class ChariotOperationSerializer(serializers.ModelSerializer):
    """Chariot Operation Assignment serializer"""
    id_chariot = ChariotSerializer(read_only=True)
    id_chariot_id = serializers.PrimaryKeyRelatedField(
        queryset=Chariot.objects.all(),
        source='id_chariot',
        write_only=True
    )
    id_emplacement_courant = EmplacementSerializer(read_only=True)
    id_emplacement_courant_id = serializers.PrimaryKeyRelatedField(
        queryset=Emplacement.objects.all(),
        source='id_emplacement_courant',
        write_only=True,
        required=False
    )

    class Meta:
        model = ChariotOperation
        fields = [
            'id_chariot_operation', 'date_assignation', 'date_liberation',
            'id_chariot', 'id_chariot_id',
            'id_emplacement_courant', 'id_emplacement_courant_id'
        ]
        read_only_fields = ['date_assignation']


# ============================================================================
# ORDER SYSTEM SERIALIZERS
# ============================================================================

class CommandeSerializer(serializers.ModelSerializer):
    """Order (Command, Preparation, Picking) serializer"""
    cree_par = UtilisateurSerializer(read_only=True)
    cree_par_id = serializers.PrimaryKeyRelatedField(
        queryset=Utilisateur.objects.all(),
        source='cree_par',
        write_only=True,
        required=False
    )

    class Meta:
        model = Commande
        fields = [
            'id_commande', 'type_commande', 'statut', 'reference',
            'creation_le', 'debut_le', 'fin_le',
            'cree_par', 'cree_par_id'
        ]
        read_only_fields = ['creation_le']


class LigneCommandeSerializer(serializers.ModelSerializer):
    """Order Line Item serializer"""
    id_commande = CommandeSerializer(read_only=True)
    id_commande_id = serializers.PrimaryKeyRelatedField(
        queryset=Commande.objects.all(),
        source='id_commande',
        write_only=True
    )
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
        model = LigneCommande
        fields = [
            'id_ligne', 'no_ligne', 'quantite', 'quantite_completee',
            'id_commande', 'id_commande_id',
            'id_produit', 'id_produit_id',
            'id_emplacement_source', 'id_emplacement_source_id',
            'id_emplacement_destination', 'id_emplacement_destination_id'
        ]


class ResultatLivraisonSerializer(serializers.ModelSerializer):
    """Delivery Result serializer"""
    id_commande = CommandeSerializer(read_only=True)
    id_commande_id = serializers.PrimaryKeyRelatedField(
        queryset=Commande.objects.all(),
        source='id_commande',
        write_only=True
    )
    valide_par = UtilisateurSerializer(read_only=True)
    valide_par_id = serializers.PrimaryKeyRelatedField(
        queryset=Utilisateur.objects.all(),
        source='valide_par',
        write_only=True,
        required=False
    )

    class Meta:
        model = ResultatLivraison
        fields = [
            'id_resultat', 'statut', 'date_validation', 'notes',
            'id_commande', 'id_commande_id',
            'valide_par', 'valide_par_id'
        ]
        read_only_fields = ['date_validation']


# ============================================================================
# OPERATION EXECUTION SERIALIZERS
# ============================================================================

class OperationSerializer(serializers.ModelSerializer):
    """Operation Execution serializer"""
    id_commande = CommandeSerializer(read_only=True)
    id_commande_id = serializers.PrimaryKeyRelatedField(
        queryset=Commande.objects.all(),
        source='id_commande',
        write_only=True,
        required=False
    )
    execute_par = UtilisateurSerializer(read_only=True)
    execute_par_id = serializers.PrimaryKeyRelatedField(
        queryset=Utilisateur.objects.all(),
        source='execute_par',
        write_only=True,
        required=False
    )

    class Meta:
        model = Operation
        fields = [
            'id_operation', 'type_operation', 'statut',
            'date_debut', 'date_fin',
            'id_commande', 'id_commande_id',
            'execute_par', 'execute_par_id'
        ]
        read_only_fields = ['date_debut']


# ============================================================================
# AI SYSTEM SERIALIZERS
# ============================================================================

class PrevisionIASerializer(serializers.ModelSerializer):
    """AI Forecast serializer"""
    id_produit = ProduitSerializer(read_only=True)
    id_produit_id = serializers.PrimaryKeyRelatedField(
        queryset=Produit.objects.all(),
        source='id_produit',
        write_only=True
    )

    class Meta:
        model = PrevisionIA
        fields = [
            'id_prevision', 'date_prevision', 'quantite_prevue',
            'confiance_score', 'cree_le',
            'id_produit', 'id_produit_id'
        ]
        read_only_fields = ['cree_le']


class AssignmentStockageIASerializer(serializers.ModelSerializer):
    """AI Storage Assignment serializer"""
    id_commande = CommandeSerializer(read_only=True)
    id_commande_id = serializers.PrimaryKeyRelatedField(
        queryset=Commande.objects.all(),
        source='id_commande',
        write_only=True
    )
    id_produit = ProduitSerializer(read_only=True)
    id_produit_id = serializers.PrimaryKeyRelatedField(
        queryset=Produit.objects.all(),
        source='id_produit',
        write_only=True,
        required=False
    )
    id_emplacement_assigne = EmplacementSerializer(read_only=True)
    id_emplacement_assigne_id = serializers.PrimaryKeyRelatedField(
        queryset=Emplacement.objects.all(),
        source='id_emplacement_assigne',
        write_only=True,
        required=False
    )

    class Meta:
        model = AssignmentStockageIA
        fields = [
            'id_assignment', 'version_algorithme', 'cree_le',
            'id_commande', 'id_commande_id',
            'id_produit', 'id_produit_id',
            'id_emplacement_assigne', 'id_emplacement_assigne_id'
        ]
        read_only_fields = ['cree_le']


class RoutePickingIASerializer(serializers.ModelSerializer):
    """AI Picking Route serializer"""
    id_commande = CommandeSerializer(read_only=True)
    id_commande_id = serializers.PrimaryKeyRelatedField(
        queryset=Commande.objects.all(),
        source='id_commande',
        write_only=True
    )

    class Meta:
        model = RoutePickingIA
        fields = [
            'id_route', 'donnees_route', 'distance_totale',
            'temps_estime', 'cree_le',
            'id_commande', 'id_commande_id'
        ]
        read_only_fields = ['cree_le']


# ============================================================================
# OVERRIDE & AUDIT SERIALIZERS
# ============================================================================

class OverrideSerializer(serializers.ModelSerializer):
    """AI Override serializer"""
    id_commande = CommandeSerializer(read_only=True)
    id_commande_id = serializers.PrimaryKeyRelatedField(
        queryset=Commande.objects.all(),
        source='id_commande',
        write_only=True,
        required=False
    )
    override_par = UtilisateurSerializer(read_only=True)
    override_par_id = serializers.PrimaryKeyRelatedField(
        queryset=Utilisateur.objects.all(),
        source='override_par',
        write_only=True
    )

    class Meta:
        model = Override
        fields = [
            'id_override', 'type_entite', 'id_entite', 'justification',
            'ancienne_valeur', 'nouvelle_valeur', 'cree_le',
            'id_commande', 'id_commande_id',
            'override_par', 'override_par_id'
        ]
        read_only_fields = ['cree_le']


class JournalAuditSerializer(serializers.ModelSerializer):
    """Immutable Audit Log serializer"""
    execute_par = UtilisateurSerializer(read_only=True)
    execute_par_id = serializers.PrimaryKeyRelatedField(
        queryset=Utilisateur.objects.all(),
        source='execute_par',
        write_only=True,
        required=False
    )

    class Meta:
        model = JournalAudit
        fields = [
            'id_audit', 'type_action', 'type_entite', 'id_entite',
            'ancienne_valeur', 'nouvelle_valeur', 'description',
            'adresse_ip', 'timestamp',
            'execute_par', 'execute_par_id'
        ]
        read_only_fields = ['timestamp']


# ============================================================================
# OFFLINE & ANOMALY SERIALIZERS
# ============================================================================

class OperationOfflineSerializer(serializers.ModelSerializer):
    """Offline Operations Queue serializer"""
    id_utilisateur = UtilisateurSerializer(read_only=True)
    id_utilisateur_id = serializers.PrimaryKeyRelatedField(
        queryset=Utilisateur.objects.all(),
        source='id_utilisateur',
        write_only=True,
        required=False
    )

    class Meta:
        model = OperationOffline
        fields = [
            'id_operation', 'type_operation', 'donnees_operation', 'statut',
            'timestamp_local', 'timestamp_sync', 'erreur_sync', 'tentatives_sync',
            'id_utilisateur', 'id_utilisateur_id'
        ]


class AnomalieDetectionSerializer(serializers.ModelSerializer):
    """Anomaly Detection serializer"""
    class Meta:
        model = AnomalieDetection
        fields = [
            'id_anomalie', 'type_anomalie', 'severite', 'description',
            'id_entite_concernee', 'type_entite', 'detectee_le',
            'resolue_le', 'statut', 'note_resolution'
        ]
        read_only_fields = ['detectee_le']

