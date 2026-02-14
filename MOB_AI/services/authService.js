import AsyncStorage from '@react-native-async-storage/async-storage';
import { apiCall } from './api';

export const authService = {
    login: async (email, password) => {
        const response = await apiCall('/users/login/', 'POST', { email, password });
        if (response && response.user) {
            await AsyncStorage.setItem('user', JSON.stringify(response.user));
        }
        return response;
    },
    
    // Add other auth related calls here (signup, logout, etc.)
    signup: async (userData) => {
        return await apiCall('/users/signup/', 'POST', userData);
    },

    logout: async () => {
        await AsyncStorage.removeItem('user');
    },

    getUser: async () => {
        const user = await AsyncStorage.getItem('user');
        return user ? JSON.parse(user) : null;
    },

    updateProfile: async (userId, userData) => {
        const response = await apiCall(`/users/update_profile/${userId}/`, 'PUT', userData);
        if (response && response.user) {
            await AsyncStorage.setItem('user', JSON.stringify(response.user));
        }
        return response;
    }
};
