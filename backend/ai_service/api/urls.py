from django.urls import path
from . import views

urlpatterns = [
    path('all/', views.generate_forecast_all, name='forecast_all'),
    path('trigger-tomorrow/', views.trigger_preparation_tomorrow, name='trigger_tomorrow'),
    path('sku/<int:sku_id>/', views.generate_forecast_sku, name='forecast_sku'),
    path('explanation/<int:sku_id>/', views.get_explanation, name='forecast_explanation'),
    path('validate/', views.validate_order, name='forecast_validate'),
    path('optimize-route/', views.get_optimized_route, name='optimize_route'),
    path('map/<int:floor_idx>/', views.get_warehouse_map, name='warehouse_map'),
    path('zoning/<int:floor_idx>/', views.get_zoning, name='warehouse_zoning'),
    path('record-performance/', views.record_picking_performance, name='record_performance'),
]
