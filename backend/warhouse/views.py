from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from django.db.models import Sum, Q
from django.utils import timezone
from django.db import transaction as db_transaction

from .models import (
    Entrepot, NiveauStockage, NiveauPicking, Rack, RackProduct, Emplacement, Stock, Vrack, MouvementStock,
    Chariot, ChariotOperation, Commande, LigneCommande, ResultatLivraison,
    Operation, PrevisionIA, AssignmentStockageIA, RoutePickingIA,
    Override, JournalAudit, OperationOffline, AnomalieDetection
)
from Users.models import Utilisateur
from Produit.models import Produit
from .serializers import (
    EntrepotSerializer, NiveauStockageSerializer, NiveauPickingSerializer, 
    RackSerializer, RackProductSerializer, EmplacementSerializer,
    StockSerializer, VrackSerializer, MouvementStockSerializer, ChariotSerializer,
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
    permission_classes = [AllowAny] # Changed from IsAuthenticated for development

    def perform_create(self, serializer):
        # The save() method of Entrepot handles floor creation,
        # but we call it explicitly here just in case.
        warehouse = serializer.save()
        return warehouse

    @action(detail=True, methods=['post'])
    @action(detail=True, methods=['post'])
    def initialize_structure(self, request, id_entrepot=None):
        """POST /warehouses/{id}/initialize_structure/ - Manually trigger auto-generation"""
        warehouse = self.get_object()
        
        # Trigger create logic manually even if not 'is_new'
        from .models import NiveauPicking, NiveauStockage, Vrack
        from Produit.models import Produit
        
        np, created = NiveauPicking.objects.get_or_create(
            id_entrepot=warehouse,
            code_niveau='PICKING',
            defaults={'description': 'Main Picking Floor (A-X)'}
        )
        
        # Create only the first storage floor (N1) manually if it doesn't exist
        floors = []
        ns, created = NiveauStockage.objects.get_or_create(
            id_entrepot=warehouse,
            code_niveau='N1',
            defaults={'type_niveau': 'STOCK', 'description': 'Storage Floor 1'}
        )
        floors.append(ns)
        
        # Ensure Vracks exist
        for produit in Produit.objects.all():
            Vrack.objects.get_or_create(
                id_entrepot=warehouse,
                id_produit=produit,
                defaults={'quantite': 0}
            )

        return Response({
            'status': 'Structure initialized',
            'floors_created': [f.code_niveau for f in floors],
            'picking_floor': np.code_niveau
        })
            
        return Response({'status': 'Structure initialized/verified'})

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
        
        # Get from both tables
        stock_floors = warehouse.niveaux_stockage.all()
        picking_floors = warehouse.niveaux_picking.all()
        
        # Serialize both
        stock_data = NiveauStockageSerializer(stock_floors, many=True).data
        picking_data = NiveauPickingSerializer(picking_floors, many=True).data
        
        # Combine
        return Response(stock_data + picking_data)

    @action(detail=True, methods=['get'])
    def warehouse_locations(self, request, id_entrepot=None):
        """GET /warehouses/{id}/warehouse_locations/ - Get all locations in warehouse"""
        warehouse = self.get_object()
        locations = warehouse.emplacements.all()
        serializer = EmplacementSerializer(locations, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    @action(detail=False, methods=['get'])
    def dashboard_stats(self, request):
        """GET /warehouses/dashboard_stats/ - Get overview statistics for the landing page"""
        warehouse_id = request.query_params.get('warehouse_id')
        now = timezone.now()
        last_24h = now - timezone.timedelta(hours=24)
        
        # User counts (Global for now, or could filter by warehouse if users are linked to warehouses)
        total_users = Utilisateur.objects.count()
        admin_users = Utilisateur.objects.filter(role='ADMIN').count()
        employee_users = Utilisateur.objects.filter(role='EMPLOYEE').count()
        
        # Warehouse & Structure
        if warehouse_id:
            total_locations = Emplacement.objects.filter(id_entrepot=warehouse_id).count()
            occupied_locations = Emplacement.objects.filter(statut='OCCUPIED', id_entrepot=warehouse_id).count()
            available_locations = Emplacement.objects.filter(statut='AVAILABLE', id_entrepot=warehouse_id).count()
            blocked_locations = Emplacement.objects.filter(statut='BLOCKED', id_entrepot=warehouse_id).count()

            stock_product_ids = set(
                Stock.objects.filter(
                    id_emplacement__id_entrepot=warehouse_id,
                    quantite__gt=0
                ).values_list('id_produit_id', flat=True)
            )
            vrack_product_ids = set(
                Vrack.objects.filter(
                    id_entrepot=warehouse_id,
                    quantite__gt=0
                ).values_list('id_produit_id', flat=True)
            )
            total_products = len(stock_product_ids.union(vrack_product_ids))

            total_stock_qty = Stock.objects.filter(id_emplacement__id_entrepot=warehouse_id).aggregate(total=Sum('quantite'))['total'] or 0
            total_vrack_qty = Vrack.objects.filter(id_entrepot=warehouse_id).aggregate(total=Sum('quantite'))['total'] or 0

            total_chariots = Chariot.objects.filter(id_entrepot=warehouse_id).count()
            available_chariots = Chariot.objects.filter(id_entrepot=warehouse_id, statut='AVAILABLE').count()
            maintenance_chariots = Chariot.objects.filter(id_entrepot=warehouse_id, statut='MAINTENANCE').count()
            
            # Activity (Last 24h)
            receptions_24h = MouvementStock.objects.filter(type_mouvement='RECEPTION', date_execution__gte=last_24h, id_entrepot=warehouse_id).count()
            pickings_24h = MouvementStock.objects.filter(type_mouvement='PICKING', date_execution__gte=last_24h, id_entrepot=warehouse_id).count()
            movements_24h = MouvementStock.objects.filter(date_execution__gte=last_24h, id_entrepot=warehouse_id).count()
        else:
            total_locations = Emplacement.objects.count()
            occupied_locations = Emplacement.objects.filter(statut='OCCUPIED').count()
            available_locations = Emplacement.objects.filter(statut='AVAILABLE').count()
            blocked_locations = Emplacement.objects.filter(statut='BLOCKED').count()
            
            total_products = Produit.objects.count()
            total_stock_qty = Stock.objects.aggregate(total=Sum('quantite'))['total'] or 0
            total_vrack_qty = Vrack.objects.aggregate(total=Sum('quantite'))['total'] or 0
            
            total_chariots = Chariot.objects.count()
            available_chariots = Chariot.objects.filter(statut='AVAILABLE').count()
            maintenance_chariots = Chariot.objects.filter(statut='MAINTENANCE').count()
            
            receptions_24h = MouvementStock.objects.filter(type_mouvement='RECEPTION', date_execution__gte=last_24h).count()
            pickings_24h = MouvementStock.objects.filter(type_mouvement='PICKING', date_execution__gte=last_24h).count()
            movements_24h = MouvementStock.objects.filter(date_execution__gte=last_24h).count()

        total_warehouses = Entrepot.objects.count()

        return Response({
            'users': {
                'total': total_users,
                'admins': admin_users,
                'employees': employee_users,
            },
            'warehouse': {
                'count': total_warehouses,
                'locations': total_locations,
                'occupied': occupied_locations,
                'available': available_locations,
                'blocked': blocked_locations,
                'occupancy_rate': (occupied_locations / total_locations * 100) if total_locations > 0 else 0
            },
            'inventory': {
                'products': total_products,
                'stock_qty': float(total_stock_qty),
                'vrack_qty': float(total_vrack_qty),
            },
            'chariots': {
                'total': total_chariots,
                'available': available_chariots,
                'maintenance': maintenance_chariots,
            },
            'activity': {
                'receptions_24h': receptions_24h,
                'pickings_24h': pickings_24h,
                'total_movements_24h': movements_24h
            }
        })


# ============================================================================
# STORAGE FLOORS (FR-13)
# ============================================================================

class NiveauStockageViewSet(viewsets.ModelViewSet):
    """Storage Floor/Level Management"""
    queryset = NiveauStockage.objects.all()
    serializer_class = NiveauStockageSerializer
    lookup_field = 'id_niveau'
    permission_classes = [AllowAny] # Changed for development

    def get_queryset(self):
        queryset = NiveauStockage.objects.all()
        warehouse_id = self.request.query_params.get('warehouse_id')
        if warehouse_id:
            queryset = queryset.filter(id_entrepot=warehouse_id)
        else:
            if not self.request.user.is_superuser:
                return NiveauStockage.objects.none()
        return queryset

    def destroy(self, request, *args, **kwargs):
        floor = self.get_object()
        # Enforce "At least one storing floor" rule
        if NiveauStockage.objects.filter(id_entrepot=floor.id_entrepot).count() <= 1:
            return Response(
                {'error': 'A warehouse must have at least one storing floor.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        return super().destroy(request, *args, **kwargs)

    @action(detail=False, methods=['get'])
    def filter_by_warehouse(self, request):
        """GET /floors/filter_by_warehouse/?warehouse_id=W001"""
        warehouse_id = request.query_params.get('warehouse_id')
        if warehouse_id:
            floors = NiveauStockage.objects.filter(id_entrepot=warehouse_id)
            serializer = self.get_serializer(floors, many=True)
            return Response(serializer.data)
        return Response({'error': 'warehouse_id required'}, status=status.HTTP_400_BAD_REQUEST)


class NiveauPickingViewSet(viewsets.ModelViewSet):
    """Picking Floor Management"""
    queryset = NiveauPicking.objects.all()
    serializer_class = NiveauPickingSerializer
    lookup_field = 'id_niveau_picking'
    permission_classes = [AllowAny]

    def get_queryset(self):
        queryset = NiveauPicking.objects.all()
        warehouse_id = self.request.query_params.get('warehouse_id')
        if warehouse_id:
            queryset = queryset.filter(id_entrepot=warehouse_id)
        else:
            if not self.request.user.is_superuser:
                return NiveauPicking.objects.none()
        return queryset

    def destroy(self, request, *args, **kwargs):
        floor = self.get_object()
        # Enforce "At least one picking floor" rule
        if NiveauPicking.objects.filter(id_entrepot=floor.id_entrepot).count() <= 1:
            return Response(
                {'error': 'A warehouse must have at least one picking floor.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        return super().destroy(request, *args, **kwargs)

    @action(detail=False, methods=['get'])
    def filter_by_warehouse(self, request):
        warehouse_id = request.query_params.get('warehouse_id')
        if warehouse_id:
            floors = NiveauPicking.objects.filter(id_entrepot=warehouse_id)
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
    permission_classes = [AllowAny] # Changed for development

    def get_queryset(self):
        queryset = Emplacement.objects.all()
        warehouse_id = self.request.query_params.get('warehouse_id')
        if warehouse_id:
            queryset = queryset.filter(id_entrepot=warehouse_id)
        else:
            if not self.request.user.is_superuser:
                return Emplacement.objects.none()
        return queryset

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset().order_by('id_emplacement')
        limit_param = request.query_params.get('limit')
        offset_param = request.query_params.get('offset')

        if limit_param is None and offset_param is None:
            serializer = self.get_serializer(queryset, many=True)
            return Response(serializer.data)

        try:
            limit = int(limit_param) if limit_param is not None else 20
            offset = int(offset_param) if offset_param is not None else 0
        except ValueError:
            return Response(
                {'error': 'limit and offset must be integers'},
                status=status.HTTP_400_BAD_REQUEST
            )

        if limit <= 0 or offset < 0:
            return Response(
                {'error': 'limit must be > 0 and offset must be >= 0'},
                status=status.HTTP_400_BAD_REQUEST
            )

        total_count = queryset.count()
        paged_queryset = queryset[offset:offset + limit]
        serializer = self.get_serializer(paged_queryset, many=True)

        return Response({
            'count': total_count,
            'limit': limit,
            'offset': offset,
            'has_more': (offset + limit) < total_count,
            'results': serializer.data,
        })

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

class RackViewSet(viewsets.ModelViewSet):
    """
    Rack Management
    """
    queryset = Rack.objects.all()
    serializer_class = RackSerializer
    lookup_field = 'id_rack'
    permission_classes = [AllowAny]

    def get_queryset(self):
        queryset = Rack.objects.all()
        warehouse_id = self.request.query_params.get('warehouse_id')
        if warehouse_id:
            # Check both possible floor links for warehouse ID
            queryset = queryset.filter(
                Q(storage_floor__id_entrepot=warehouse_id) | 
                Q(picking_floor__id_entrepot=warehouse_id)
            )
        return queryset


class RackProductViewSet(viewsets.ModelViewSet):
    """
    Products in Rack Management
    """
    queryset = RackProduct.objects.all()
    serializer_class = RackProductSerializer
    permission_classes = [AllowAny]


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

    def get_queryset(self):
        queryset = Stock.objects.all()
        warehouse_id = self.request.query_params.get('warehouse_id')
        if warehouse_id:
            queryset = queryset.filter(id_emplacement__id_entrepot=warehouse_id)
        else:
            # If no warehouse_id is provided, we return nothing to ensure isolation
            # The exception is for superusers or if we want to default to something
            if self.request.user.is_superuser:
                return queryset
            return Stock.objects.none()
        return queryset

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


class VrackViewSet(viewsets.ModelViewSet):
    """
    Vrack Management - specialized bulk storage tracking

    Operations:
    - Track products in the V-Rack area
    - Know quantity per product in the bulk zone
    """
    queryset = Vrack.objects.all()
    serializer_class = VrackSerializer
    lookup_field = 'id_vrack'
    permission_classes = [AllowAny] # Changed for development

    def get_queryset(self):
        queryset = Vrack.objects.all()
        warehouse_id = self.request.query_params.get('warehouse_id')
        if warehouse_id:
            queryset = queryset.filter(id_entrepot=warehouse_id)
        return queryset

    @action(detail=False, methods=['get'])
    def by_warehouse(self, request):
        """GET /vracks/by_warehouse/?warehouse_id=WH001"""
        warehouse_id = request.query_params.get('warehouse_id')
        if warehouse_id:
            vracks = Vrack.objects.filter(id_entrepot=warehouse_id)
            serializer = self.get_serializer(vracks, many=True)
            return Response(serializer.data)
        return Response({'error': 'warehouse_id required'}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['get'])
    def product_quantity(self, request):
        """GET /vracks/product_quantity/?product_id=P0001&warehouse_id=WH001"""
        p_id = request.query_params.get('product_id')
        w_id = request.query_params.get('warehouse_id')
        if p_id and w_id:
            try:
                vrack = Vrack.objects.get(id_produit=p_id, id_entrepot=w_id)
                return Response({'product_id': p_id, 'quantity': vrack.quantite})
            except Vrack.DoesNotExist:
                return Response({'product_id': p_id, 'quantity': 0})
        return Response({'error': 'product_id and warehouse_id required'}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['post'])
    def transfer_to_shelf(self, request, id_vrack=None):
        """
        POST /vracks/{id}/transfer_to_shelf/
        Body: { 
          'destination_location_id': 'EMP001', 
          'quantity': 10,
          'notes': 'Picking for order...' 
        }
        This will create a MouvementStock which triggers the signal to update Vrack qty.
        """
        vrack = self.get_object()
        dest_id = request.data.get('destination_location_id')
        qty = request.data.get('quantity')
        notes = request.data.get('notes', '')

        if not dest_id or not qty:
            return Response({'error': 'destination_location_id and quantity required'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            qty = float(qty)
            if qty <= 0:
                return Response({'error': 'Quantity must be positive'}, status=status.HTTP_400_BAD_REQUEST)
            if qty > vrack.quantite:
                return Response({'error': 'Insufficient quantity in Vrack'}, status=status.HTTP_400_BAD_REQUEST)

            destination = Emplacement.objects.get(id_emplacement=dest_id)
            source_code = f"V-RACK-{vrack.id_entrepot_id}"
            
            # Find the V-RACK source emplacement
            try:
                source = Emplacement.objects.get(code_emplacement=source_code, id_entrepot=vrack.id_entrepot)
            except Emplacement.DoesNotExist:
                # Fallback: maybe just V-RACK
                source = Emplacement.objects.filter(code_emplacement__contains='V-RACK', id_entrepot=vrack.id_entrepot).first()
                if not source:
                    return Response({'error': f'Source location {source_code} not found in this warehouse'}, status=status.HTTP_404_NOT_FOUND)

            with db_transaction.atomic():
                # 1. Create MouvementStock
                mvt_id = f"MVT_{timezone.now().strftime('%Y%m%d%H%M%S')}_{vrack.id_produit_id}"
                mvt = MouvementStock.objects.create(
                    id_mouvement=mvt_id,
                    id_entrepot=vrack.id_entrepot,
                    type_mouvement='TRANSFERT',
                    id_produit=vrack.id_produit,
                    id_emplacement_source=source,
                    id_emplacement_destination=destination,
                    quantite=qty,
                    notes=f"Vrack Transfer: {notes}"
                )
                
                # 2. Update physical stock in destination
                # (Normally handled by a trigger/signal or manually)
                stock_dest, _ = Stock.objects.get_or_create(
                    id_produit=vrack.id_produit,
                    id_emplacement=destination,
                    defaults={'quantite': 0}
                )
                stock_dest.quantite += qty
                stock_dest.save()

                # Note: The post_save signal on MouvementStock will handle vrack.quantite -= qty

            return Response({
                'status': 'Transfer successful',
                'new_vrack_quantity': vrack.quantite - qty, # Signal will have updated the DB but we return expected
                'movement_id': mvt.id_mouvement
            })

        except Emplacement.DoesNotExist:
            return Response({'error': 'Destination location not found'}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


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

    def get_queryset(self):
        queryset = MouvementStock.objects.all()
        warehouse_id = self.request.query_params.get('warehouse_id')
        if warehouse_id:
            queryset = queryset.filter(id_entrepot=warehouse_id)
        else:
            if self.request.user.is_superuser:
                return queryset.order_by('-date_execution')
            return MouvementStock.objects.none()
        return queryset.order_by('-date_execution')

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
    permission_classes = [AllowAny] # Changed for development

    def get_queryset(self):
        queryset = Chariot.objects.all()
        warehouse_id = self.request.query_params.get('warehouse_id')
        if warehouse_id:
            queryset = queryset.filter(id_entrepot=warehouse_id)
        return queryset

    @action(detail=False, methods=['get'])
    def list_available_chariots(self, request):
        """GET /chariots/list_available_chariots/ - Get available chariots"""
        chariots = Chariot.objects.filter(statut='AVAILABLE')
        serializer = self.get_serializer(chariots, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def by_code(self, request):
        """GET /chariots/by_code/?code=CH01"""
        code = request.query_params.get('code')
        if not code:
            return Response({'error': 'Code required'}, status=status.HTTP_400_BAD_REQUEST)
        try:
            chariot = Chariot.objects.get(code_chariot=code)
            return Response(self.get_serializer(chariot).data)
        except Chariot.DoesNotExist:
            return Response({'error': 'Chariot not found'}, status=status.HTTP_404_NOT_FOUND)

    @action(detail=True, methods=['post'])
    def assign_chariot(self, request, id_chariot=None):
        """POST /chariots/{id}/assign_chariot/ - Assign chariot to operation"""
        chariot = self.get_object()
        if chariot.statut != 'AVAILABLE':
            return Response({'error': f'Chariot is {chariot.statut}'}, status=status.HTTP_400_BAD_REQUEST)
        
        chariot.statut = 'IN_USE'
        chariot.save()
        
        # Log operation
        ChariotOperation.objects.create(
            id_chariot_operation=f"OP_{chariot.id_chariot}_{timezone.now().strftime('%Y%m%d%H%M%S')}",
            id_chariot=chariot,
            id_emplacement_courant=chariot.id_emplacement_courant
        )
        
        serializer = self.get_serializer(chariot)
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def release_chariot(self, request, id_chariot=None):
        """POST /chariots/{id}/release_chariot/ - Release chariot"""
        chariot = self.get_object()
        chariot.statut = 'AVAILABLE'
        chariot.save()
        
        # Close last operation
        last_op = chariot.operations.filter(date_liberation__isnull=True).last()
        if last_op:
            last_op.date_liberation = timezone.now()
            last_op.save()
            
        serializer = self.get_serializer(chariot)
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def set_maintenance(self, request, id_chariot=None):
        """POST /chariots/{id}/set_maintenance/"""
        chariot = self.get_object()
        chariot.statut = 'MAINTENANCE'
        chariot.save()
        return Response(self.get_serializer(chariot).data)


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

    def get_queryset(self):
        queryset = JournalAudit.objects.all()
        warehouse_id = self.request.query_params.get('warehouse_id')
        if warehouse_id:
            queryset = queryset.filter(id_entrepot=warehouse_id)
        else:
            if self.request.user.is_superuser:
                return queryset.order_by('-timestamp')
            return JournalAudit.objects.none()
        return queryset.order_by('-timestamp')

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
