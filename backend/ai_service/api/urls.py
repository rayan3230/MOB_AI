from django.urls import path
from . import views

urlpatterns = [
    path('all/', views.generate_forecast_all, name='forecast_all'),
    path('sku/<int:sku_id>/', views.generate_forecast_sku, name='forecast_sku'),
    path('explanation/<int:sku_id>/', views.get_explanation, name='forecast_explanation'),
    path('validate/', views.validate_order, name='forecast_validate'),
]
