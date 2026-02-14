// Using 127.0.0.1 instead of localhost for better iOS compatibility
//const BASE_URL = 'http://127.0.0.1:8000';
const BASE_URL = 'http://10.80.241.245:8000'; // Computer IP (for physical devices)
// const BASE_URL = 'http://10.0.2.2:8000'; // Android Emulator

import { offlineService } from './offlineService';
import { connectionService } from './connectionService';

export const apiCall = async (endpoint, method = 'POST', body = null, token = null, skipQueue = false) => {
    // 1. Proactive check - if we already know we are offline, don't even try the network
    // (unless it's skipQueue, then we might be in manual retry or sync mode)
    const status = connectionService.getStatus();
    const isActuallyOffline = !status.isConnected || !status.isInternetReachable;
    
    if (isActuallyOffline && !skipQueue && method !== 'GET') {
        console.log(`[API] Proactive offline detection for ${endpoint}`);
        const queued = await offlineService.queueRequest(endpoint, method, body, token);
        if (queued) return { _queued: true };
    }

    // Ensure endpoint starts with /
    const cleanEndpoint = endpoint.startsWith('/') ? endpoint : `/${endpoint}`;
    const url = `${BASE_URL}${cleanEndpoint}`;
    
    console.log(`Calling API: ${method} ${url}`);
    
    const headers = {
        'Content-Type': 'application/json',
    };
    
    if (token) {
        headers['Authorization'] = `Token ${token}`;
    }
    
    const config = {
        method,
        headers,
    };
    
    if (body) {
        config.body = JSON.stringify(body);
    }
    
    // 2. Add a manageable timeout (60 seconds for heavy operations like warehouse creation)
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), 60000);
    config.signal = controller.signal;
    
    try {
        const response = await fetch(url, config);
        clearTimeout(timeoutId);
        
        // If it's a server error (500+) or timeout, we might want to queue it for POST/PUT/PATCH/DELETE
        if (!response.ok && response.status >= 500 && !skipQueue && method !== 'GET') {
            const queued = await offlineService.queueRequest(endpoint, method, body, token);
            if (queued) return { _queued: true };
        }

        const data = await response.json();
        
        if (!response.ok) {
            const error = new Error(data.detail || data.message || 'API Error');
            error.status = response.status;
            error.data = data;
            throw error;
        }
        
        return data;
    } catch (error) {
        clearTimeout(timeoutId);
        // Only log if it's not a handled error or if we want to see it
        // console.error(`API Call Error (${endpoint}):`, error);
        
        // Network errors (no connection) or timeout
        if (!skipQueue && method !== 'GET') {
            // Update reachability status based on failure
            connectionService.checkServerPresence();
            
            const queued = await offlineService.queueRequest(endpoint, method, body, token);
            if (queued) return { _queued: true };
        }
        
        throw error;
    }
};
