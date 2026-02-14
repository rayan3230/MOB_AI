import { apiCall } from './api';
import { offlineService } from './offlineService';

/**
 * Product Service for managing SKUs
 */

export const getProducts = async (token = null, search = '', options = {}) => {
    const {
        actif = null,
        warehouse_id = null,
        limit = 20,
        offset = 0,
    } = options;

    const params = new URLSearchParams();

    if (search) {
        params.append('search', search);
    }

    if (actif !== null && actif !== undefined) {
        params.append('actif', String(actif));
    }

    if (warehouse_id !== null && warehouse_id !== undefined && String(warehouse_id).trim() !== '') {
        params.append('warehouse_id', String(warehouse_id).trim());
    }

    params.append('limit', String(limit));
    params.append('offset', String(offset));

    const endpoint = `/api/produit/produits/?${params.toString()}`;
    
    try {
        const response = await apiCall(endpoint, 'GET', null, token);
        const results = Array.isArray(response?.results) ? response.results : [];
        
        // Cache frequently used/searched products for offline locator
        if (results.length > 0 && !search) {
            await offlineService.cacheData('frequent_products', results.slice(0, 100));
        }
        
        return results;
    } catch (error) {
        // Fallback to cache if offline
        const cached = await offlineService.getCachedData('frequent_products');
        if (cached) {
            if (search) {
                return cached.filter(p => 
                    p.nom_produit.toLowerCase().includes(search.toLowerCase()) || 
                    p.sku.toLowerCase().includes(search.toLowerCase())
                );
            }
            return cached;
        }
        throw error;
    }
};

export const getProductsPaged = async ({ token = null, search = '', actif = null, warehouse_id = null, limit = 20, offset = 0 } = {}) => {
    const params = new URLSearchParams();

    if (search) {
        params.append('search', search);
    }

    if (actif !== null && actif !== undefined) {
        params.append('actif', String(actif));
    }

    if (warehouse_id !== null && warehouse_id !== undefined && String(warehouse_id).trim() !== '') {
        params.append('warehouse_id', String(warehouse_id).trim());
    }

    params.append('limit', String(limit));
    params.append('offset', String(offset));

    const endpoint = `/api/produit/produits/?${params.toString()}`;
    return await apiCall(endpoint, 'GET', null, token);
};

export const createProduct = async (productData, token = null) => {
    return await apiCall('/api/produit/produits/', 'POST', productData, token);
};

export const updateProduct = async (id, productData, token = null) => {
    return await apiCall(`/api/produit/produits/${id}/`, 'PUT', productData, token);
};

export const deleteProduct = async (id, token = null) => {
    // Delete in this context might be logical delete (deactivate) as per views.py documentation
    return await apiCall(`/api/produit/produits/${id}/`, 'DELETE', null, token);
};

export const getVrackInfo = async (productId) => {
    return await apiCall(`/api/produit/produits/${productId}/vrack_info/`, 'GET');
};

/**
 * Locate a product across all warehouses
 * Caches results for offline locator functionality
 */
export const locateProduct = async (searchQuery) => {
    try {
        const products = await getProducts(null, searchQuery);
        
        // Enhance with location data (id_rack)
        const locatedProducts = products.map(p => ({
            id: p.id_produit,
            sku: p.sku,
            name: p.nom_produit,
            location: p.id_rack ? (p.id_rack.code_rack || p.id_rack) : 'No fixed location',
            warehouse: p.id_rack?.id_zone?.id_etage?.id_entrepot?.nom_entrepot || 'Unknown',
            category: p.categorie
        }));

        // Update the "frequently picked" cache with these results
        if (locatedProducts.length > 0) {
            const currentCache = await offlineService.getCachedData('product_locator_cache') || [];
            // Merge and keep unique, prioritizing newest
            const merged = [...locatedProducts, ...currentCache].filter((v, i, a) => a.findIndex(t => t.id === v.id) === i).slice(0, 50);
            await offlineService.cacheData('product_locator_cache', merged);
        }

        return locatedProducts;
    } catch (error) {
        const cached = await offlineService.getCachedData('product_locator_cache');
        if (cached) {
            return cached.filter(p => 
                p.name.toLowerCase().includes(searchQuery.toLowerCase()) || 
                p.sku.toLowerCase().includes(searchQuery.toLowerCase())
            );
        }
        throw error;
    }
};

export const productService = {
    getProducts,
    getProductsPaged,
    createProduct,
    updateProduct,
    deleteProduct,
    getVrackInfo,
    locateProduct
};

export default productService;
