import { apiCall } from './api';

/**
 * Product Service for managing SKUs
 */

export const getProducts = async (token = null, search = '') => {
    const endpoint = `/api/produit/produits/${search ? `?search=${search}` : ''}`;
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
    createProduct,
    updateProduct,
    deleteProduct,
    getVrackInfo
};

export default productService;
