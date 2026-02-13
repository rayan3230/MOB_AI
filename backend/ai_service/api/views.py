import os
import json
from django.shortcuts import render
from django.http import JsonResponse
from django.conf import settings
from django.views.decorators.csrf import csrf_exempt
from ai_service.logic.forecasting_service import ForecastingService

# Initialize the service once (or on demand)
EXCEL_PATH = os.path.join(settings.BASE_DIR, 'ai_service', 'data', 'WMS_Hackathon_DataPack_Templates_FR_FV_B7_ONLY.xlsx')
service = ForecastingService(EXCEL_PATH)

def generate_forecast_all(request):
    """
    Endpoint 1: Generate forecast for all SKUs (limited to 20 for performance in this demo)
    """
    try:
        limit = int(request.GET.get('limit', 20))
        order_obj = service.run(limit_products=limit)
        return JsonResponse({
            'status': 'success',
            'order': order_obj
        })
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=500)

def generate_forecast_sku(request, sku_id):
    """
    Endpoint 2: Generate forecast for specific SKU
    """
    try:
        result = service.get_sku_forecast(sku_id)
        if result:
            return JsonResponse({
                'status': 'success',
                'forecast': result
            })
        else:
            return JsonResponse({'status': 'error', 'message': f'SKU {sku_id} not found or insufficient history.'}, status=404)
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=500)

def get_explanation(request, sku_id):
    """
    Endpoint 3: Return explanation for supervisor dashboard
    """
    try:
        result = service.get_sku_forecast(sku_id)
        if result:
            return JsonResponse({
                'status': 'success',
                'sku_id': sku_id,
                'explanation': result['explanation'],
                'model_logic': {
                    'sma': result['sma'],
                    'regression': result['regression'],
                    'trend': result['trend'],
                    'volatility': result['volatility']
                }
            })
        else:
            return JsonResponse({'status': 'error', 'message': f'SKU {sku_id} not found.'}, status=404)
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=500)

@csrf_exempt
def validate_order(request):
    """
    Endpoint 4: Supervisor Validation & Override
    Demonstrates human-in-the-loop and auditability.
    """
    if request.method != 'POST':
        return JsonResponse({'status': 'error', 'message': 'Only POST allowed.'}, status=405)
    
    try:
        data = json.loads(request.body)
        order_obj = data.get('order')
        sku_id = data.get('sku_id')
        override_qty = data.get('override_qty')
        justification = data.get('justification')

        updated_order = service.order_service.validate_order(
            order_obj, 
            sku_id=sku_id, 
            override_qty=override_qty, 
            justification=justification
        )
        
        return JsonResponse({
            'status': 'success',
            'order': updated_order
        })
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=500)
