import { apiCall } from './api';

/**
 * Product Service for managing SKUs
 */

export const getProducts = async (token = null, search = '', options = {}) => {
    const {
        actif = null,
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

    params.append('limit', String(limit));
    params.append('offset', String(offset));

    const endpoint = `/api/produit/produits/?${params.toString()}`;
    const response = await apiCall(endpoint, 'GET', null, token);
    return Array.isArray(response?.results) ? response.results : [];
};

export const getProductsPaged = async ({ token = null, search = '', actif = null, limit = 20, offset = 0 } = {}) => {
    const params = new URLSearchParams();

    if (search) {
        params.append('search', search);
    }

    if (actif !== null && actif !== undefined) {
        params.append('actif', String(actif));
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

export const productService = {
    getProducts,
    getProductsPaged,
    createProduct,
    updateProduct,
    deleteProduct,
    getVrackInfo
};

export default productService;
