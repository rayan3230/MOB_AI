import { apiCall } from './api';
import { offlineService } from './offlineService';

/**
 * AI Service for managing forecasting and optimization reports
 */

export const aiService = {
    /**
     * Get all general forecasts
     */
    getGeneralForecasts: async () => {
        try {
            const data = await apiCall('/api/forecast/all/', 'GET');
            await offlineService.cacheData('ai_general_forecasts', data);
            return data;
        } catch (error) {
            const cached = await offlineService.getCachedData('ai_general_forecasts');
            if (cached) return cached;
            throw error;
        }
    },

    /**
     * Get forecast for a specific SKU
     */
    getSKUForecast: async (skuId) => {
        try {
            const data = await apiCall(`/api/forecast/sku/${skuId}/`, 'GET');
            await offlineService.cacheData(`ai_sku_forecast_${skuId}`, data);
            return data;
        } catch (error) {
            const cached = await offlineService.getCachedData(`ai_sku_forecast_${skuId}`);
            if (cached) return cached;
            throw error;
        }
    },

    /**
     * Get explanation for a specific SKU forecast
     */
    getForecastExplanation: async (skuId) => {
        try {
            const data = await apiCall(`/api/forecast/explanation/${skuId}/`, 'GET');
            await offlineService.cacheData(`ai_explanation_${skuId}`, data);
            return data;
        } catch (error) {
            const cached = await offlineService.getCachedData(`ai_explanation_${skuId}`);
            if (cached) return cached;
            throw error;
        }
    },

    /**
     * Trigger preparation for tomorrow
     */
    triggerTomorrowPreparation: async () => {
        return await apiCall('/api/forecast/trigger-tomorrow/', 'POST');
    },

    /**
     * Validate an order
     */
    validateOrder: async (orderData) => {
        return await apiCall('/api/forecast/validate/', 'POST', orderData);
    },

    /**
     * Get picking routes (from warehouse service context)
     */
    getPickingRoutes: async (warehouseId = null) => {
        const url = warehouseId 
            ? `/api/warehouse/picking-routes/?warehouse_id=${warehouseId}` 
            : '/api/warehouse/picking-routes/';
        try {
            const data = await apiCall(url, 'GET');
            const cacheKey = warehouseId ? `picking_routes_${warehouseId}` : 'picking_routes_global';
            await offlineService.cacheData(cacheKey, data);
            return data;
        } catch (error) {
            const cacheKey = warehouseId ? `picking_routes_${warehouseId}` : 'picking_routes_global';
            const cached = await offlineService.getCachedData(cacheKey);
            if (cached) return cached;
            throw error;
        }
    },

    /**
     * Get AI-optimized picking route (based on Requirement 8.3)
     */
    getAIPathOptimization: async (floorIdx, startPos, picks) => {
        try {
            const data = await apiCall('/api/forecast/optimize-route/', 'POST', {
                floor_idx: floorIdx,
                start_pos: startPos,
                picks: picks
            });
            return data;
        } catch (error) {
            console.error('AI Path Optimization Error:', error);
            throw error;
        }
    },

    /**
     * Get Digital Twin map data for a specific floor
     */
    getDigitalTwinMap: async (floorIdx, warehouseId = null) => {
        try {
            let url = `/api/forecast/map/${floorIdx}/`;
            if (warehouseId) {
                url += `?warehouse_id=${warehouseId}`;
            }
            const data = await apiCall(url, 'GET');
            await offlineService.cacheData(`digital_twin_map_${floorIdx}_${warehouseId}`, data);
            return data;
        } catch (error) {
            const cached = await offlineService.getCachedData(`digital_twin_map_${floorIdx}_${warehouseId}`);
            if (cached) return cached;
            throw error;
        }
    },

    /**
     * Get AI storage zoning (FAST/MEDIUM/SLOW slots)
     */
    getWarehouseZoning: async (floorIdx) => {
        try {
            const data = await apiCall(`/api/forecast/zoning/${floorIdx}/`, 'GET');
            await offlineService.cacheData(`warehouse_zoning_${floorIdx}`, data);
            return data;
        } catch (error) {
            const cached = await offlineService.getCachedData(`warehouse_zoning_${floorIdx}`);
            if (cached) return cached;
            throw error;
        }
    },

    /**
     * Record actual picking performance for AI learning
     */
    recordPickingPerformance: async (taskId, predictedSec, actualSec) => {
        try {
            return await apiCall('/api/forecast/record-performance/', 'POST', {
                task_id: taskId,
                predicted_time_seconds: predictedSec,
                actual_time_seconds: actualSec
            });
        } catch (error) {
            console.error('Performance recording error:', error);
            // Non-critical, don't throw
            return null;
        }
    }
};

export default aiService;
