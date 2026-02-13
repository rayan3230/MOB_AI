// Using 127.0.0.1 instead of localhost for better iOS compatibility
//const BASE_URL = 'http://127.0.0.1:8000';
const BASE_URL = 'http://192.168.100.66:8000'; // Computer IP (for physical devices)
// const BASE_URL = 'http://10.0.2.2:8000'; // Android Emulator

export const apiCall = async (endpoint, method = 'POST', body = null, token = null) => {
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
    
    try {
        const response = await fetch(url, config);
        const data = await response.json();
        
        if (!response.ok) {
            throw data;
        }
        
        return data;
    } catch (error) {
        console.error(`API Call Error (${endpoint}):`, error);
        throw error;
    }
};
