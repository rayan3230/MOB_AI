from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from django.db.models import Sum, Q
from django.utils import timezone

from .models import (
    Produit, CodeBarresProduit, HistoriqueDemande,
    DelaisApprovisionnement, PolitiqueReapprovisionnement,
    cmd_achat_ouvertes_opt
)
from .serializers import (
    ProduitSerializer, CodeBarresProduitSerializer,
    HistoriqueDemandeSerializer, DelaisApprovisionnementSerializer,
    PolitiqueReapprovisionnementSerializer, CmdAchatSerializer
)


# ============================================================================
# SKU/PRODUCT CRUD
# ============================================================================

class ProduitViewSet(viewsets.ModelViewSet):
    """
    Complete SKU/Product Management

    API Endpoints:
    - GET    /produits/                          - List all SKUs
    - POST   /produits/                          - Create new SKU
    - GET    /produits/{id}/                     - Get SKU by ID
    - PUT    /produits/{id}/                     - Update SKU completely
    - PATCH  /produits/{id}/                     - Update SKU partially
    - DELETE /produits/{id}/                     - Deactivate SKU (logical delete)

    Custom Endpoints:
    - GET    /produits/active/                   - Get active SKUs only
    - GET    /produits/{id}/barcodes/            - Get all barcodes for SKU
    - POST   /produits/{id}/barcode/             - Add barcode to SKU
    - GET    /produits/{id}/demand-history/     - Get demand history for SKU
    - GET    /produits/{id}/stock-level/        - Get current stock level
    - GET    /produits/{id}/replenishment-policy/ - Get replenishment policy
    - POST   /produits/{id}/update-weight/      - Update SKU weight
    """

    queryset = Produit.objects.select_related('id_rack').all()
    serializer_class = ProduitSerializer
    lookup_field = 'id_produit'
    permission_classes = [AllowAny]

    # -----------------------------------------------------------------------
    # CREATE OPERATIONS
    # -----------------------------------------------------------------------

    def create(self, request, *args, **kwargs):
        """
        POST /produits/
        Create new SKU/Product
        Required: id_produit, sku, nom_produit, unite_mesure, categorie
        """
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            produit = serializer.save()

            # Create default replenishment policy
            try:
                PolitiqueReapprovisionnement.objects.create(
                    id_produit=produit,
                    stock_securite=0,
                    quantite_min_commande=0,
                    taille_lot=0
                )
            except Exception as e:
                print(f"Error creating replenishment policy: {str(e)}")

            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['post'])
    def add_barcode(self, request, id_produit=None):
        """
        POST /produits/{id}/barcode/
        Add barcode to SKU
        Body: { "code_barres": "123456789", "type_code_barres": "EAN13", "principal": true }
        """
        produit = self.get_object()
        code_barres = request.data.get('code_barres')
        type_code = request.data.get('type_code_barres', 'UNKNOWN')
        is_principal = request.data.get('principal', False)

        if not code_barres:
            return Response(
                {'error': 'code_barres is required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            # If marking as principal, unmark others
            if is_principal:
                CodeBarresProduit.objects.filter(
                    id_produit=produit,
                    principal=True
                ).update(principal=False)

            barcode, created = CodeBarresProduit.objects.get_or_create(
                code_barres=code_barres,
                defaults={
                    'id_produit': produit,
                    'type_code_barres': type_code,
                    'principal': is_principal
                }
            )

            serializer = CodeBarresProduitSerializer(barcode)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        except Exception as e:
            return Response(
                {'error': f'Error adding barcode: {str(e)}'},
                status=status.HTTP_400_BAD_REQUEST
            )

    # -----------------------------------------------------------------------
    # READ OPERATIONS
    # -----------------------------------------------------------------------

    def list(self, request, *args, **kwargs):
        """
        GET /produits/
        List all SKUs
        Query params: actif (true/false), search (SKU or Name), limit, offset
        """
        queryset = self.get_queryset().order_by('id_produit')
        actif = request.query_params.get('actif')
        search = request.query_params.get('search')
        warehouse_id = request.query_params.get('warehouse_id')
        limit_param = request.query_params.get('limit')
        offset_param = request.query_params.get('offset')

        if actif is not None:
            queryset = queryset.filter(actif=actif.lower() == 'true')
        
        if search:
            queryset = queryset.filter(
                Q(sku__icontains=search) | Q(nom_produit__icontains=search)
            )

        if warehouse_id:
            normalized_warehouse_id = str(warehouse_id).strip().strip('"')
            queryset = queryset.filter(
                Q(id_rack__storage_floor__id_entrepot_id=normalized_warehouse_id)
                | Q(id_rack__picking_floor__id_entrepot_id=normalized_warehouse_id)
            ).distinct()

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

    def retrieve(self, request, *args, **kwargs):
        """
        GET /produits/{id}/
        Get single SKU with all details
        """
        return super().retrieve(request, *args, **kwargs)

    @action(detail=False, methods=['get'])
    def active(self, request):
        """
        GET /produits/active/
        Get all active SKUs
        """
        produits = Produit.objects.filter(actif=True)
        serializer = self.get_serializer(produits, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['get'])
    def barcodes(self, request, id_produit=None):
        """
        GET /produits/{id}/barcodes/
        Get all barcodes for a SKU
        """
        produit = self.get_object()
        barcodes = CodeBarresProduit.objects.filter(id_produit=produit)
        serializer = CodeBarresProduitSerializer(barcodes, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['get'])
    def vrack_info(self, request, id_produit=None):
        """
        GET /produits/{id}/vrack_info/
        Get Vrack quantities across all warehouses for this product
        """
        produit = self.get_object()
        vracks = produit.vracks.all()
        data = []
        for v in vracks:
            data.append({
                'id_vrack': v.id_vrack,
                'id_entrepot': v.id_entrepot_id,
                'nom_entrepot': v.id_entrepot.nom_entrepot,
                'quantite': v.quantite,
                'mise_a_jour_le': v.mise_a_jour_le
            })
        return Response(data)

    @action(detail=True, methods=['get'])
    def demand_history(self, request, id_produit=None):
        """
        GET /produits/{id}/demand-history/
        Get demand history for SKU
        Query params: days (get last N days, default: 30)
        """
        produit = self.get_object()
        days = int(request.query_params.get('days', 30))

        from datetime import timedelta
        start_date = timezone.now().date() - timedelta(days=days)

        history = HistoriqueDemande.objects.filter(
            id_produit=produit,
            date__gte=start_date
        ).order_by('-date')

        serializer = HistoriqueDemandeSerializer(history, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['get'])
    def stock_level(self, request, id_produit=None):
        """
        GET /produits/{id}/stock-level/
        Get current total stock level for SKU
        """
        produit = self.get_object()
        try:
            from warhouse.models import Stock
            total_stock = Stock.objects.filter(
                id_produit=produit
            ).aggregate(total=Sum('quantite'))['total'] or 0

            return Response({
                'id_produit': produit.id_produit,
                'nom_produit': produit.nom_produit,
                'total_stock': total_stock,
                'unit': produit.unite_mesure
            })
        except Exception as e:
            return Response(
                {'error': f'Error retrieving stock: {str(e)}'},
                status=status.HTTP_400_BAD_REQUEST
            )

    @action(detail=True, methods=['get'])
    def replenishment_policy(self, request, id_produit=None):
        """
        GET /produits/{id}/replenishment-policy/
        Get replenishment policy for SKU
        """
        produit = self.get_object()
        try:
            policy = PolitiqueReapprovisionnement.objects.get(id_produit=produit)
            serializer = PolitiqueReapprovisionnementSerializer(policy)
            return Response(serializer.data)
        except PolitiqueReapprovisionnement.DoesNotExist:
            return Response(
                {'error': 'No replenishment policy found'},
                status=status.HTTP_404_NOT_FOUND
            )

    @action(detail=True, methods=['get'])
    def lead_time(self, request, id_produit=None):
        """
        GET /produits/{id}/lead-time/
        Get supplier lead time for SKU
        """
        produit = self.get_object()
        try:
            lead_time = DelaisApprovisionnement.objects.get(id_produit=produit)
            serializer = DelaisApprovisionnementSerializer(lead_time)
            return Response(serializer.data)
        except DelaisApprovisionnement.DoesNotExist:
            return Response(
                {'error': 'No lead time data found'},
                status=status.HTTP_404_NOT_FOUND
            )

    # -----------------------------------------------------------------------
    # UPDATE OPERATIONS
    # -----------------------------------------------------------------------

    def update(self, request, *args, **kwargs):
        """
        PUT /produits/{id}/
        Update SKU completely
        """
        return super().update(request, *args, **kwargs)

    def partial_update(self, request, *args, **kwargs):
        """
        PATCH /produits/{id}/
        Partially update SKU
        """
        return super().partial_update(request, *args, **kwargs)

    @action(detail=True, methods=['post'])
    def update_weight(self, request, id_produit=None):
        """
        POST /produits/{id}/update-weight/
        Update SKU weight
        Body: { "weight": 2.5 }
        """
        produit = self.get_object()
        # Note: weight is not in current model, add if needed
        return Response(
            {'message': 'Weight field not implemented in current model'},
            status=status.HTTP_400_BAD_REQUEST
        )

    @action(detail=True, methods=['post'])
    def set_replenishment_policy(self, request, id_produit=None):
        """
        POST /produits/{id}/set-replenishment-policy/
        Set/update replenishment policy
        Body: { "stock_securite": 100, "quantite_min_commande": 50, "taille_lot": 200 }
        """
        produit = self.get_object()

        try:
            policy, created = PolitiqueReapprovisionnement.objects.get_or_create(
                id_produit=produit
            )

            if 'stock_securite' in request.data:
                policy.stock_securite = request.data['stock_securite']
            if 'quantite_min_commande' in request.data:
                policy.quantite_min_commande = request.data['quantite_min_commande']
            if 'taille_lot' in request.data:
                policy.taille_lot = request.data['taille_lot']

            policy.save()

            serializer = PolitiqueReapprovisionnementSerializer(policy)
            return Response(serializer.data)
        except Exception as e:
            return Response(
                {'error': f'Error updating policy: {str(e)}'},
                status=status.HTTP_400_BAD_REQUEST
            )

    # -----------------------------------------------------------------------
    # DELETE/DEACTIVATE OPERATIONS
    # -----------------------------------------------------------------------

    def destroy(self, request, *args, **kwargs):
        """
        DELETE /produits/{id}/
        Deactivate SKU (logical delete)
        """
        produit = self.get_object()
        produit.actif = False
        produit.save()

        return Response(
            {'message': 'SKU deactivated successfully'},
            status=status.HTTP_200_OK
        )


# ============================================================================
# BARCODE CRUD
# ============================================================================

class CodeBarresProduitViewSet(viewsets.ModelViewSet):
    """
    Barcode Management

    API Endpoints:
    - GET    /barcodes/                      - List all barcodes
    - POST   /barcodes/                      - Create new barcode
    - GET    /barcodes/{barcode}/            - Get barcode details
    - PUT    /barcodes/{barcode}/            - Update barcode
    - DELETE /barcodes/{barcode}/            - Delete barcode

    Custom Endpoints:
    - GET    /barcodes/by-sku/{sku_id}/      - Get barcodes by SKU
    - POST   /barcodes/{barcode}/set-primary/ - Set as primary barcode
    """

    queryset = CodeBarresProduit.objects.all()
    serializer_class = CodeBarresProduitSerializer
    lookup_field = 'code_barres'
    permission_classes = [AllowAny]  # Changed from IsAuthenticated for development

    @action(detail=True, methods=['post'])
    def set_primary(self, request, code_barres=None):
        """
        POST /barcodes/{barcode}/set-primary/
        Set barcode as primary for its SKU
        """
        barcode = self.get_object()
        produit = barcode.id_produit

        # Unmark all others as primary
        CodeBarresProduit.objects.filter(
            id_produit=produit,
            principal=True
        ).update(principal=False)

        # Mark this as primary
        barcode.principal = True
        barcode.save()

        serializer = self.get_serializer(barcode)
        return Response(serializer.data)


# ============================================================================
# PURCHASE ORDERS CRUD
# ============================================================================

class CmdAchatViewSet(viewsets.ModelViewSet):
    """
    Purchase Orders Management

    API Endpoints:
    - GET    /purchase-orders/                           - List all purchase orders
    - POST   /purchase-orders/                           - Create new purchase order
    - GET    /purchase-orders/{id}/                      - Get purchase order
    - PUT    /purchase-orders/{id}/                      - Update purchase order
    - DELETE /purchase-orders/{id}/                      - Cancel purchase order

    Custom Endpoints:
    - GET    /purchase-orders/open/                      - Get open purchase orders
    - GET    /purchase-orders/by-sku/{sku_id}/          - Get POs for SKU
    - POST   /purchase-orders/{id}/mark-received/       - Mark PO as received
    - POST   /purchase-orders/{id}/mark-delivered/      - Mark PO as delivered
    """

    queryset = cmd_achat_ouvertes_opt.objects.all()
    serializer_class = CmdAchatSerializer
    lookup_field = 'id_commande_achat'
    permission_classes = [AllowAny]  # Changed from IsAuthenticated for development

    def create(self, request, *args, **kwargs):
        """
        POST /purchase-orders/
        Create new purchase order
        """
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            po = serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['get'])
    def open(self, request):
        """
        GET /purchase-orders/open/
        Get all open purchase orders
        """
        po_list = cmd_achat_ouvertes_opt.objects.filter(
            statut__in=['OPEN', 'PARTIALLY_RECEIVED']
        )
        serializer = self.get_serializer(po_list, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def mark_received(self, request, id_commande_achat=None):
        """
        POST /purchase-orders/{id}/mark-received/
        Mark PO as received (full or partial)
        Body: { "quantity_received": 100 }
        """
        po = self.get_object()
        quantity_received = request.data.get('quantity_received', po.quantite_commandee)

        if quantity_received == po.quantite_commandee:
            po.statut = 'COMPLETED'
        else:
            po.statut = 'PARTIALLY_RECEIVED'

        po.save()

        serializer = self.get_serializer(po)
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def cancel(self, request, id_commande_achat=None):
        """
        POST /purchase-orders/{id}/cancel/
        Cancel purchase order
        """
        po = self.get_object()
        po.statut = 'CANCELLED'
        po.save()

        return Response(
            {'message': 'Purchase order cancelled'},
            status=status.HTTP_200_OK
        )


# ============================================================================
# DEMAND HISTORY CRUD
# ============================================================================

class HistoriqueDemandeViewSet(viewsets.ModelViewSet):
    """
    Demand History Management

    API Endpoints:
    - GET    /demand-history/                        - List all demand records
    - POST   /demand-history/                        - Create new demand record
    - GET    /demand-history/{id}/                   - Get demand record by ID
    - PUT    /demand-history/{id}/                   - Update demand record
    - PATCH  /demand-history/{id}/                   - Partially update demand record
    - DELETE /demand-history/{id}/                   - Delete demand record

    Custom Endpoints:
    - GET    /demand-history/by-product/?product_id=SKU001  - Get demand for product
    - GET    /demand-history/by-date-range/?start=2026-01-01&end=2026-02-01 - Date range query
    - GET    /demand-history/average-demand/?product_id=SKU001&days=30 - Calculate average demand
    """

    queryset = HistoriqueDemande.objects.all()
    serializer_class = HistoriqueDemandeSerializer
    permission_classes = [AllowAny]  # Changed from IsAuthenticated for development

    @action(detail=False, methods=['get'])
    def by_product(self, request):
        """
        GET /demand-history/by-product/?product_id=SKU001
        Get all demand records for a specific product
        """
        product_id = request.query_params.get('product_id')
        if not product_id:
            return Response(
                {'error': 'product_id parameter is required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            produit = Produit.objects.get(id_produit=product_id)
            historique = HistoriqueDemande.objects.filter(id_produit=produit)
            serializer = self.get_serializer(historique, many=True)
            return Response(serializer.data)
        except Produit.DoesNotExist:
            return Response(
                {'error': 'Product not found'},
                status=status.HTTP_404_NOT_FOUND
            )

    @action(detail=False, methods=['get'])
    def by_date_range(self, request):
        """
        GET /demand-history/by-date-range/?start=2026-01-01&end=2026-02-01
        Get demand records within a date range
        """
        start_date = request.query_params.get('start')
        end_date = request.query_params.get('end')

        if not start_date or not end_date:
            return Response(
                {'error': 'start and end date parameters are required (YYYY-MM-DD)'},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            historique = HistoriqueDemande.objects.filter(
                date__gte=start_date,
                date__lte=end_date
            ).order_by('date')
            serializer = self.get_serializer(historique, many=True)
            return Response(serializer.data)
        except Exception as e:
            return Response(
                {'error': f'Invalid date format: {str(e)}'},
                status=status.HTTP_400_BAD_REQUEST
            )

    @action(detail=False, methods=['get'])
    def average_demand(self, request):
        """
        GET /demand-history/average-demand/?product_id=SKU001&days=30
        Calculate average daily demand for a product over N days
        """
        product_id = request.query_params.get('product_id')
        days = request.query_params.get('days', 30)

        if not product_id:
            return Response(
                {'error': 'product_id parameter is required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            days = int(days)
            produit = Produit.objects.get(id_produit=product_id)
            from datetime import timedelta
            start_date = timezone.now().date() - timedelta(days=days)

            demand_data = HistoriqueDemande.objects.filter(
                id_produit=produit,
                date__gte=start_date
            )

            total_demand = demand_data.aggregate(Sum('quantite_demande'))['quantite_demande__sum'] or 0
            count = demand_data.count()
            average = total_demand / days if days > 0 else 0

            return Response({
                'product_id': product_id,
                'period_days': days,
                'total_demand': float(total_demand),
                'record_count': count,
                'average_daily_demand': float(average),
                'start_date': start_date,
                'end_date': timezone.now().date()
            })
        except Produit.DoesNotExist:
            return Response(
                {'error': 'Product not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        except ValueError:
            return Response(
                {'error': 'days parameter must be an integer'},
                status=status.HTTP_400_BAD_REQUEST
            )


# ============================================================================
# SUPPLIER LEAD TIME CRUD
# ============================================================================

class DelaisApprovisionnementViewSet(viewsets.ModelViewSet):
    """
    Supplier Lead Time Management

    API Endpoints:
    - GET    /supplier-lead-times/                    - List all lead times
    - POST   /supplier-lead-times/                    - Create new lead time
    - GET    /supplier-lead-times/{id}/               - Get lead time by ID
    - PUT    /supplier-lead-times/{id}/               - Update lead time
    - PATCH  /supplier-lead-times/{id}/               - Partially update lead time
    - DELETE /supplier-lead-times/{id}/               - Delete lead time

    Custom Endpoints:
    - GET    /supplier-lead-times/by-product/?product_id=SKU001 - Get lead time for product
    - POST   /supplier-lead-times/{id}/update-delay/ - Update lead time in days
    """

    queryset = DelaisApprovisionnement.objects.all()
    serializer_class = DelaisApprovisionnementSerializer
    lookup_field = 'id_produit'
    permission_classes = [AllowAny]  # Changed from IsAuthenticated for development

    @action(detail=False, methods=['get'])
    def by_product(self, request):
        """
        GET /supplier-lead-times/by-product/?product_id=SKU001
        Get lead time for a specific product
        """
        product_id = request.query_params.get('product_id')
        if not product_id:
            return Response(
                {'error': 'product_id parameter is required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            lead_time = DelaisApprovisionnement.objects.get(id_produit=product_id)
            serializer = self.get_serializer(lead_time)
            return Response(serializer.data)
        except DelaisApprovisionnement.DoesNotExist:
            return Response(
                {'error': 'Lead time not found for this product'},
                status=status.HTTP_404_NOT_FOUND
            )

    @action(detail=True, methods=['post'])
    def update_delay(self, request, id_produit=None):
        """
        POST /supplier-lead-times/{id}/update-delay/
        Update the lead time in days
        Body: { "delai_jours": 14 }
        """
        lead_time = self.get_object()
        new_delay = request.data.get('delai_jours')

        if new_delay is None:
            return Response(
                {'error': 'delai_jours is required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            new_delay = int(new_delay)
            if new_delay < 0:
                return Response(
                    {'error': 'Lead time cannot be negative'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            lead_time.delai_jours = new_delay
            lead_time.save()

            return Response({
                'message': 'Lead time updated successfully',
                'product_id': lead_time.id_produit.id_produit,
                'delai_jours': lead_time.delai_jours
            })
        except ValueError:
            return Response(
                {'error': 'delai_jours must be an integer'},
                status=status.HTTP_400_BAD_REQUEST
            )


# ============================================================================
# REPLENISHMENT POLICY CRUD
# ============================================================================

class PolitiqueReapprovisionnementViewSet(viewsets.ModelViewSet):
    """
    Replenishment Policy Management

    API Endpoints:
    - GET    /replenishment-policies/                 - List all policies
    - POST   /replenishment-policies/                 - Create new policy
    - GET    /replenishment-policies/{id}/            - Get policy by ID
    - PUT    /replenishment-policies/{id}/            - Update policy
    - PATCH  /replenishment-policies/{id}/            - Partially update policy
    - DELETE /replenishment-policies/{id}/            - Delete policy

    Custom Endpoints:
    - GET    /replenishment-policies/by-product/?product_id=SKU001 - Get policy for product
    - POST   /replenishment-policies/{id}/update-security-stock/ - Update security stock
    - POST   /replenishment-policies/{id}/update-min-order/ - Update minimum order quantity
    - POST   /replenishment-policies/{id}/update-lot-size/ - Update lot size
    """

    queryset = PolitiqueReapprovisionnement.objects.all()
    serializer_class = PolitiqueReapprovisionnementSerializer
    lookup_field = 'id_produit'
    permission_classes = [AllowAny]  # Changed from IsAuthenticated for development

    @action(detail=False, methods=['get'])
    def by_product(self, request):
        """
        GET /replenishment-policies/by-product/?product_id=SKU001
        Get replenishment policy for a specific product
        """
        product_id = request.query_params.get('product_id')
        if not product_id:
            return Response(
                {'error': 'product_id parameter is required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            policy = PolitiqueReapprovisionnement.objects.get(id_produit=product_id)
            serializer = self.get_serializer(policy)
            return Response(serializer.data)
        except PolitiqueReapprovisionnement.DoesNotExist:
            return Response(
                {'error': 'Policy not found for this product'},
                status=status.HTTP_404_NOT_FOUND
            )

    @action(detail=True, methods=['post'])
    def update_security_stock(self, request, id_produit=None):
        """
        POST /replenishment-policies/{id}/update-security-stock/
        Update safety stock level
        Body: { "stock_securite": 100 }
        """
        policy = self.get_object()
        stock_securite = request.data.get('stock_securite')

        if stock_securite is None:
            return Response(
                {'error': 'stock_securite is required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            stock_securite = float(stock_securite)
            if stock_securite < 0:
                return Response(
                    {'error': 'Security stock cannot be negative'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            policy.stock_securite = stock_securite
            policy.save()

            return Response({
                'message': 'Security stock updated successfully',
                'product_id': policy.id_produit.id_produit,
                'stock_securite': float(policy.stock_securite)
            })
        except ValueError:
            return Response(
                {'error': 'stock_securite must be a number'},
                status=status.HTTP_400_BAD_REQUEST
            )

    @action(detail=True, methods=['post'])
    def update_min_order(self, request, id_produit=None):
        """
        POST /replenishment-policies/{id}/update-min-order/
        Update minimum order quantity
        Body: { "quantite_min_commande": 50 }
        """
        policy = self.get_object()
        quantite_min = request.data.get('quantite_min_commande')

        if quantite_min is None:
            return Response(
                {'error': 'quantite_min_commande is required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            quantite_min = float(quantite_min)
            if quantite_min < 0:
                return Response(
                    {'error': 'Minimum order quantity cannot be negative'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            policy.quantite_min_commande = quantite_min
            policy.save()

            return Response({
                'message': 'Minimum order quantity updated successfully',
                'product_id': policy.id_produit.id_produit,
                'quantite_min_commande': float(policy.quantite_min_commande)
            })
        except ValueError:
            return Response(
                {'error': 'quantite_min_commande must be a number'},
                status=status.HTTP_400_BAD_REQUEST
            )

    @action(detail=True, methods=['post'])
    def update_lot_size(self, request, id_produit=None):
        """
        POST /replenishment-policies/{id}/update-lot-size/
        Update lot size
        Body: { "taille_lot": 200 }
        """
        policy = self.get_object()
        taille_lot = request.data.get('taille_lot')

        if taille_lot is None:
            return Response(
                {'error': 'taille_lot is required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            taille_lot = float(taille_lot)
            if taille_lot < 0:
                return Response(
                    {'error': 'Lot size cannot be negative'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            policy.taille_lot = taille_lot
            policy.save()

            return Response({
                'message': 'Lot size updated successfully',
                'product_id': policy.id_produit.id_produit,
                'taille_lot': float(policy.taille_lot)
            })
        except ValueError:
            return Response(
                {'error': 'taille_lot must be a number'},
                status=status.HTTP_400_BAD_REQUEST
            )
