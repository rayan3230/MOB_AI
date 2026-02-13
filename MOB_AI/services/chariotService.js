import api from './api';

export const chariotService = {
  getChariots: async () => {
    try {
      const response = await api.get('/warehouse/chariots/');
      return response.data;
    } catch (error) {
      console.error('Error fetching chariots:', error);
      throw error;
    }
  },

  getAvailableChariots: async () => {
    try {
      const response = await api.get('/warehouse/chariots/list_available_chariots/');
      return response.data;
    } catch (error) {
      console.error('Error fetching available chariots:', error);
      throw error;
    }
  },

  getChariotByCode: async (code) => {
    try {
      const response = await api.get(`/warehouse/chariots/by_code/?code=${code}`);
      return response.data;
    } catch (error) {
      console.error('Error fetching chariot by code:', error);
      throw error;
    }
  },

  assignChariot: async (id) => {
    try {
      const response = await api.post(`/warehouse/chariots/${id}/assign_chariot/`);
      return response.data;
    } catch (error) {
      console.error('Error assigning chariot:', error);
      throw error;
    }
  },

  releaseChariot: async (id) => {
    try {
      const response = await api.post(`/warehouse/chariots/${id}/release_chariot/`);
      return response.data;
    } catch (error) {
      console.error('Error releasing chariot:', error);
      throw error;
    }
  },

  setMaintenance: async (id) => {
    try {
      const response = await api.post(`/warehouse/chariots/${id}/set_maintenance/`);
      return response.data;
    } catch (error) {
      console.error('Error setting chariot to maintenance:', error);
      throw error;
    }
  },

  createChariot: async (data) => {
    try {
      const response = await api.post('/warehouse/chariots/', data);
      return response.data;
    } catch (error) {
      console.error('Error creating chariot:', error);
      throw error;
    }
  },

  updateChariot: async (id, data) => {
    try {
      const response = await api.put(`/warehouse/chariots/${id}/`, data);
      return response.data;
    } catch (error) {
      console.error('Error updating chariot:', error);
      throw error;
    }
  },

  deleteChariot: async (id) => {
    try {
      const response = await api.delete(`/warehouse/chariots/${id}/`);
      return response.data;
    } catch (error) {
      console.error('Error deleting chariot:', error);
      throw error;
    }
  }
};
