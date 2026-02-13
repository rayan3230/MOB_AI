import { apiCall } from './api';

export const chariotService = {
  getChariots: async (warehouseId = null) => {
    const normalizedWarehouseId = warehouseId !== null && warehouseId !== undefined
      ? String(warehouseId).trim().replace(/^"|"$/g, '')
      : '';
    const hasWarehouse = normalizedWarehouseId && normalizedWarehouseId !== 'undefined' && normalizedWarehouseId !== 'null';
    const endpoint = hasWarehouse
      ? `/api/warehouse/chariots/?warehouse_id=${encodeURIComponent(normalizedWarehouseId)}`
      : '/api/warehouse/chariots/';
    return await apiCall(endpoint, 'GET');
  },

  getAvailableChariots: async () => {
    return await apiCall('/api/warehouse/chariots/list_available_chariots/', 'GET');
  },

  getChariotByCode: async (code) => {
    return await apiCall(`/api/warehouse/chariots/by_code/?code=${encodeURIComponent(code)}`, 'GET');
  },

  assignChariot: async (id) => {
    return await apiCall(`/api/warehouse/chariots/${id}/assign_chariot/`, 'POST');
  },

  releaseChariot: async (id) => {
    return await apiCall(`/api/warehouse/chariots/${id}/release_chariot/`, 'POST');
  },

  setMaintenance: async (id) => {
    return await apiCall(`/api/warehouse/chariots/${id}/set_maintenance/`, 'POST');
  },

  createChariot: async (data) => {
    return await apiCall('/api/warehouse/chariots/', 'POST', data);
  },

  updateChariot: async (id, data) => {
    return await apiCall(`/api/warehouse/chariots/${id}/`, 'PATCH', data);
  },

  deleteChariot: async (id) => {
    return await apiCall(`/api/warehouse/chariots/${id}/`, 'DELETE');
  }
};
