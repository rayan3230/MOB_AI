import AsyncStorage from '@react-native-async-storage/async-storage';
import { apiCall } from './api';
import { authService } from './authService';

const OFFLINE_QUEUE_KEY = '@api_offline_queue';

export const offlineService = {
    /**
     * Store a failed request for later synchronization
     */
    queueRequest: async (endpoint, method, body, token) => {
        try {
            const queueStr = await AsyncStorage.getItem(OFFLINE_QUEUE_KEY);
            const queue = queueStr ? JSON.parse(queueStr) : [];
            
            const newRequest = {
                id: `off_${Date.now()}`,
                timestamp: new Date().toISOString(),
                endpoint,
                method,
                body,
                token
            };
            
            queue.push(newRequest);
            await AsyncStorage.setItem(OFFLINE_QUEUE_KEY, JSON.stringify(queue));
            console.log(`[Offline] Request queued: ${method} ${endpoint}`);
            return true;
        } catch (e) {
            console.error('[Offline] Error queuing request:', e);
            return false;
        }
    },

    /**
     * Sync all queued requests with the server
     */
    syncQueue: async () => {
        try {
            // Check connectivity before starting sync
            const queueStr = await AsyncStorage.getItem(OFFLINE_QUEUE_KEY);
            if (!queueStr) return;
            
            let queue = JSON.parse(queueStr);
            if (queue.length === 0) return;

            // Only proceed if we have a connection
            // We'll import connectionService dynamically to avoid circular dependency
            const { connectionService } = require('./connectionService');
            const status = connectionService.getStatus();
            if (!status.isConnected || !status.isInternetReachable) {
                console.log('[Offline] Sync deferred: No connection');
                return;
            }
            
            console.log(`[Offline] Starting sync for ${queue.length} requests...`);
            
            const remainingQueue = [];
            const user = await authService.getUser();
            
            for (const request of queue) {
                try {
                    // 1. Replay original action
                    // Important: skipQueue=true to avoid re-queuing if this call fails
                    const response = await apiCall(request.endpoint, request.method, request.body, request.token, true);
                    
                    // 2. Log to backend OperationOffline table for audit
                    if (user && response) {
                        try {
                            await apiCall('/sync-queue/', 'POST', {
                                id_operation: String(request.id).substring(0, 30),
                                type_operation: `${request.method} ${request.endpoint}`,
                                donnees_operation: request.body || {},
                                statut: 'SYNCED',
                                timestamp_local: request.timestamp,
                                timestamp_sync: new Date().toISOString(),
                                id_utilisateur_id: user.id_utilisateur
                            }, request.token, true);
                        } catch (logError) {
                            console.warn('[Offline] Could not log to sync-queue table:', logError);
                        }
                    }

                    console.log(`[Offline] Successfully synced: ${request.endpoint}`);
                } catch (e) {
                    console.error(`[Offline] Sync failed for ${request.endpoint}, keeping in queue:`, e);
                    remainingQueue.push(request);
                }
            }
            
            await AsyncStorage.setItem(OFFLINE_QUEUE_KEY, JSON.stringify(remainingQueue));
            console.log(`[Offline] Sync finished. ${remainingQueue.length} items remaining.`);
        } catch (e) {
            console.error('[Offline] Error during sync:', e);
        }
    },

    /**
     * Cache data for offline viewing
     */
    cacheData: async (key, data) => {
        try {
            await AsyncStorage.setItem(`@cache_${key}`, JSON.stringify({
                timestamp: Date.now(),
                data
            }));
        } catch (e) {
            console.error('[Offline] Error caching data:', e);
        }
    },

    /**
     * Retrieve cached data
     */
    getCachedData: async (key) => {
        try {
            const cached = await AsyncStorage.getItem(`@cache_${key}`);
            return cached ? JSON.parse(cached).data : null;
        } catch (e) {
            return null;
        }
    }
};
