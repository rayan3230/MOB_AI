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
    }
};

export default aiService;
