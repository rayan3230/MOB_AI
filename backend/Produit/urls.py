from django.urls import path, include
from rest_framework.routers import SimpleRouter
from .views import (
    ProduitViewSet,
    CodeBarresProduitViewSet,
    CmdAchatViewSet,
    HistoriqueDemandeViewSet,
    DelaisApprovisionnementViewSet,
    PolitiqueReapprovisionnementViewSet,
)

router = SimpleRouter()
router.register(r'produits', ProduitViewSet, basename='produit')
router.register(r'barcodes', CodeBarresProduitViewSet, basename='barcode')
router.register(r'purchase-orders', CmdAchatViewSet, basename='purchase-order')
router.register(r'demand-history', HistoriqueDemandeViewSet, basename='demand-history')
router.register(r'supplier-lead-times', DelaisApprovisionnementViewSet, basename='supplier-lead-time')
router.register(r'replenishment-policies', PolitiqueReapprovisionnementViewSet, basename='replenishment-policy')

urlpatterns = [
    path('', include(router.urls)),
]
