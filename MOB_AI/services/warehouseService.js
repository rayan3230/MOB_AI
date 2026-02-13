import { apiCall } from './api';

export const warehouseService = {
    getWarehouses: async () => {
        const response = await apiCall('/api/warehouse/warehouses/', 'GET');
        if (Array.isArray(response)) {
            return response;
        }
        if (Array.isArray(response?.results)) {
            return response.results;
        }
        return [];
    },

    getWarehouseDetail: async (warehouseId) => {
        return await apiCall(`/api/warehouse/warehouses/${warehouseId}/`, 'GET');
    },

    getWarehouseFloors: async (warehouseId) => {
        return await apiCall(`/api/warehouse/warehouses/${warehouseId}/warehouse_floors/`, 'GET');
    },

    // Floor Management
    getFloors: async (warehouseId = null) => {
        const url = warehouseId ? `/api/warehouse/floors/?warehouse_id=${warehouseId}` : '/api/warehouse/floors/';
        return await apiCall(url, 'GET');
    },

    getPickingFloors: async (warehouseId = null) => {
        const url = warehouseId ? `/api/warehouse/picking-floors/?warehouse_id=${warehouseId}` : '/api/warehouse/picking-floors/';
        return await apiCall(url, 'GET');
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
        return await apiCall(url, 'GET');
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
        return await apiCall(url, 'GET');
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
        return await apiCall(url, 'GET');
    },

    adjustVrackQuantity: async (vrackId, delta) => {
        return await apiCall(`/api/warehouse/vracks/${vrackId}/adjust_quantity/`, 'POST', { delta });
    },

    transferFromVrack: async (vrackId, transferData) => {
        // transferData: { destination_location_id, quantity, notes }
        return await apiCall(`/api/warehouse/vracks/${vrackId}/transfer_to_shelf/`, 'POST', transferData);
    }
};
