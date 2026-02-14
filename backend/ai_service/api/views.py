import os
import json
from datetime import datetime
from django.shortcuts import render
from django.http import JsonResponse
from django.conf import settings
from django.views.decorators.csrf import csrf_exempt
from .models import AIPerformanceLog
from Produit.models import Produit
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

def get_rack_display(code):
    """Converts 0Q-02-03 into human readable Rack Q, Level 2, Slot 3"""
    if not code or not isinstance(code, str):
        return str(code)
    parts = code.split('-')
    if len(parts) >= 1:
        rack = parts[0]
        if rack.startswith('0'): rack = rack[1:]
        
        display = f"Rack {rack}"
        if len(parts) >= 2:
            level = parts[1]
            if level.startswith('0'): level = level[1:]
            display += f", L{level}"
        if len(parts) >= 3:
            slot = parts[2]
            if slot.startswith('0'): slot = slot[1:]
            display += f", S{slot}"
        return display
    return code

def generate_forecast_all(request):
    """
    Endpoint 1: Generate full replenishment & optimization plan for dashboard.
    Combines forecasting (Demand) and storage optimization (Movement).
    """
    try:
        limit = int(request.GET.get('limit', 20))
        # Get raw forecast data from service
        forecast_results = forecast_service.get_all_forecasts_raw(limit_products=limit)
        
        # Sync physical state for storage optimization
        if forecast_service.loader.emplacements is not None:
            storage_service.sync_physical_state(forecast_service.loader.emplacements)
        
        formatted_predictions = []
        
        # 1. Add Space Allocation / Move Actions (PRIORITY)
        # Check for rebalancing suggestions
        relocations = storage_service.check_for_rebalancing(traffic_threshold=5)
        for move in relocations:
            # Get slot names for better UI display
            from_floor = move['from_floor']
            from_coord = move['from_coord']
            to_floor = move['to_floor']
            to_coord = move['to_coord']
            
            # Resolve codes from storage service mapping if they exist
            from_name_raw = storage_service.slot_to_code.get((from_floor, from_coord[0], from_coord[1]))
            if not from_name_raw:
                from_name_raw = floor_maps[from_floor].get_slot_name(WarehouseCoordinate(*from_coord))
            
            to_name_raw = floor_maps[to_floor].get_slot_name(WarehouseCoordinate(*to_coord))
            
            # Format human readable
            from_display = get_rack_display(from_name_raw)
            to_display = get_rack_display(to_name_raw)
            
            # Get SKU string if possible
            prod_obj = Produit.objects.filter(id_produit=move['product_id']).first()
            sku_str = prod_obj.sku if prod_obj else f"SKU-{move['product_id']}"
            
            # AI Logic: Confidence based on relocation necessity
            # If it's a mismatched zone, we have high confidence. If it's just congestion, slightly lower.
            confidence = 90 if "Mismatched" in move['reason'] else 75

            formatted_predictions.append({
                'id': f"MOV-{move['product_id']}",
                'date': "Next 24 Hours",
                'type': 'Space Allocation',
                'predictedValue': f"Move {sku_str} to {to_display}",
                'currentValue': f"In {from_display}",
                'status': 'AI Suggested',
                'justification': '',
                'confidence': confidence,
                'reasoning': f"Optimize warehouse flow: {move['reason']}. This move will reduce picking distance for high-turnover items.",
                'sku_id': move['product_id']
            })
            
        # 2. Add Replenishment Actions
        for pid, data in forecast_results.items():
            # Filter out SKUs with zero or negligible forecast to avoid cluttering the UI
            # Also filter out low-confidence defaults (confidence 10 is the floor)
            if data['forecast'] <= 0.1 or data['confidence'] <= 10:
                continue
                
            formatted_predictions.append({
                'id': f"REP-{pid}",
                'date': "Scheduled for Tomorrow",
                'type': 'Stock Replenishment',
                'predictedValue': f"Buy {data['forecast']:.0f} units",
                'currentValue': f"{data['forecast']:.0f} needed",
                'status': 'AI Predicted',
                'justification': '',
                'confidence': data['confidence'],
                'reasoning': data['reasoning'],
                'sku_id': pid
            })
            
        return JsonResponse(formatted_predictions, safe=False)
    except Exception as e:
        import traceback
        traceback.print_exc()
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
        if floor_idx not in floor_maps:
            return JsonResponse({'status': 'error', 'message': f'Floor {floor_idx} not found.'}, status=404)
        
        m = floor_maps[floor_idx]
        
        # Safely get zones and landmarks
        zones = getattr(m, 'zones', {})
        landmarks_dict = getattr(m, 'landmarks', {})
        
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
@csrf_exempt
def validate_order(request):
    """
    Endpoint 4: Supervisor Validation & Override
    Demonstrates human-in-the-loop and auditability.
    Handles both 'order' wrapped objects and direct overrides from the UI.
    """
    if request.method != 'POST':
        return JsonResponse({'status': 'error', 'message': 'Only POST allowed.'}, status=405)
    
    try:
        data = json.loads(request.body)
        
        # Handle field name variations from frontend
        sku_id = data.get('sku_id') or data.get('prediction_id')
        override_qty = data.get('override_qty') or data.get('override_value')
        justification = data.get('justification')
        
        # In the AI Actions UI, we might not have a full order object yet
        order_obj = data.get('order')
        if order_obj is None:
            # Create a dummy container for the validation logic if only a single SKU override is sent
            order_obj = {
                'order_id': f"MAN-{datetime.now().strftime('%H%M%S')}",
                'items': [{
                    'sku_id': sku_id,
                    'quantity': 0, 
                    'status': 'PENDING'
                }]
            }

        updated_order = forecast_service.order_service.validate_order(
            order_obj, 
            sku_id=sku_id, 
            override_qty=float(override_qty) if override_qty is not None else None, 
            justification=justification
        )
        
        return JsonResponse({
            'status': 'success',
            'order': updated_order
        })
    except Exception as e:
        import traceback
        traceback.print_exc()
        return JsonResponse({'status': 'error', 'message': str(e)}, status=500)
