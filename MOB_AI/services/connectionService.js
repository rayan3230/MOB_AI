import NetInfo from '@react-native-community/netinfo';
import { offlineService } from './offlineService';

// This should match the IP in api.js
const BASE_URL = 'http://10.80.241.245:8000';
const PING_URL = `${BASE_URL}/api/warehouse/ping/`; // Using an existing or expected endpoint

let listeners = [];
let isConnected = true;
let isInternetReachable = true;
let isServerReachable = true;

const notifyListeners = () => {
    listeners.forEach(callback => callback({
        isConnected,
        isInternetReachable,
        isServerReachable
    }));
};

// Monitor NetInfo
NetInfo.addEventListener(state => {
    const wasOffline = !isConnected || !isInternetReachable;
    
    isConnected = state.isConnected;
    isInternetReachable = state.isInternetReachable;
    
    console.log(`[Connection] NetInfo: Connected=${isConnected}, Reachable=${isInternetReachable}`);
    
    // If we were offline and now we are online, trigger a sync and ping
    if (wasOffline && isConnected && isInternetReachable) {
        connectionService.checkServerPresence();
        offlineService.syncQueue();
    }
    
    notifyListeners();
});

export const connectionService = {
    getStatus: () => ({
        isConnected,
        isInternetReachable,
        isServerReachable
    }),

    subscribe: (callback) => {
        listeners.push(callback);
        callback({ isConnected, isInternetReachable, isServerReachable });
        return () => {
            listeners = listeners.filter(l => l !== callback);
        };
    },

    /**
     * Actively check if the backend is reachable
     */
    checkServerPresence: async () => {
        try {
            const controller = new AbortController();
            const timeoutId = setTimeout(() => controller.abort(), 3000);
            
            const response = await fetch(PING_URL, { 
                method: 'GET',
                signal: controller.signal 
            });
            
            clearTimeout(timeoutId);
            isServerReachable = response.ok;
        } catch (error) {
            isServerReachable = false;
        }
        
        notifyListeners();
        return isServerReachable;
    }
};
