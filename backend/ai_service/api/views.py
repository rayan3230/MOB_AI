import os
import json
from datetime import datetime
from django.shortcuts import render
from django.http import JsonResponse
from django.conf import settings
from django.views.decorators.csrf import csrf_exempt
from .models import AIPerformanceLog
from django.db import models
from Produit.models import Produit
from warhouse.models import Rack, RackProduct
from ai_service.core.forecasting_service import ForecastingService
from ai_service.core.picking_service import PickingOptimizationService
from ai_service.core.storage import StorageOptimizationService
from ai_service.core.product_manager import ProductStorageManager
from ai_service.engine.base import WarehouseCoordinate, Role
from ai_service.maps import GroundFloorMap, IntermediateFloorMap, UpperFloorMap

# Initialize services
# If no data path passed, core/forecasting_service.py's DataLoader will use Supabase/Django ORM
forecast_service = ForecastingService()
pm = ProductStorageManager()

# Initialize Digital Twin Maps (0: RDV/Picking, 1: N1/N2, 2: N3/N4)
floor_maps = {
    0: GroundFloorMap(),
    1: IntermediateFloorMap(floor_index=1),
    2: UpperFloorMap(floor_index=2)
}
picking_service = PickingOptimizationService(floor_maps)
storage_service = StorageOptimizationService(floor_maps, pm)

def generate_forecast_all(request):
    """
    Endpoint 1: Generate forecast for all SKUs (Requirement 8.1 part 1)
    """
    try:
        limit = int(request.GET.get('limit', 20))
        order_obj = forecast_service.run(limit_products=limit)
        return JsonResponse({
            'status': 'success',
            'order': order_obj
        })
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=500)

def trigger_preparation_tomorrow(request):
    """
    Endpoint 5: Trigger preparation one day in advance (Requirement 8.1 part 2)
    Analyzes historical stock and delivery data to predict tomorrow's needs.
    """
    try:
        limit = int(request.GET.get('limit', 20))
        order_obj = forecast_service.trigger_daily_preparation(limit_products=limit)
        return JsonResponse({
            'status': 'success',
            'message': 'Preparation order triggered one day in advance.',
            'order': order_obj
        })
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=500)

def generate_forecast_sku(request, sku_id):
    """
    Endpoint 2: Generate forecast for specific SKU
    """
    try:
        result = forecast_service.get_sku_forecast(sku_id)
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
        result = forecast_service.get_sku_forecast(sku_id)
        if result:
            return JsonResponse({
                'status': 'success',
                'sku_id': sku_id,
                'explanation': result['explanation'],
                'model_logic': {
                    'ses': result['ses'],
                    'regression': result['regression'],
                    'yoy_seasonal': result['yoy_seasonal'],
                    'trend': result['trend'],
                    'volatility': result['volatility'],
                    'demand_class': result['demand_class']
                }
            })
        else:
            return JsonResponse({'status': 'error', 'message': f'SKU {sku_id} not found.'}, status=404)
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=500)

@csrf_exempt
def get_optimized_route(request):
    """
    Endpoint 6: Calculate Optimized Picking Route (Requirement 8.3)
    """
    if request.method != 'POST':
        return JsonResponse({'status': 'error', 'message': 'Only POST allowed.'}, status=405)
    
    try:
        data = json.loads(request.body)
        floor_idx = data.get('floor_idx', 0)
        start_pos = data.get('start_pos', {'x': 0, 'y': 0})
        picks_data = data.get('picks', [])
        role_str = data.get('role', 'SYSTEM')
        
        # Convert role string to Role enum
        try:
            user_role = Role[role_str.upper()]
        except (KeyError, AttributeError):
            user_role = Role.SYSTEM
        
        start_coord = WarehouseCoordinate(start_pos['x'], start_pos['y'])
        picks = [WarehouseCoordinate(p['x'], p['y']) for p in picks_data]
        
        result = picking_service.calculate_picking_route(floor_idx, start_coord, picks, user_role)
        
        # Check if there's an error in the result
        if "error" in result:
            return JsonResponse({
                'status': 'error',
                'message': result['error']
            }, status=400)
        
        # Convert coordinates to JSON-serializable tuples
        def _serialize_point(point):
            if hasattr(point, 'to_tuple'):
                return point.to_tuple()
            if isinstance(point, (tuple, list)) and len(point) >= 2:
                return (point[0], point[1])
            if isinstance(point, dict) and 'x' in point and 'y' in point:
                return (point['x'], point['y'])
            return point

        if "route_sequence" in result and result["route_sequence"]:
            result["route_sequence"] = [_serialize_point(p) for p in result["route_sequence"]]
        
        if "path_segments" in result and result["path_segments"]:
            serialized_segments = []
            for seg in result["path_segments"]:
                if seg:  # Only process non-empty segments
                    serialized_segments.append([_serialize_point(p) for p in seg])
                else:
                    serialized_segments.append([])
            result["path_segments"] = serialized_segments

        return JsonResponse({
            'status': 'success',
            'data': result
        })
    except Exception as e:
        import traceback
        return JsonResponse({'status': 'error', 'message': str(e), 'traceback': traceback.format_exc()}, status=500)

def get_warehouse_map(request, floor_idx):
    """
    Endpoint 7: Get Digital Twin Map Data for Frontend Visualization
    """
    try:
        floor_idx = int(floor_idx)
        warehouse_id = request.GET.get('warehouse_id')
        
        if floor_idx not in floor_maps:
            return JsonResponse({'status': 'error', 'message': f'Floor {floor_idx} not found.'}, status=404)
        
        m = floor_maps[floor_idx]
        
        # Safely get zones and landmarks
        zones = getattr(m, 'zones', {})
        landmarks_dict = getattr(m, 'landmarks', {})
        
        # Determine occupancy if warehouse_id is provided
        occupancy = {}
        if warehouse_id:
            # Check for products directly linked to racks in this warehouse
            occupied_codes = list(Produit.objects.filter(
                models.Q(id_rack__storage_floor__id_entrepot_id=warehouse_id) |
                models.Q(id_rack__picking_floor__id_entrepot_id=warehouse_id)
            ).values_list('id_rack__code_rack', flat=True).distinct())
            
            # Also check RackProduct for many-to-many style storage
            occupied_codes_rp = list(RackProduct.objects.filter(
                models.Q(rack__storage_floor__id_entrepot_id=warehouse_id) |
                models.Q(rack__picking_floor__id_entrepot_id=warehouse_id),
                quantity__gt=0
            ).values_list('rack__code_rack', flat=True).distinct())
            
            all_occupied = set(occupied_codes + occupied_codes_rp)
            occupancy = {code: True for code in all_occupied}

        # Convert landmarks coordinates to dict format
        serializable_landmarks = {}
        for name, coord in landmarks_dict.items():
            if hasattr(coord, 'to_tuple'):
                serializable_landmarks[name] = {'x': coord.x, 'y': coord.y}
            else:
                serializable_landmarks[name] = coord
        
        return JsonResponse({
            'status': 'success',
            'width': m.width,
            'height': m.height,
            'zones': zones,
            'occupancy': occupancy,
            'landmarks': serializable_landmarks
        })
    except Exception as e:
        import traceback
        return JsonResponse({'status': 'error', 'message': str(e), 'traceback': traceback.format_exc()}, status=500)

def get_zoning(request, floor_idx):
    """
    Endpoint 8: Get AI Zoning Data (FAST, MEDIUM, SLOW slots)
    """
    try:
        if floor_idx not in floor_maps:
            return JsonResponse({'status': 'error', 'message': f'Floor {floor_idx} not found.'}, status=404)
        
        zoning = storage_service.storage_zoning.get(floor_idx, {})
        # Convert Tuple keys to strings for JSON
        serializable_zoning = {f"{k[0]},{k[1]}": v.value for k, v in zoning.items()}
        
        return JsonResponse({
            'status': 'success',
            'floor_idx': floor_idx,
            'zoning': serializable_zoning
        })
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=500)

@csrf_exempt
def record_picking_performance(request):
    """
    Endpoint 9: Record Actual Picking Performance (Requirement 8.5 - Learning Loop)
    Logs actual vs predicted values to enable continuous AI improvement.
    """
    if request.method != 'POST':
        return JsonResponse({'status': 'error', 'message': 'Only POST allowed.'}, status=405)
    
    try:
        data = json.loads(request.body)
        task_id = data.get('task_id')
        predicted_sec = float(data.get('predicted_time_seconds', 0))
        actual_sec = float(data.get('actual_time_seconds', 0))
        
        if not task_id or predicted_sec <= 0 or actual_sec <= 0:
            return JsonResponse({'status': 'error', 'message': 'Invalid data. Ensure task_id and valid times.'}, status=400)
        
        # Save to DB for background processing
        log = AIPerformanceLog.objects.create(
            task_id=task_id,
            task_type='PICKING',
            predicted_value=predicted_sec,
            actual_value=actual_sec,
            unit='seconds'
        )
        
        return JsonResponse({
            'status': 'success',
            'message': 'Performance data recorded. AI will learn from this.',
            'log_id': log.id
        })
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
        if order_obj is None:
            return JsonResponse({
                'status': 'success',
                'message': 'No order provided. Nothing to validate.',
                'order': {
                    'order_id': None,
                    'date': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    'items': [],
                    'status': 'DRAFT',
                    'source': 'AI_FORECASTING_SERVICE'
                }
            }, status=200)

        sku_id = data.get('sku_id')
        override_qty = data.get('override_qty')
        justification = data.get('justification')

        updated_order = forecast_service.order_service.validate_order(
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
