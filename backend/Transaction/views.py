# ============================================================================
# TRANSACTION MODULE - API VIEWS
# ============================================================================
# This module handles all warehouse transaction operations including:
# - Receipt of new inventory
# - Internal transfers between locations
# - Stock adjustments and issues
# - Complete transaction lifecycle management
#
# REST API Routes:
#   Base: /api/transaction-management/      - Manage transactions
#   Base: /api/transaction-line-items/      - Manage line items within transactions
#
# Authentication: All endpoints require user authentication (IsAuthenticated)
# ============================================================================

from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from django.db.models import Count, Q
from django.utils import timezone
from datetime import timedelta

from .models import Transaction, LigneTransaction
from .serializers import (
    TransactionListSerializer,
    TransactionDetailSerializer,
    TransactionCreateUpdateSerializer,
    LigneTransactionDetailSerializer,
    LigneTransactionSimpleSerializer
)


# ============================================================================
# TRANSACTION MANAGEMENT VIEWSET
# ============================================================================
# Purpose: Manage all warehouse transactions (receipts, transfers, issues, adjustments)
# Main Features:
#   - CRUD operations for transactions
#   - Filter transactions by type, status, creator, or date range
#   - Track transaction lifecycle (pending → confirmed → completed)
#   - Retrieve associated line items and creator information
#   - Generate transaction statistics and trends
# Status Values: PENDING, CONFIRMED, COMPLETED, CANCELLED
# Type Values: RECEIPT, TRANSFER, ISSUE, ADJUSTMENT
# ============================================================================
class TransactionViewSet(viewsets.ModelViewSet):
    """
    Complete Transaction Management

    CRUD Operations:
    - GET    /transaction-management/                      - List all transactions
    - POST   /transaction-management/                      - Create new transaction
    - GET    /transaction-management/{id}/                 - Get transaction details
    - PUT    /transaction-management/{id}/                 - Update transaction
    - PATCH  /transaction-management/{id}/                 - Partial update
    - DELETE /transaction-management/{id}/                 - Delete transaction

    Filter & Query Actions:
    - GET    /transaction-management/filter_by_type/?type=RECEIPT
    - GET    /transaction-management/filter_by_status/?status=PENDING
    - GET    /transaction-management/filter_by_creator/?user_id=USR001
    - GET    /transaction-management/filter_by_date_range/?start=2026-01-01&end=2026-02-01
    - GET    /transaction-management/transaction_statistics/

    Status Actions:
    - POST   /transaction-management/{id}/confirm_transaction/
    - POST   /transaction-management/{id}/complete_transaction/
    - POST   /transaction-management/{id}/cancel_transaction/
    """
    queryset = Transaction.objects.all()
    lookup_field = 'id_transaction'
    permission_classes = [AllowAny]  # Changed from IsAuthenticated for development

    def get_serializer_class(self):
        """Use different serializers based on action"""
        if self.action == 'retrieve':
            return TransactionDetailSerializer
        elif self.action == 'list':
            return TransactionListSerializer
        elif self.action in ['create', 'update', 'partial_update']:
            return TransactionCreateUpdateSerializer
        return TransactionDetailSerializer

    @action(detail=False, methods=['get'])
    def filter_by_type(self, request):
        """
        GET /transaction-management/filter_by_type/?type=RECEIPT
        Get transactions filtered by type (RECEIPT, TRANSFER, ISSUE, ADJUSTMENT)
        """
        transaction_type = request.query_params.get('type')
        if not transaction_type:
            return Response(
                {'error': 'type parameter is required (RECEIPT, TRANSFER, ISSUE, ADJUSTMENT)'},
                status=status.HTTP_400_BAD_REQUEST
            )

        valid_types = ['RECEIPT', 'TRANSFER', 'ISSUE', 'ADJUSTMENT']
        if transaction_type not in valid_types:
            return Response(
                {'error': f'Invalid type. Must be one of: {", ".join(valid_types)}'},
                status=status.HTTP_400_BAD_REQUEST
            )

        transactions = Transaction.objects.filter(type_transaction=transaction_type).order_by('-cree_le')
        serializer = self.get_serializer(transactions, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def filter_by_status(self, request):
        """
        GET /transaction-management/filter_by_status/?status=PENDING
        Get transactions filtered by status (PENDING, CONFIRMED, COMPLETED, CANCELLED)
        """
        transaction_status = request.query_params.get('status')
        if not transaction_status:
            return Response(
                {'error': 'status parameter is required (PENDING, CONFIRMED, COMPLETED, CANCELLED)'},
                status=status.HTTP_400_BAD_REQUEST
            )

        valid_statuses = ['PENDING', 'CONFIRMED', 'COMPLETED', 'CANCELLED']
        if transaction_status not in valid_statuses:
            return Response(
                {'error': f'Invalid status. Must be one of: {", ".join(valid_statuses)}'},
                status=status.HTTP_400_BAD_REQUEST
            )

        transactions = Transaction.objects.filter(statut=transaction_status).order_by('-cree_le')
        serializer = self.get_serializer(transactions, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def filter_by_creator(self, request):
        """
        GET /transaction-management/filter_by_creator/?user_id=USR001
        Get all transactions created by a specific user
        """
        user_id = request.query_params.get('user_id')
        if not user_id:
            return Response(
                {'error': 'user_id parameter is required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        transactions = Transaction.objects.filter(cree_par_id_utilisateur__id_utilisateur=user_id).order_by('-cree_le')
        if not transactions.exists():
            return Response(
                {'message': 'No transactions found for this user'},
                status=status.HTTP_404_NOT_FOUND
            )

        serializer = self.get_serializer(transactions, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def filter_by_date_range(self, request):
        """
        GET /transaction-management/filter_by_date_range/?start=2026-01-01&end=2026-02-01
        Get transactions within a date range
        """
        start_date = request.query_params.get('start')
        end_date = request.query_params.get('end')

        if not start_date or not end_date:
            return Response(
                {'error': 'start and end date parameters are required (YYYY-MM-DD)'},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            transactions = Transaction.objects.filter(
                cree_le__date__gte=start_date,
                cree_le__date__lte=end_date
            ).order_by('-cree_le')
            serializer = self.get_serializer(transactions, many=True)
            return Response(serializer.data)
        except Exception as e:
            return Response(
                {'error': f'Invalid date format: {str(e)}'},
                status=status.HTTP_400_BAD_REQUEST
            )

    @action(detail=False, methods=['get'])
    def transaction_statistics(self, request):
        """
        GET /transaction-management/transaction_statistics/
        Get transaction statistics (counts by type and status)
        """
        total_transactions = Transaction.objects.count()

        by_type = {}
        for trans_type in ['RECEIPT', 'TRANSFER', 'ISSUE', 'ADJUSTMENT']:
            by_type[trans_type] = Transaction.objects.filter(type_transaction=trans_type).count()

        by_status = {}
        for stat in ['PENDING', 'CONFIRMED', 'COMPLETED', 'CANCELLED']:
            by_status[stat] = Transaction.objects.filter(statut=stat).count()

        today = timezone.now().date()
        last_7_days = today - timedelta(days=7)
        recent_transactions = Transaction.objects.filter(cree_le__date__gte=last_7_days).count()

        return Response({
            'total_transactions': total_transactions,
            'by_type': by_type,
            'by_status': by_status,
            'recent_transactions_7_days': recent_transactions,
            'date_calculated': timezone.now()
        })

    @action(detail=True, methods=['post'])
    def confirm_transaction(self, request, id_transaction=None):
        """
        POST /transaction-management/{id}/confirm_transaction/
        Change transaction status from PENDING to CONFIRMED
        """
        transaction = self.get_object()

        if transaction.statut != 'PENDING':
            return Response(
                {'error': f'Cannot confirm transaction with status {transaction.statut}'},
                status=status.HTTP_400_BAD_REQUEST
            )

        transaction.statut = 'CONFIRMED'
        transaction.save()

        return Response({
            'message': 'Transaction confirmed successfully',
            'id_transaction': transaction.id_transaction,
            'statut': transaction.statut
        }, status=status.HTTP_200_OK)

    @action(detail=True, methods=['post'])
    def complete_transaction(self, request, id_transaction=None):
        """
        POST /transaction-management/{id}/complete_transaction/
        Mark transaction as COMPLETED
        """
        transaction = self.get_object()

        if transaction.statut == 'CANCELLED':
            return Response(
                {'error': 'Cannot complete a cancelled transaction'},
                status=status.HTTP_400_BAD_REQUEST
            )

        transaction.statut = 'COMPLETED'
        transaction.save()

        return Response({
            'message': 'Transaction completed successfully',
            'id_transaction': transaction.id_transaction,
            'statut': transaction.statut
        }, status=status.HTTP_200_OK)

    @action(detail=True, methods=['post'])
    def cancel_transaction(self, request, id_transaction=None):
        """
        POST /transaction-management/{id}/cancel_transaction/
        Cancel a transaction
        """
        transaction = self.get_object()

        if transaction.statut == 'COMPLETED':
            return Response(
                {'error': 'Cannot cancel a completed transaction'},
                status=status.HTTP_400_BAD_REQUEST
            )

        transaction.statut = 'CANCELLED'
        transaction.save()

        return Response({
            'message': 'Transaction cancelled successfully',
            'id_transaction': transaction.id_transaction,
            'statut': transaction.statut
        }, status=status.HTTP_200_OK)


# ============================================================================
# TRANSACTION LINE ITEMS VIEWSET
# ============================================================================
# Purpose: Manage detailed line items within each transaction
# Main Features:
#   - CRUD operations for individual line items (products and quantities)
#   - Link products to their source and destination locations
#   - Filter line items by transaction, product, quantity range, or lot number
#   - Retrieve product and location details for each line item
#   - Generate summaries of line items per transaction (count and total quantity)
# Key Relations: Each line connects a product, transaction, and two locations
# Line Item Attributes: quantity, product SKU, lot/serial numbers, source/destination
# ============================================================================
class LigneTransactionViewSet(viewsets.ModelViewSet):
    """
    Transaction Line Items Management

    CRUD Operations:
    - GET    /transaction-line-items/                - List all line items
    - POST   /transaction-line-items/                - Create new line item
    - GET    /transaction-line-items/{id}/           - Get line item details
    - PUT    /transaction-line-items/{id}/           - Update line item
    - PATCH  /transaction-line-items/{id}/           - Partial update
    - DELETE /transaction-line-items/{id}/           - Delete line item

    Filter & Query Actions:
    - GET    /transaction-line-items/filter_by_transaction/?transaction_id=TX001
    - GET    /transaction-line-items/filter_by_product/?product_id=SKU001
    - GET    /transaction-line-items/filter_by_quantity_range/?min=10&max=100
    - GET    /transaction-line-items/filter_by_lot_number/?lot_serie=LOT123
    """
    queryset = LigneTransaction.objects.all()
    permission_classes = [AllowAny]  # Changed from IsAuthenticated for development

    def get_serializer_class(self):
        """Use different serializers based on action"""
        if self.action in ['create', 'update', 'partial_update']:
            return LigneTransactionSimpleSerializer
        return LigneTransactionDetailSerializer

    @action(detail=False, methods=['get'])
    def filter_by_transaction(self, request):
        """
        GET /transaction-line-items/filter_by_transaction/?transaction_id=TX001
        Get all line items for a specific transaction
        """
        transaction_id = request.query_params.get('transaction_id')
        if not transaction_id:
            return Response(
                {'error': 'transaction_id parameter is required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        lignes = LigneTransaction.objects.filter(id_transaction__id_transaction=transaction_id).order_by('no_ligne')
        if not lignes.exists():
            return Response(
                {'message': 'No line items found for this transaction'},
                status=status.HTTP_404_NOT_FOUND
            )

        serializer = self.get_serializer(lignes, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def filter_by_product(self, request):
        """
        GET /transaction-line-items/filter_by_product/?product_id=SKU001
        Get all line items for a specific product
        """
        product_id = request.query_params.get('product_id')
        if not product_id:
            return Response(
                {'error': 'product_id parameter is required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        lignes = LigneTransaction.objects.filter(id_produit__id_produit=product_id).order_by('-id_transaction__cree_le')
        if not lignes.exists():
            return Response(
                {'message': 'No line items found for this product'},
                status=status.HTTP_404_NOT_FOUND
            )

        serializer = self.get_serializer(lignes, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def filter_by_quantity_range(self, request):
        """
        GET /transaction-line-items/filter_by_quantity_range/?min=10&max=100
        Get line items filtered by quantity range
        """
        min_qty = request.query_params.get('min')
        max_qty = request.query_params.get('max')

        if not min_qty or not max_qty:
            return Response(
                {'error': 'min and max parameters are required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            min_qty = float(min_qty)
            max_qty = float(max_qty)

            if min_qty > max_qty:
                return Response(
                    {'error': 'min quantity cannot be greater than max'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            lignes = LigneTransaction.objects.filter(
                quantite__gte=min_qty,
                quantite__lte=max_qty
            ).order_by('-quantite')

            serializer = self.get_serializer(lignes, many=True)
            return Response(serializer.data)
        except ValueError:
            return Response(
                {'error': 'min and max must be numeric values'},
                status=status.HTTP_400_BAD_REQUEST
            )

    @action(detail=False, methods=['get'])
    def filter_by_lot_number(self, request):
        """
        GET /transaction-line-items/filter_by_lot_number/?lot_serie=LOT123
        Get all line items for a specific lot/serial number
        """
        lot_serie = request.query_params.get('lot_serie')
        if not lot_serie:
            return Response(
                {'error': 'lot_serie parameter is required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        lignes = LigneTransaction.objects.filter(lot_serie=lot_serie).order_by('-id_transaction__cree_le')
        if not lignes.exists():
            return Response(
                {'message': 'No line items found for this lot'},
                status=status.HTTP_404_NOT_FOUND
            )

        serializer = self.get_serializer(lignes, many=True)
        return Response(serializer.data)
