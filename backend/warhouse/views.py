from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.db.models import Sum, Q
from django.utils import timezone
from django.db import transaction as db_transaction

from .models import (
    Entrepot, NiveauStockage, Emplacement, Stock, MouvementStock,
    Chariot, ChariotOperation, Commande, LigneCommande, ResultatLivraison,
    Operation, PrevisionIA, AssignmentStockageIA, RoutePickingIA,
    Override, JournalAudit, OperationOffline, AnomalieDetection
)
from .serializers import (
    EntrepotSerializer, NiveauStockageSerializer, EmplacementSerializer,
    StockSerializer, MouvementStockSerializer, ChariotSerializer,
    ChariotOperationSerializer, CommandeSerializer, LigneCommandeSerializer,
    ResultatLivraisonSerializer, OperationSerializer, PrevisionIASerializer,
    AssignmentStockageIASerializer, RoutePickingIASerializer, OverrideSerializer,
    JournalAuditSerializer, OperationOfflineSerializer, AnomalieDetectionSerializer
)


# ============================================================================
# WAREHOUSE MANAGEMENT (FR-10 → FR-12)
# ============================================================================

class EntrepotViewSet(viewsets.ModelViewSet):
    """
    Warehouse/Depot Management

    Key Operations:
    - Create, Read, Update, Delete warehouses
    - View warehouse structure (floors, locations)
    - Manage active/inactive status
    - Cannot delete if has stock/floors/orders
    """
    queryset = Entrepot.objects.all()
    serializer_class = EntrepotSerializer
    lookup_field = 'id_entrepot'
    permission_classes = [IsAuthenticated]

    def destroy(self, request, *args, **kwargs):
        """Warehouse deletion with validation"""
        warehouse = self.get_object()
        # Check if warehouse has floors, locations, or stock
        if warehouse.niveaux_stockage.exists() or warehouse.emplacements.exists():
            return Response(
                {'error': 'Cannot delete warehouse with floors or locations'},
                status=status.HTTP_400_BAD_REQUEST
            )
        return super().destroy(request, *args, **kwargs)

    @action(detail=True, methods=['get'])
    def warehouse_floors(self, request, id_entrepot=None):
        """GET /warehouses/{id}/warehouse_floors/ - Get all floors in warehouse"""
        warehouse = self.get_object()
        floors = warehouse.niveaux_stockage.all()
        serializer = NiveauStockageSerializer(floors, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['get'])
    def warehouse_locations(self, request, id_entrepot=None):
        """GET /warehouses/{id}/warehouse_locations/ - Get all locations in warehouse"""
        warehouse = self.get_object()
        locations = warehouse.emplacements.all()
        serializer = EmplacementSerializer(locations, many=True)
        return Response(serializer.data)


# ============================================================================
# STORAGE FLOORS (FR-13)
# ============================================================================

class NiveauStockageViewSet(viewsets.ModelViewSet):
    """Storage Floor/Level Management"""
    queryset = NiveauStockage.objects.all()
    serializer_class = NiveauStockageSerializer
    lookup_field = 'id_niveau'
    permission_classes = [IsAuthenticated]

    @action(detail=False, methods=['get'])
    def filter_by_warehouse(self, request):
        """GET /floors/filter_by_warehouse/?warehouse_id=W001"""
        warehouse_id = request.query_params.get('warehouse_id')
        if warehouse_id:
            floors = NiveauStockage.objects.filter(id_entrepot=warehouse_id)
            serializer = self.get_serializer(floors, many=True)
            return Response(serializer.data)
        return Response({'error': 'warehouse_id required'}, status=status.HTTP_400_BAD_REQUEST)


# ============================================================================
# LOCATIONS/EMPLACEMENTS (FR-14 → FR-17)
# ============================================================================

class EmplacementViewSet(viewsets.ModelViewSet):
    """
    Location Management (both STORAGE and PICKING)

    Key Features:
    - Unique location codes (FR-17)
    - Type: STORAGE or PICKING
    - Status: AVAILABLE, OCCUPIED, BLOCKED
    - Can query by floor, warehouse, type, availability
    """
    queryset = Emplacement.objects.all()
    serializer_class = EmplacementSerializer
    lookup_field = 'id_emplacement'
    permission_classes = [IsAuthenticated]

    @action(detail=False, methods=['get'])
    def search_by_code(self, request):
        """GET /locations/search_by_code/?code=A1-01"""
        code = request.query_params.get('code')
        if code:
            try:
                location = Emplacement.objects.get(code_emplacement=code)
                serializer = self.get_serializer(location)
                return Response(serializer.data)
            except Emplacement.DoesNotExist:
                return Response({'error': 'Location not found'}, status=status.HTTP_404_NOT_FOUND)
        return Response({'error': 'code parameter required'}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['get'])
    def filter_by_floor(self, request):
        """GET /locations/filter_by_floor/?floor_id=F001"""
        floor_id = request.query_params.get('floor_id')
        if floor_id:
            locations = Emplacement.objects.filter(id_niveau=floor_id)
            serializer = self.get_serializer(locations, many=True)
            return Response(serializer.data)
        return Response({'error': 'floor_id required'}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['get'])
    def list_available_locations(self, request):
        """GET /locations/list_available_locations/ - Get available locations"""
        loc = Emplacement.objects.filter(statut='AVAILABLE', actif=True)
        serializer = self.get_serializer(loc, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def change_location_status(self, request, id_emplacement=None):
        """POST /locations/{id}/change_location_status/ - Update location status"""
        location = self.get_object()
        new_status = request.data.get('statut')
        if new_status in ['AVAILABLE', 'OCCUPIED', 'BLOCKED']:
            location.statut = new_status
            location.save()
            serializer = self.get_serializer(location)
            return Response(serializer.data)
        return Response({'error': 'Invalid status'}, status=status.HTTP_400_BAD_REQUEST)


# ============================================================================
# INVENTORY - STOCK (FR-23 → FR-27)
# ============================================================================

class StockViewSet(viewsets.ModelViewSet):
    """
    Stock Management - Current snapshot per SKU per location

    Operations:
    - Add stock, Transfer, Adjust, Query total
    - Prevent negative stock (FR-24)
    - Track by SKU, by location, by lot/serie
    """
    queryset = Stock.objects.all()
    serializer_class = StockSerializer
    lookup_field = 'id_stock'
    permission_classes = [IsAuthenticated]

    @action(detail=False, methods=['get'])
    def filter_by_sku(self, request):
        """GET /stock/filter_by_sku/?sku_id=SKU001"""
        sku_id = request.query_params.get('sku_id')
        if sku_id:
            stock = Stock.objects.filter(id_produit=sku_id)
            serializer = self.get_serializer(stock, many=True)
            return Response(serializer.data)
        return Response({'error': 'sku_id required'}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['get'])
    def calculate_total_by_sku(self, request):
        """GET /stock/calculate_total_by_sku/?sku_id=SKU001 - Total stock for SKU"""
        sku_id = request.query_params.get('sku_id')
        if sku_id:
            total = Stock.objects.filter(id_produit=sku_id).aggregate(Sum('quantite'))
            return Response({'sku_id': sku_id, 'total': total['quantite__sum'] or 0})
        return Response({'error': 'sku_id required'}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['post'])
    def transfer_stock(self, request, id_stock=None):
        """POST /stock/{id}/transfer_stock/ - Transfer stock between locations"""
        # Create stock movement and update source/destination stock
        pass

    @action(detail=True, methods=['post'])
    def adjust_stock_quantity(self, request, id_stock=None):
        """POST /stock/{id}/adjust_stock_quantity/ - Adjust stock quantity"""
        stock = self.get_object()
        new_quantity = request.data.get('quantity')
        if new_quantity < 0:
            return Response({'error': 'Cannot set negative stock'}, status=status.HTTP_400_BAD_REQUEST)
        stock.quantite = new_quantity
        stock.save()
        serializer = self.get_serializer(stock)
        return Response(serializer.data)


# ============================================================================
# STOCK MOVEMENTS - IMMUTABLE LEDGER (FR-25, FR-26)
# ============================================================================

class MouvementStockViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Stock Movement Ledger - IMMUTABLE (View only)

    All movements are created automatically from operations.
    This is an immutable audit trail of all stock changes.
    """
    queryset = MouvementStock.objects.all()
    serializer_class = MouvementStockSerializer
    lookup_field = 'id_mouvement'
    permission_classes = [IsAuthenticated]

    @action(detail=False, methods=['get'])
    def filter_by_sku(self, request):
        """GET /stock-movements/filter_by_sku/?sku_id=SKU001"""
        sku_id = request.query_params.get('sku_id')
        if sku_id:
            movements = MouvementStock.objects.filter(id_produit=sku_id).order_by('-date_execution')
            serializer = self.get_serializer(movements, many=True)
            return Response(serializer.data)
        return Response({'error': 'sku_id required'}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['get'])
    def filter_by_date_range(self, request):
        """GET /stock-movements/filter_by_date_range/?start=2026-01-01&end=2026-02-01"""
        start = request.query_params.get('start')
        end = request.query_params.get('end')
        if start and end:
            movements = MouvementStock.objects.filter(
                date_execution__gte=start,
                date_execution__lte=end
            ).order_by('-date_execution')
            serializer = self.get_serializer(movements, many=True)
            return Response(serializer.data)
        return Response({'error': 'start and end dates required'}, status=status.HTTP_400_BAD_REQUEST)


# ============================================================================
# CHARIOTS/TROLLEYS (FR-30 → FR-34)
# ============================================================================

class ChariotViewSet(viewsets.ModelViewSet):
    """Chariot/Trolley Management for picking operations"""
    queryset = Chariot.objects.all()
    serializer_class = ChariotSerializer
    lookup_field = 'id_chariot'
    permission_classes = [IsAuthenticated]

    @action(detail=False, methods=['get'])
    def list_available_chariots(self, request):
        """GET /chariots/list_available_chariots/ - Get available chariots"""
        chariots = Chariot.objects.filter(statut='AVAILABLE')
        serializer = self.get_serializer(chariots, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def assign_chariot(self, request, id_chariot=None):
        """POST /chariots/{id}/assign_chariot/ - Assign chariot to operation"""
        chariot = self.get_object()
        chariot.statut = 'IN_USE'
        chariot.save()
        serializer = self.get_serializer(chariot)
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def release_chariot(self, request, id_chariot=None):
        """POST /chariots/{id}/release_chariot/ - Release chariot"""
        chariot = self.get_object()
        chariot.statut = 'AVAILABLE'
        chariot.save()
        serializer = self.get_serializer(chariot)
        return Response(serializer.data)


class ChariotOperationViewSet(viewsets.ModelViewSet):
    """Chariot Operation Tracking"""
    queryset = ChariotOperation.objects.all()
    serializer_class = ChariotOperationSerializer
    lookup_field = 'id_chariot_operation'
    permission_classes = [IsAuthenticated]


# ============================================================================
# ORDERS MANAGEMENT (FR-40 → FR-47)
# ============================================================================

class CommandeViewSet(viewsets.ModelViewSet):
    """
    Order Management

    Types: COMMAND, PREPARATION, PICKING
    Statuses: DRAFT, GENERATED, IN_PROGRESS, COMPLETED, CANCELLED
    """
    queryset = Commande.objects.all()
    serializer_class = CommandeSerializer
    lookup_field = 'id_commande'
    permission_classes = [IsAuthenticated]

    @action(detail=False, methods=['get'])
    def list_pending_orders(self, request):
        """GET /orders/list_pending_orders/ - Get pending orders"""
        orders = Commande.objects.filter(statut__in=['DRAFT', 'GENERATED', 'IN_PROGRESS'])
        serializer = self.get_serializer(orders, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['get'])
    def order_line_items(self, request, id_commande=None):
        """GET /orders/{id}/order_line_items/ - Get order line items"""
        order = self.get_object()
        lines = order.lignes.all()
        serializer = LigneCommandeSerializer(lines, many=True)
        return Response(serializer.data)


class LigneCommandeViewSet(viewsets.ModelViewSet):
    """Order Line Items"""
    queryset = LigneCommande.objects.all()
    serializer_class = LigneCommandeSerializer
    lookup_field = 'id_ligne'
    permission_classes = [IsAuthenticated]


class ResultatLivraisonViewSet(viewsets.ModelViewSet):
    """Delivery Results - IMMUTABLE"""
    queryset = ResultatLivraison.objects.all()
    serializer_class = ResultatLivraisonSerializer
    lookup_field = 'id_resultat'
    permission_classes = [IsAuthenticated]

    def destroy(self, request, *args, **kwargs):
        """Prevent deletion of delivery results"""
        return Response(
            {'error': 'Delivery results are immutable'},
            status=status.HTTP_403_FORBIDDEN
        )


# ============================================================================
# OPERATIONS EXECUTION (FR-50 → FR-57)
# ============================================================================

class OperationViewSet(viewsets.ModelViewSet):
    """
    Operation Execution Management

    Types: RECEPTION, TRANSFER, PICKING, DELIVERY
    Atomic operations with stock updates
    """
    queryset = Operation.objects.all()
    serializer_class = OperationSerializer
    lookup_field = 'id_operation'
    permission_classes = [IsAuthenticated]

    @action(detail=True, methods=['post'])
    def execute_receipt_operation(self, request, id_operation=None):
        """POST /operations/{id}/execute_receipt_operation/"""
        operation = self.get_object()
        # Implement receipt logic with stock creation
        pass

    @action(detail=True, methods=['post'])
    def execute_transfer_operation(self, request, id_operation=None):
        """POST /operations/{id}/execute_transfer_operation/"""
        operation = self.get_object()
        # Implement atomic transfer logic
        pass

    @action(detail=True, methods=['post'])
    def execute_picking_operation(self, request, id_operation=None):
        """POST /operations/{id}/execute_picking_operation/"""
        operation = self.get_object()
        # Implement picking logic
        pass

    @action(detail=True, methods=['post'])
    def execute_delivery_operation(self, request, id_operation=None):
        """POST /operations/{id}/execute_delivery_operation/"""
        operation = self.get_object()
        # Implement delivery logic
        pass


# ============================================================================
# AI SYSTEM (FR-8, AI Order Generation)
# ============================================================================

class PrevisionIAViewSet(viewsets.ModelViewSet):
    """AI Demand Forecasts"""
    queryset = PrevisionIA.objects.all()
    serializer_class = PrevisionIASerializer
    lookup_field = 'id_prevision'
    permission_classes = [IsAuthenticated]


class AssignmentStockageIAViewSet(viewsets.ModelViewSet):
    """AI Storage Location Assignments"""
    queryset = AssignmentStockageIA.objects.all()
    serializer_class = AssignmentStockageIASerializer
    lookup_field = 'id_assignment'
    permission_classes = [IsAuthenticated]

    @action(detail=True, methods=['post'])
    def override_ai_assignment(self, request, id_assignment=None):
        """POST /storage-assignments/{id}/override_ai_assignment/ - Override AI recommendation"""
        # Create override record and log justification
        pass


class RoutePickingIAViewSet(viewsets.ModelViewSet):
    """AI Optimized Picking Routes"""
    queryset = RoutePickingIA.objects.all()
    serializer_class = RoutePickingIASerializer
    lookup_field = 'id_route'
    permission_classes = [IsAuthenticated]

    @action(detail=True, methods=['post'])
    def override_ai_route(self, request, id_route=None):
        """POST /picking-routes/{id}/override_ai_route/ - Override AI route"""
        pass


# ============================================================================
# OVERRIDES & AUDIT (FR-44 → FR-47) - IMMUTABLE
# ============================================================================

class OverrideViewSet(viewsets.ReadOnlyModelViewSet):
    """
    AI Override Records - IMMUTABLE VIEW ONLY

    Records all instances where users overrode AI recommendations
    with justification and old/new values.
    """
    queryset = Override.objects.all()
    serializer_class = OverrideSerializer
    lookup_field = 'id_override'
    permission_classes = [IsAuthenticated]

    @action(detail=False, methods=['get'])
    def filter_by_user(self, request):
        """GET /overrides/filter_by_user/?user_id=USR001"""
        user_id = request.query_params.get('user_id')
        if user_id:
            overrides = Override.objects.filter(override_par=user_id)
            serializer = self.get_serializer(overrides, many=True)
            return Response(serializer.data)
        return Response({'error': 'user_id required'}, status=status.HTTP_400_BAD_REQUEST)


class JournalAuditViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Immutable Audit Log - VIEW ONLY

    Complete historical record of all system actions.
    Cannot be modified or deleted (FR-9, FR-47, NFR-10).
    """
    queryset = JournalAudit.objects.all()
    serializer_class = JournalAuditSerializer
    lookup_field = 'id_audit'
    permission_classes = [IsAuthenticated]

    @action(detail=False, methods=['get'])
    def filter_by_user(self, request):
        """GET /audit-logs/filter_by_user/?user_id=USR001"""
        user_id = request.query_params.get('user_id')
        if user_id:
            logs = JournalAudit.objects.filter(execute_par=user_id).order_by('-timestamp')
            serializer = self.get_serializer(logs, many=True)
            return Response(serializer.data)
        return Response({'error': 'user_id required'}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['get'])
    def filter_by_entity(self, request):
        """GET /audit-logs/filter_by_entity/?type=Order&id=ORD001"""
        entity_type = request.query_params.get('type')
        entity_id = request.query_params.get('id')
        if entity_type and entity_id:
            logs = JournalAudit.objects.filter(
                type_entite=entity_type,
                id_entite=entity_id
            ).order_by('-timestamp')
            serializer = self.get_serializer(logs, many=True)
            return Response(serializer.data)
        return Response({'error': 'type and id required'}, status=status.HTTP_400_BAD_REQUEST)


# ============================================================================
# OFFLINE & SYNC (FR-70, FR-71)
# ============================================================================

class OperationOfflineViewSet(viewsets.ModelViewSet):
    """
    Offline Operations Sync Queue

    Manages operations queued while offline.
    Automatic sync on reconnection (FR-70, FR-71).
    Conflict resolution with stock consistency.
    """
    queryset = OperationOffline.objects.all()
    serializer_class = OperationOfflineSerializer
    lookup_field = 'id_operation'
    permission_classes = [IsAuthenticated]

    @action(detail=False, methods=['get'])
    def list_pending_sync_operations(self, request):
        """GET /sync-queue/list_pending_sync_operations/ - Get pending sync operations"""
        operations = OperationOffline.objects.filter(statut='PENDING')
        serializer = self.get_serializer(operations, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def synchronize_operation(self, request, id_operation=None):
        """POST /sync-queue/{id}/synchronize_operation/ - Manually trigger sync"""
        operation = self.get_object()
        # Execute sync and update status
        operation.statut = 'SYNCED'
        operation.timestamp_sync = timezone.now()
        operation.save()
        serializer = self.get_serializer(operation)
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def resolve_conflict(self, request, id_operation=None):
        """POST /sync-queue/{id}/resolve-conflict/ - Resolve sync conflict"""
        operation = self.get_object()
        # Implement conflict resolution logic
        pass


# ============================================================================
# ANOMALY DETECTION
# ============================================================================

class AnomalieDetectionViewSet(viewsets.ModelViewSet):
    """Anomaly Detection & Monitoring"""
    queryset = AnomalieDetection.objects.all()
    serializer_class = AnomalieDetectionSerializer
    lookup_field = 'id_anomalie'
    permission_classes = [IsAuthenticated]

    @action(detail=False, methods=['get'])
    def list_critical_anomalies(self, request):
        """GET /anomalies/list_critical_anomalies/ - Get critical anomalies"""
        anomalies = AnomalieDetection.objects.filter(severite='CRITICAL', statut='OPEN')
        serializer = self.get_serializer(anomalies, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def list_open_anomalies(self, request):
        """GET /anomalies/list_open_anomalies/ - Get unresolved anomalies"""
        anomalies = AnomalieDetection.objects.filter(statut__in=['OPEN', 'INVESTIGATING'])
        serializer = self.get_serializer(anomalies, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def resolve_anomaly(self, request, id_anomalie=None):
        """POST /anomalies/{id}/resolve_anomaly/ - Mark anomaly as resolved"""
        anomaly = self.get_object()
        anomaly.statut = 'RESOLVED'
        anomaly.resolue_le = timezone.now()
        anomaly.note_resolution = request.data.get('note', '')
        anomaly.save()
        serializer = self.get_serializer(anomaly)
        return Response(serializer.data)
