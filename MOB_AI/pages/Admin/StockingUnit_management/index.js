import React, { useState, useEffect, useCallback, useRef } from 'react';
import { 
  View, 
  Text, 
  StyleSheet, 
  FlatList, 
  ActivityIndicator, 
  TouchableOpacity, 
  Alert, 
  Modal, 
  TextInput,
  ScrollView,
  Switch
} from 'react-native';
import { Feather } from '@expo/vector-icons';
import { productService } from '../../../services/productService';
import { warehouseService } from '../../../services/warehouseService';

const PAGE_SIZE = 20;
const PRELOAD_INDEX = 13;

const StockingUnitManagement = () => {
  const [products, setProducts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [loadingMore, setLoadingMore] = useState(false);
  const [currentOffset, setCurrentOffset] = useState(0);
  const [hasMore, setHasMore] = useState(false);
  const [totalProducts, setTotalProducts] = useState(0);
  const [warehouses, setWarehouses] = useState([]);
  const [selectedWarehouseId, setSelectedWarehouseId] = useState('');
  const [warehouseFilterModalVisible, setWarehouseFilterModalVisible] = useState(false);
  const [filterLoading, setFilterLoading] = useState(false);
  const [modalVisible, setModalVisible] = useState(false);
  const [isEditing, setIsEditing] = useState(false);
  const [editingId, setEditingId] = useState(null);
  const [submitting, setSubmitting] = useState(false);

  const [newProduct, setNewProduct] = useState({
    sku: '',
    nom_produit: '',
    unite_mesure: 'PCS',
    categorie: '',
    collisage_palette: '',
    collisage_fardeau: '',
    poids: '',
    actif: true
  });

  const paginationStateRef = useRef({
    loading: true,
    refreshing: false,
    loadingMore: false,
    hasMore: false,
    currentOffset: 0,
    selectedWarehouseId: '',
    productsLength: 0,
  });
  const viewabilityConfig = useRef({ itemVisiblePercentThreshold: 40 });

  paginationStateRef.current = {
    loading,
    refreshing,
    loadingMore,
    hasMore,
    currentOffset,
    selectedWarehouseId,
    productsLength: products.length,
  };

  const fetchData = async (warehouseIdOverride = null) => {
    try {
      setLoading(true);
      const warehousesData = await warehouseService.getWarehouses();

      const safeWarehouses = Array.isArray(warehousesData)
        ? warehousesData
            .filter((w) => w && w.id_entrepot)
            .map((w) => ({ ...w, id_entrepot: String(w.id_entrepot).trim() }))
        : [];

      const normalizedOverride = warehouseIdOverride !== null && warehouseIdOverride !== undefined
        ? String(warehouseIdOverride).trim()
        : null;
      const currentWarehouseId = selectedWarehouseId ? String(selectedWarehouseId).trim() : '';

      let effectiveWarehouseId = normalizedOverride !== null ? normalizedOverride : currentWarehouseId;
      if (effectiveWarehouseId && !safeWarehouses.some((w) => w.id_entrepot === effectiveWarehouseId)) {
        effectiveWarehouseId = '';
      }

      const response = await productService.getProductsPaged({
        warehouse_id: effectiveWarehouseId || null,
        limit: PAGE_SIZE,
        offset: 0,
      });
      const firstPage = Array.isArray(response?.results) ? response.results : [];

      setProducts(firstPage);
      setTotalProducts(typeof response?.count === 'number' ? response.count : firstPage.length);
      setCurrentOffset(firstPage.length);
      setHasMore(Boolean(response?.has_more));
      setWarehouses(safeWarehouses);
      setSelectedWarehouseId(effectiveWarehouseId);
    } catch (error) {
      console.error('Error fetching products:', error);
      Alert.alert('Error', 'Failed to load products');
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, []);

  const onRefresh = () => {
    setRefreshing(true);
    fetchData(selectedWarehouseId);
  };

  const loadMoreProducts = useCallback(async () => {
    const state = paginationStateRef.current;
    if (state.loading || state.refreshing || state.loadingMore || !state.hasMore) {
      return;
    }

    try {
      setLoadingMore(true);
      const response = await productService.getProductsPaged({
        warehouse_id: state.selectedWarehouseId || null,
        limit: PAGE_SIZE,
        offset: state.currentOffset,
      });

      const nextPage = Array.isArray(response?.results) ? response.results : [];
      if (nextPage.length > 0) {
        setProducts((prev) => [...prev, ...nextPage]);
        setCurrentOffset((prev) => prev + nextPage.length);
      }
      setHasMore(Boolean(response?.has_more));
    } catch (error) {
      console.error('Error loading more products:', error);
    } finally {
      setLoadingMore(false);
    }
  }, []);

  const handleViewableItemsChanged = useCallback(({ viewableItems }) => {
    const state = paginationStateRef.current;
    if (!viewableItems?.length || !state.hasMore || state.loadingMore) {
      return;
    }

    const maxVisibleIndex = viewableItems.reduce((maxIdx, viewableItem) => {
      if (typeof viewableItem.index === 'number') {
        return Math.max(maxIdx, viewableItem.index);
      }
      return maxIdx;
    }, -1);

    const preloadTrigger = Math.max(PRELOAD_INDEX, state.productsLength - (PAGE_SIZE - PRELOAD_INDEX));
    if (maxVisibleIndex >= preloadTrigger) {
      loadMoreProducts();
    }
  }, [loadMoreProducts]);

  const handleWarehouseFilterChange = async (warehouseId) => {
    setWarehouseFilterModalVisible(false);
    setFilterLoading(true);
    try {
      const selectedId = warehouseId ? String(warehouseId).trim() : '';
      setSelectedWarehouseId(selectedId);
      setRefreshing(true);
      await fetchData(selectedId);
    } catch (error) {
      console.error('Error changing product warehouse filter:', error);
      Alert.alert('Error', 'Failed to change warehouse filter');
      setRefreshing(false);
    } finally {
      setFilterLoading(false);
    }
  };

  const handleSubmitProduct = async () => {
    if (!newProduct.sku || !newProduct.nom_produit) {
      Alert.alert('Error', 'Please fill in SKU and Product Name');
      return;
    }

    try {
      setSubmitting(true);
      if (isEditing) {
        await productService.updateProduct(editingId, newProduct);
        Alert.alert('Success', 'Product updated successfully');
      } else {
        await productService.createProduct(newProduct);
        Alert.alert('Success', 'Product added successfully');
      }
      closeModal();
      fetchData(selectedWarehouseId);
    } catch (error) {
      console.error('Error submitting product:', error);
      Alert.alert('Error', `Failed to ${isEditing ? 'update' : 'add'} product`);
    } finally {
      setSubmitting(false);
    }
  };

  const handleDeleteProduct = (id) => {
    Alert.alert(
      'Delete Product',
      'Are you sure you want to delete this product?',
      [
        { text: 'Cancel', style: 'cancel' },
        { 
          text: 'Delete', 
          style: 'destructive',
          onPress: async () => {
            try {
              await productService.deleteProduct(id);
              Alert.alert('Success', 'Product deleted successfully');
              fetchData(selectedWarehouseId);
            } catch (error) {
              console.error('Error deleting product:', error);
              Alert.alert('Error', 'Failed to delete product');
            }
          }
        }
      ]
    );
  };

  const openEditModal = (prod) => {
    setNewProduct({
      sku: prod.sku,
      nom_produit: prod.nom_produit,
      unite_mesure: prod.unite_mesure,
      categorie: prod.categorie,
      collisage_palette: prod.collisage_palette ? prod.collisage_palette.toString() : '',
      collisage_fardeau: prod.collisage_fardeau ? prod.collisage_fardeau.toString() : '',
      poids: prod.poids ? prod.poids.toString() : '',
      actif: prod.actif
    });
    setEditingId(prod.id_produit);
    setIsEditing(true);
    setModalVisible(true);
  };

  const openAddModal = () => {
    setNewProduct({
      sku: '',
      nom_produit: '',
      unite_mesure: 'PCS',
      categorie: '',
      collisage_palette: '',
      collisage_fardeau: '',
      poids: '',
      actif: true
    });
    setIsEditing(false);
    setEditingId(null);
    setModalVisible(true);
  };

  const closeModal = () => {
    setModalVisible(false);
    setIsEditing(false);
  };

  const renderProductItem = ({ item }) => (
    <View style={styles.card}>
      <View style={styles.infoContainer}>
        <View style={styles.row}>
          <Text style={styles.skuText}>{item.sku}</Text>
          {!item.actif && (
            <View style={styles.inactiveBadge}>
              <Text style={styles.inactiveText}>INACTIVE</Text>
            </View>
          )}
        </View>
        <Text style={styles.nameText}>{item.nom_produit}</Text>
        <Text style={styles.subText}>
          {item.categorie} • {item.unite_mesure}
        </Text>
        <View style={styles.logisticsRow}>
          <View style={styles.logisticsItem}>
            <Feather name="box" size={12} color="#7f8c8d" />
            <Text style={styles.logisticsText}> P: {item.collisage_palette || 0}</Text>
          </View>
          <View style={styles.logisticsItem}>
            <Feather name="package" size={12} color="#7f8c8d" />
            <Text style={styles.logisticsText}> B: {item.collisage_fardeau || 0}</Text>
          </View>
          <View style={styles.logisticsItem}>
            <Feather name="database" size={12} color="#7f8c8d" />
            <Text style={styles.logisticsText}> {item.poids || 0}kg</Text>
          </View>
        </View>
      </View>
      
      <View style={styles.actionButtons}>
        <TouchableOpacity 
          style={styles.actionButton} 
          onPress={() => openEditModal(item)}
        >
          <Feather name="edit-2" size={18} color="#2196F3" />
        </TouchableOpacity>
        <TouchableOpacity 
          style={styles.actionButton} 
          onPress={() => handleDeleteProduct(item.id_produit)}
        >
          <Feather name="trash-2" size={18} color="#F44336" />
        </TouchableOpacity>
      </View>
    </View>
  );

  if (loading && !refreshing) {
    return (
      <View style={styles.centered}>
        <ActivityIndicator size="large" color="#2196F3" />
      </View>
    );
  }

  const selectedWarehouse = warehouses.find((w) => w.id_entrepot === selectedWarehouseId);
  const selectedWarehouseLabel = selectedWarehouse?.nom_entrepot || 'Tous les entrepôts';

  return (
    <View style={styles.container}>
      <View style={styles.header}>
        <View style={styles.titleContainer}>
          <Text style={styles.title}>Produits / Unitées</Text>
          <Text style={styles.subtitle}>{totalProducts} produit(s)</Text>
          <TouchableOpacity
            style={styles.filterButton}
            onPress={() => setWarehouseFilterModalVisible(true)}
            disabled={filterLoading || loading}
          >
            <Feather name="filter" size={14} color="#2196F3" />
            <Text style={styles.filterButtonText}>{selectedWarehouseLabel}</Text>
          </TouchableOpacity>
        </View>
        <TouchableOpacity
          style={styles.addButton}
          onPress={openAddModal}
        >
          <Text style={styles.addButtonText}>+ Ajouter Produit</Text>
        </TouchableOpacity>
      </View>

      {filterLoading && (
        <View style={styles.filterLoadingRow}>
          <ActivityIndicator size="small" color="#2196F3" />
          <Text style={styles.filterLoadingText}>Chargement des produits filtrés...</Text>
        </View>
      )}
      
      {products.length === 0 ? (
        <View style={styles.centered}>
          <Text>Aucun produit trouvé</Text>
        </View>
      ) : (
        <FlatList
          data={products}
          keyExtractor={(item) => String(item.id_produit)}
          renderItem={renderProductItem}
          onRefresh={onRefresh}
          refreshing={refreshing}
          onViewableItemsChanged={handleViewableItemsChanged}
          viewabilityConfig={viewabilityConfig.current}
          ListFooterComponent={
            loadingMore ? (
              <View style={styles.footerLoader}>
                <ActivityIndicator size="small" color="#2196F3" />
              </View>
            ) : null
          }
          contentContainerStyle={styles.listContainer}
        />
      )}

      <Modal
        animationType="fade"
        transparent={true}
        visible={warehouseFilterModalVisible}
        onRequestClose={() => setWarehouseFilterModalVisible(false)}
      >
        <View style={styles.selectorOverlay}>
          <View style={styles.selectorCard}>
            <Text style={styles.selectorTitle}>Filtrer par entrepôt</Text>

            <TouchableOpacity
              style={[
                styles.selectorOption,
                selectedWarehouseId === '' && styles.selectorOptionActive,
              ]}
              onPress={() => handleWarehouseFilterChange('')}
            >
              <Text
                style={[
                  styles.selectorOptionText,
                  selectedWarehouseId === '' && styles.selectorOptionTextActive,
                ]}
              >
                Tous les entrepôts
              </Text>
            </TouchableOpacity>

            <ScrollView style={styles.selectorList}>
              {warehouses.map((w) => {
                const id = String(w.id_entrepot).trim();
                const isSelected = selectedWarehouseId === id;

                return (
                  <TouchableOpacity
                    key={id}
                    style={[styles.selectorOption, isSelected && styles.selectorOptionActive]}
                    onPress={() => handleWarehouseFilterChange(id)}
                  >
                    <Text style={[styles.selectorOptionText, isSelected && styles.selectorOptionTextActive]}>
                      {w.nom_entrepot || id}
                    </Text>
                    <Text style={styles.selectorOptionSub}>{id}</Text>
                  </TouchableOpacity>
                );
              })}
            </ScrollView>

            <TouchableOpacity
              style={styles.selectorCloseBtn}
              onPress={() => setWarehouseFilterModalVisible(false)}
            >
              <Text style={styles.selectorCloseText}>Fermer</Text>
            </TouchableOpacity>
          </View>
        </View>
      </Modal>

      <Modal
        animationType="slide"
        transparent={true}
        visible={modalVisible}
        onRequestClose={closeModal}
      >
        <View style={styles.modalOverlay}>
          <View style={styles.modalContent}>
            <View style={styles.modalHandle} />
            <Text style={styles.modalTitle}>
              {isEditing ? 'Modifier Produit' : 'Ajouter Nouveau Produit'}
            </Text>
            
            <ScrollView style={styles.form}>
              <Text style={styles.label}>SKU *</Text>
              <TextInput
                style={styles.input}
                value={newProduct.sku}
                onChangeText={(t) => setNewProduct({...newProduct, sku: t})}
                placeholder="Unique SKU code"
              />

              <Text style={styles.label}>Nom Produit *</Text>
              <TextInput
                style={styles.input}
                value={newProduct.nom_produit}
                onChangeText={(t) => setNewProduct({...newProduct, nom_produit: t})}
                placeholder="Entrer nom produit"
              />

              <Text style={styles.label}>Catégorie</Text>
              <TextInput
                style={styles.input}
                value={newProduct.categorie}
                onChangeText={(t) => setNewProduct({...newProduct, categorie: t})}
                placeholder="e.g., Electronics, Food"
              />

              <Text style={styles.label}>Unitée de mesure</Text>
              <TextInput
                style={styles.input}
                value={newProduct.unite_mesure}
                onChangeText={(t) => setNewProduct({...newProduct, unite_mesure: t})}
                placeholder="e.g., PCS, KG, BOX"
              />

              <Text style={styles.label}>Poids (kg)</Text>
              <TextInput
                style={styles.input}
                value={newProduct.poids}
                onChangeText={(t) => setNewProduct({...newProduct, poids: t})}
                placeholder="0.00"
                keyboardType="numeric"
              />

              <Text style={styles.label}>Collisage Palette (qty par palette)</Text>
              <TextInput
                style={styles.input}
                value={newProduct.collisage_palette}
                onChangeText={(t) => setNewProduct({...newProduct, collisage_palette: t})}
                placeholder="0"
                keyboardType="numeric"
              />

              <Text style={styles.label}>Collisage Fardeau (qty par fardeau)</Text>
              <TextInput
                style={styles.input}
                value={newProduct.collisage_fardeau}
                onChangeText={(t) => setNewProduct({...newProduct, collisage_fardeau: t})}
                placeholder="0"
                keyboardType="numeric"
              />

              <View style={styles.switchRow}>
                <Text style={styles.label}>Actif</Text>
                <Switch
                  value={newProduct.actif}
                  onValueChange={(val) => setNewProduct({...newProduct, actif: val})}
                />
              </View>
            </ScrollView>

            <View style={styles.modalButtons}>
              <TouchableOpacity 
                style={[styles.modalButton, styles.cancelButton]} 
                onPress={closeModal}
                disabled={submitting}
              >
                <Text style={styles.cancelButtonText}>Annuler</Text>
              </TouchableOpacity>
              <TouchableOpacity 
                style={[styles.modalButton, styles.saveButton]} 
                onPress={handleSubmitProduct}
                disabled={submitting}
              >
                {submitting ? (
                  <ActivityIndicator color="white" size="small" />
                ) : (
                  <Text style={styles.saveButtonText}>{isEditing ? 'Enregistrer' : 'Valider'}</Text>
                )}
              </TouchableOpacity>
            </View>
          </View>
        </View>
      </Modal>
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#ffffff',
    padding: 16,
  },
  centered: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
  },
  header: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'flex-start',
    marginBottom: 16,
    marginTop: 8,
  },
  titleContainer: {
    flex: 1,
    paddingRight: 8,
  },
  title: {
    fontSize: 24,
    fontWeight: 'bold',
    color: '#333',
  },
  subtitle: {
    fontSize: 14,
    color: '#607080',
    marginTop: 2,
  },
  filterButton: {
    marginTop: 8,
    flexDirection: 'row',
    alignItems: 'center',
    alignSelf: 'flex-start',
    backgroundColor: '#eef6ff',
    borderWidth: 1,
    borderColor: '#d6eaff',
    borderRadius: 8,
    paddingHorizontal: 10,
    paddingVertical: 6,
  },
  filterButtonText: {
    marginLeft: 6,
    color: '#1f5f9b',
    fontWeight: '600',
    maxWidth: 220,
  },
  addButton: {
    backgroundColor: '#4CAF50',
    paddingHorizontal: 12,
    paddingVertical: 8,
    borderRadius: 8,
  },
  addButtonText: {
    color: 'white',
    fontWeight: 'bold',
  },
  filterLoadingRow: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#f4f8ff',
    borderWidth: 1,
    borderColor: '#dce9ff',
    borderRadius: 8,
    paddingHorizontal: 10,
    paddingVertical: 8,
    marginBottom: 10,
  },
  filterLoadingText: {
    marginLeft: 8,
    color: '#36577a',
    fontSize: 13,
    fontWeight: '500',
  },
  listContainer: {
    paddingBottom: 20,
  },
  card: {
    backgroundColor: 'white',
    borderRadius: 12,
    padding: 16,
    marginBottom: 12,
    flexDirection: 'row',
    justifyContent: 'space-between',
    elevation: 2,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 1 },
    shadowOpacity: 0.1,
    shadowRadius: 2,
  },
  infoContainer: {
    flex: 1,
  },
  row: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 4,
  },
  skuText: {
    fontSize: 16,
    fontWeight: 'bold',
    color: '#3498db',
    marginRight: 8,
  },
  nameText: {
    fontSize: 18,
    fontWeight: '600',
    color: '#2c3e50',
    marginBottom: 4,
  },
  subText: {
    fontSize: 14,
    color: '#7f8c8d',
  },
  logisticsRow: {
    flexDirection: 'row',
    marginTop: 8,
    gap: 12,
  },
  logisticsItem: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#f1f3f5',
    paddingHorizontal: 6,
    paddingVertical: 2,
    borderRadius: 4,
  },
  logisticsText: {
    fontSize: 11,
    color: '#666',
    fontWeight: '500',
  },
  inactiveBadge: {
    backgroundColor: '#F44336',
    paddingHorizontal: 6,
    paddingVertical: 2,
    borderRadius: 4,
  },
  inactiveText: {
    color: 'white',
    fontSize: 10,
    fontWeight: 'bold',
  },
  actionButtons: {
    flexDirection: 'row',
    alignItems: 'flex-start',
  },
  actionButton: {
    padding: 8,
    marginLeft: 4,
    borderRadius: 8,
    backgroundColor: '#f1f3f5',
  },
  modalOverlay: {
    flex: 1,
    backgroundColor: 'rgba(0,0,0,0.5)',
    justifyContent: 'flex-end',
  },
  modalContent: {
    backgroundColor: 'white',
    borderTopLeftRadius: 24,
    borderTopRightRadius: 24,
    padding: 24,
    maxHeight: '90%',
  },
  modalHandle: {
    width: 40,
    height: 5,
    backgroundColor: '#e0e0e0',
    borderRadius: 3,
    alignSelf: 'center',
    marginBottom: 16,
  },
  modalTitle: {
    fontSize: 20,
    fontWeight: 'bold',
    marginBottom: 20,
    textAlign: 'center',
  },
  form: {
    marginBottom: 24,
  },
  label: {
    fontSize: 14,
    fontWeight: '600',
    color: '#666',
    marginBottom: 6,
    marginTop: 12,
  },
  input: {
    backgroundColor: '#f8f9fa',
    borderWidth: 1,
    borderColor: '#e9ecef',
    borderRadius: 8,
    padding: 12,
    fontSize: 16,
  },
  switchRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginTop: 16,
    paddingVertical: 8,
  },
  modalButtons: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    paddingBottom: 20,
  },
  modalButton: {
    flex: 1,
    padding: 14,
    borderRadius: 10,
    alignItems: 'center',
    marginHorizontal: 6,
  },
  saveButton: {
    backgroundColor: '#4CAF50',
  },
  cancelButton: {
    backgroundColor: '#f1f3f5',
  },
  saveButtonText: {
    color: 'white',
    fontWeight: 'bold',
  },
  cancelButtonText: {
    color: '#495057',
    fontWeight: 'bold',
  },
  footerLoader: {
    paddingVertical: 12,
  },
  selectorOverlay: {
    flex: 1,
    backgroundColor: 'rgba(0,0,0,0.35)',
    justifyContent: 'center',
    alignItems: 'center',
    padding: 16,
  },
  selectorCard: {
    width: '100%',
    maxWidth: 420,
    maxHeight: '80%',
    backgroundColor: '#fff',
    borderRadius: 14,
    padding: 16,
  },
  selectorTitle: {
    fontSize: 18,
    fontWeight: '700',
    color: '#223245',
    marginBottom: 12,
  },
  selectorList: {
    maxHeight: 320,
  },
  selectorOption: {
    borderWidth: 1,
    borderColor: '#e6edf3',
    borderRadius: 10,
    paddingHorizontal: 12,
    paddingVertical: 10,
    marginBottom: 8,
    backgroundColor: '#fff',
  },
  selectorOptionActive: {
    borderColor: '#2d74b6',
    backgroundColor: '#edf6ff',
  },
  selectorOptionText: {
    fontSize: 14,
    fontWeight: '600',
    color: '#2d3b49',
  },
  selectorOptionTextActive: {
    color: '#1f5f9b',
  },
  selectorOptionSub: {
    marginTop: 2,
    fontSize: 12,
    color: '#7b8894',
  },
  selectorCloseBtn: {
    marginTop: 8,
    paddingVertical: 10,
    borderRadius: 8,
    backgroundColor: '#f1f3f5',
    alignItems: 'center',
  },
  selectorCloseText: {
    fontWeight: '700',
    color: '#425466',
  },
});

export default StockingUnitManagement;
