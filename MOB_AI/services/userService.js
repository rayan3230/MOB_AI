import { apiCall } from './api';
import { offlineService } from './offlineService';

export const userService = {
    /**
     * Get all users
     * Caches data for offline configuration reference
     */
    getUsers: async () => {
        try {
            const data = await apiCall('/users/users/', 'GET');
            if (Array.isArray(data)) {
                await offlineService.cacheData('users_list', data);
            }
            return data;
        } catch (error) {
            const cached = await offlineService.getCachedData('users_list');
            if (cached) return cached;
            throw error;
        }
    },

    createUser: async (userData) => {
        return await apiCall('/users/users/', 'POST', userData);
    },

    updateUser: async (userId, userData) => {
        return await apiCall(`/users/users/${userId}/`, 'PUT', userData);
    },

    patchUser: async (userId, userData) => {
        return await apiCall(`/users/users/${userId}/`, 'PATCH', userData);
    },

    deleteUser: async (userId) => {
        return await apiCall(`/users/users/${userId}/`, 'DELETE');
    },

    getUserActivities: async (userId) => {
        try {
            const data = await apiCall(`/users/users/${userId}/activities/`, 'GET');
            await offlineService.cacheData(`user_activities_${userId}`, data);
            return data;
        } catch (error) {
            const cached = await offlineService.getCachedData(`user_activities_${userId}`);
            if (cached) return cached;
            throw error;
        }
    }
};
