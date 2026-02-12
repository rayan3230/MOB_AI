import { apiCall } from './api';

export const authService = {
    login: async (username, password) => {
        return await apiCall('/users/login/', 'POST', { username, password });
    },
    
    // Add other auth related calls here (signup, logout, etc.)
    signup: async (userData) => {
        return await apiCall('/users/signup/', 'POST', userData);
    }
};
