from django.urls import path, include
from rest_framework.routers import SimpleRouter
from .views import (
    EntrepotViewSet,
    NiveauStockageViewSet,
    NiveauPickingViewSet,
    EmplacementViewSet,
    StockViewSet,
    VrackViewSet,
    MouvementStockViewSet,
    ChariotViewSet,
    ChariotOperationViewSet,
    CommandeViewSet,
    LigneCommandeViewSet,
    ResultatLivraisonViewSet,
    OperationViewSet,
    PrevisionIAViewSet,
    AssignmentStockageIAViewSet,
    RoutePickingIAViewSet,
    OverrideViewSet,
    JournalAuditViewSet,
    OperationOfflineViewSet,
    AnomalieDetectionViewSet,
)

router = SimpleRouter()
router.register(r'warehouses', EntrepotViewSet, basename='warehouse')
router.register(r'floors', NiveauStockageViewSet, basename='floor')
router.register(r'picking-floors', NiveauPickingViewSet, basename='picking-floor')
router.register(r'locations', EmplacementViewSet, basename='location')
router.register(r'stock', StockViewSet, basename='stock')
router.register(r'vracks', VrackViewSet, basename='vrack')
router.register(r'stock-movements', MouvementStockViewSet, basename='stock-movement')
router.register(r'chariots', ChariotViewSet, basename='chariot')
router.register(r'chariot-operations', ChariotOperationViewSet, basename='chariot-operation')
router.register(r'orders', CommandeViewSet, basename='order')
router.register(r'order-lines', LigneCommandeViewSet, basename='order-line')
router.register(r'deliveries', ResultatLivraisonViewSet, basename='delivery')
router.register(r'operations', OperationViewSet, basename='operation')
router.register(r'forecasts', PrevisionIAViewSet, basename='forecast')
router.register(r'storage-assignments', AssignmentStockageIAViewSet, basename='storage-assignment')
router.register(r'picking-routes', RoutePickingIAViewSet, basename='picking-route')
router.register(r'overrides', OverrideViewSet, basename='override')
router.register(r'audit-logs', JournalAuditViewSet, basename='audit-log')
router.register(r'sync-queue', OperationOfflineViewSet, basename='sync-queue')
router.register(r'anomalies', AnomalieDetectionViewSet, basename='anomaly')

urlpatterns = [
    path('', include(router.urls)),
]
