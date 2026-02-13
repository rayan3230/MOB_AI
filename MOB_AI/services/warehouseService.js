import { apiCall } from './api';

export const warehouseService = {
    getWarehouses: async () => {
        return await apiCall('/api/warehouse/warehouses/', 'GET');
    },

    getWarehouseDetail: async (warehouseId) => {
        return await apiCall(`/api/warehouse/warehouses/${warehouseId}/`, 'GET');
    },

    getWarehouseFloors: async (warehouseId) => {
        return await apiCall(`/api/warehouse/warehouses/${warehouseId}/warehouse_floors/`, 'GET');
    },

    createWarehouse: async (warehouseData) => {
        return await apiCall('/api/warehouse/warehouses/', 'POST', warehouseData);
    },

    updateWarehouse: async (warehouseId, warehouseData) => {
        return await apiCall(`/api/warehouse/warehouses/${warehouseId}/`, 'PATCH', warehouseData);
    },

    deleteWarehouse: async (warehouseId) => {
        return await apiCall(`/api/warehouse/warehouses/${warehouseId}/`, 'DELETE');
    }
};
