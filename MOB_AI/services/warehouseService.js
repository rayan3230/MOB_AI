import { apiCall } from './api';
import { offlineService } from './offlineService';

export const warehouseService = {
    getWarehouses: async () => {
        try {
            const response = await apiCall('/api/warehouse/warehouses/', 'GET');
            const data = Array.isArray(response) ? response : (Array.isArray(response?.results) ? response.results : []);
            if (data.length > 0) {
                await offlineService.cacheData('warehouses', data);
            }
            return data;
        } catch (error) {
            const cached = await offlineService.getCachedData('warehouses');
            if (cached) return cached;
            throw error;
        }
    },

    getWarehouseDetail: async (warehouseId) => {
        try {
            const data = await apiCall(`/api/warehouse/warehouses/${warehouseId}/`, 'GET');
            await offlineService.cacheData(`warehouse_detail_${warehouseId}`, data);
            return data;
        } catch (error) {
            const cached = await offlineService.getCachedData(`warehouse_detail_${warehouseId}`);
            if (cached) return cached;
            throw error;
        }
    },

    getWarehouseFloors: async (warehouseId) => {
        try {
            const data = await apiCall(`/api/warehouse/warehouses/${warehouseId}/warehouse_floors/`, 'GET');
            await offlineService.cacheData(`warehouse_floors_${warehouseId}`, data);
            return data;
        } catch (error) {
            const cached = await offlineService.getCachedData(`warehouse_floors_${warehouseId}`);
            if (cached) return cached;
            throw error;
        }
    },

    // Floor Management
    getFloors: async (warehouseId = null) => {
        const url = warehouseId ? `/api/warehouse/floors/?warehouse_id=${warehouseId}` : '/api/warehouse/floors/';
        try {
            const data = await apiCall(url, 'GET');
            if (warehouseId) await offlineService.cacheData(`floors_${warehouseId}`, data);
            return data;
        } catch (error) {
            if (warehouseId) {
                const cached = await offlineService.getCachedData(`floors_${warehouseId}`);
                if (cached) return cached;
            }
            throw error;
        }
    },

    getPickingFloors: async (warehouseId = null) => {
        const url = warehouseId ? `/api/warehouse/picking-floors/?warehouse_id=${warehouseId}` : '/api/warehouse/picking-floors/';
        try {
            const data = await apiCall(url, 'GET');
            if (warehouseId) await offlineService.cacheData(`picking_floors_${warehouseId}`, data);
            return data;
        } catch (error) {
            if (warehouseId) {
                const cached = await offlineService.getCachedData(`picking_floors_${warehouseId}`);
                if (cached) return cached;
            }
            throw error;
        }
    },

    createFloor: async (floorData) => {
        if (floorData.type_niveau === 'PICKING') {
            return await apiCall('/api/warehouse/picking-floors/', 'POST', floorData);
        }
        return await apiCall('/api/warehouse/floors/', 'POST', floorData);
    },

    updateFloor: async (floorId, floorData) => {
        if (floorData.type_niveau === 'PICKING') {
            return await apiCall(`/api/warehouse/picking-floors/${floorId}/`, 'PATCH', floorData);
        }
        return await apiCall(`/api/warehouse/floors/${floorId}/`, 'PATCH', floorData);
    },

    deleteFloor: async (floorId, type = 'STOCK') => {
        const endpoint = type === 'PICKING' ? 'picking-floors' : 'floors';
        return await apiCall(`/api/warehouse/${endpoint}/${floorId}/`, 'DELETE');
    },

    createWarehouse: async (warehouseData) => {
        return await apiCall('/api/warehouse/warehouses/', 'POST', warehouseData);
    },

    updateWarehouse: async (warehouseId, warehouseData) => {
        return await apiCall(`/api/warehouse/warehouses/${warehouseId}/`, 'PATCH', warehouseData);
    },

    deleteWarehouse: async (warehouseId) => {
        return await apiCall(`/api/warehouse/warehouses/${warehouseId}/`, 'DELETE');
    },

    // Location Management
    getLocations: async (warehouseId = null) => {
        const normalizedWarehouseId = warehouseId !== null && warehouseId !== undefined
            ? String(warehouseId).trim().replace(/^"|"$/g, '')
            : '';
        const hasValidWarehouseId = normalizedWarehouseId && normalizedWarehouseId !== 'undefined' && normalizedWarehouseId !== 'null';
        const url = hasValidWarehouseId
            ? `/api/warehouse/locations/?warehouse_id=${encodeURIComponent(normalizedWarehouseId)}`
            : '/api/warehouse/locations/';
        
        try {
            const data = await apiCall(url, 'GET');
            if (hasValidWarehouseId) await offlineService.cacheData(`locations_${normalizedWarehouseId}`, data);
            return data;
        } catch (error) {
            if (hasValidWarehouseId) {
                const cached = await offlineService.getCachedData(`locations_${normalizedWarehouseId}`);
                if (cached) return cached;
            }
            throw error;
        }
    },

    getLocationsPaged: async (warehouseId = null, { limit = 20, offset = 0 } = {}) => {
        const normalizedWarehouseId = warehouseId !== null && warehouseId !== undefined
            ? String(warehouseId).trim().replace(/^"|"$/g, '')
            : '';
        const params = new URLSearchParams();

        if (normalizedWarehouseId && normalizedWarehouseId !== 'undefined' && normalizedWarehouseId !== 'null') {
            params.append('warehouse_id', normalizedWarehouseId);
        }

        params.append('limit', String(limit));
        params.append('offset', String(offset));

        const url = `/api/warehouse/locations/?${params.toString()}`;
        
        try {
            const data = await apiCall(url, 'GET');
            // We only cache the first page for offline map viewing
            if (offset === 0 && normalizedWarehouseId) {
                await offlineService.cacheData(`locations_paged_0_${normalizedWarehouseId}`, data);
            }
            return data;
        } catch (error) {
            if (offset === 0 && normalizedWarehouseId) {
                const cached = await offlineService.getCachedData(`locations_paged_0_${normalizedWarehouseId}`);
                if (cached) return cached;
            }
            throw error;
        }
    },

    createLocation: async (locationData) => {
        return await apiCall('/api/warehouse/locations/', 'POST', locationData);
    },

    updateLocation: async (locationId, locationData) => {
        return await apiCall(`/api/warehouse/locations/${locationId}/`, 'PATCH', locationData);
    },

    deleteLocation: async (locationId) => {
        return await apiCall(`/api/warehouse/locations/${locationId}/`, 'DELETE');
    },

    // Chariot Management
    getChariots: async () => {
        return await apiCall('/api/warehouse/chariots/', 'GET');
    },

    createChariot: async (chariotData) => {
        return await apiCall('/api/warehouse/chariots/', 'POST', chariotData);
    },

    updateChariot: async (chariotId, chariotData) => {
        return await apiCall(`/api/warehouse/chariots/${chariotId}/`, 'PATCH', chariotData);
    },

    deleteChariot: async (chariotId) => {
        return await apiCall(`/api/warehouse/chariots/${chariotId}/`, 'DELETE');
    },

    // Vrack Management
    getVracks: async (warehouseId = null) => {
        const url = warehouseId ? `/api/warehouse/vracks/?warehouse_id=${warehouseId}` : '/api/warehouse/vracks/';
        return await apiCall(url, 'GET');
    },

    createVrack: async (vrackData) => {
        return await apiCall('/api/warehouse/vracks/', 'POST', vrackData);
    },

    updateVrack: async (vrackId, vrackData) => {
        return await apiCall(`/api/warehouse/vracks/${vrackId}/`, 'PATCH', vrackData);
    },

    deleteVrack: async (vrackId) => {
        return await apiCall(`/api/warehouse/vracks/${vrackId}/`, 'DELETE');
    },

    getVrackByWarehouse: async (warehouseId) => {
        return await apiCall(`/api/warehouse/vracks/by_warehouse/?warehouse_id=${warehouseId}`, 'GET');
    },

    getDashboardStats: async (warehouseId = null) => {
        const url = warehouseId ? `/api/warehouse/warehouses/dashboard_stats/?warehouse_id=${warehouseId}` : '/api/warehouse/warehouses/dashboard_stats/';
        try {
            const data = await apiCall(url, 'GET');
            const cacheKey = warehouseId ? `dashboard_stats_${warehouseId}` : 'dashboard_stats_global';
            await offlineService.cacheData(cacheKey, data);
            return data;
        } catch (error) {
            const cacheKey = warehouseId ? `dashboard_stats_${warehouseId}` : 'dashboard_stats_global';
            const cached = await offlineService.getCachedData(cacheKey);
            if (cached) return cached;
            throw error;
        }
    },

    adjustVrackQuantity: async (vrackId, delta) => {
        return await apiCall(`/api/warehouse/vracks/${vrackId}/adjust_quantity/`, 'POST', { delta });
    },

    transferFromVrack: async (vrackId, transferData) => {
        // transferData: { destination_location_id, quantity, notes }
        return await apiCall(`/api/warehouse/vracks/${vrackId}/transfer_to_shelf/`, 'POST', transferData);
    }
};
