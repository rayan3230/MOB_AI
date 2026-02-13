# ============================================================================
# TRANSACTION MODULE - URL ROUTING
# ============================================================================
# This module configures API endpoints for transaction management
#
# ViewSets Registered:
#   1. TransactionViewSet - CRUD operations and filtering for transactions
#      Base URL: /transaction-management/
#      Methods: GET (list, retrieve), POST (create), PUT/PATCH (update), DELETE
#      Actions: filter_by_type, filter_by_status, filter_by_creator, 
#               filter_by_date_range, transaction_statistics,
#               confirm_transaction, complete_transaction, cancel_transaction
#
#   2. LigneTransactionViewSet - CRUD operations for transaction line items
#      Base URL: /transaction-line-items/
#      Methods: GET (list, retrieve), POST (create), PUT/PATCH (update), DELETE
#      Actions: filter_by_transaction, filter_by_product,
#               filter_by_quantity_range, filter_by_lot_number
#
# Example Requests:
#   GET  /api/transaction-management/                          - List all transactions
#   POST /api/transaction-management/                          - Create new transaction
#   GET  /api/transaction-management/{id}/                     - Get transaction details
#   GET  /api/transaction-management/filter_by_type/?type=RECEIPT
#   GET  /api/transaction-management/filter_by_status/?status=PENDING
#   GET  /api/transaction-line-items/                          - List all line items
#   POST /api/transaction-line-items/                          - Create new line item
#   GET  /api/transaction-line-items/filter_by_transaction/?transaction_id=TX001
# ============================================================================

from django.urls import path, include
from rest_framework.routers import SimpleRouter
from .views import (
    TransactionViewSet,
    LigneTransactionViewSet,
)

router = SimpleRouter()
router.register(r'transaction-management', TransactionViewSet, basename='transaction-management')
router.register(r'transaction-line-items', LigneTransactionViewSet, basename='transaction-line-items')

urlpatterns = [
    path('', include(router.urls)),
]
