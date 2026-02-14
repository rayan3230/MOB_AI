import React, { useState, useEffect, useRef } from 'react';
import { 
  View, 
  Text, 
  StyleSheet, 
  FlatList, 
  ActivityIndicator, 
  TouchableOpacity, 
  Alert, 
  TextInput,
  StatusBar
} from 'react-native';
import { Feather } from '@expo/vector-icons';
import OptionSelector from '../../../components/OptionSelector';
import { warehouseService } from '../../../services/warehouseService';
import { productService } from '../../../services/productService';
import CollapsibleManagementCard from '../../../components/CollapsibleManagementCard';
import ManagementModal from '../../../components/ManagementModal';
import { lightTheme } from '../../../constants/theme';

const PRODUCTS_PAGE_SIZE = 1000;

const VrackManagement = () => {
  const [vracks, setVracks] = useState([]);
  const [warehouses, setWarehouses] = useState([]);
  const [products, setProducts] = useState([]);
  const [productsLoading, setProductsLoading] = useState(false);
  const [selectedWarehouseId, setSelectedWarehouseId] = useState('');
  const [warehouseFilterModalVisible, setWarehouseFilterModalVisible] = useState(false);
  const [filterLoading, setFilterLoading] = useState(false);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [modalVisible, setModalVisible] = useState(false);
  const [isEditing, setIsEditing] = useState(false);
  const [editingId, setEditingId] = useState(null);
  const [submitting, setSubmitting] = useState(false);
  const [locations, setLocations] = useState([]);
  const [transferModalVisible, setTransferModalVisible] = useState(false);
  const [selectedVrack, setSelectedVrack] = useState(null);
  const [transferData, setTransferData] = useState({
    destination_location_id: '',
    quantity: '',
    notes: ''
  });
  const [newVrack, setNewVrack] = useState({
    id_entrepot_id: '',
    id_produit_id: '',
    quantite: '0'
  });
  const productsBgLoadingRef = useRef(false);

  const mergeProducts = (incomingProducts) => {
    const seen = new Set();
    return incomingProducts.filter((item) => {
      const key = String(item.id_produit);
      if (seen.has(key)) {
        return false;
      }
      seen.add(key);
      return true;
    });
  };

  const loadProductsInBackground = async (initialOffset) => {
    if (productsBgLoadingRef.current) {
      return;
    }
    productsBgLoadingRef.current = true;

    try {
      let offset = initialOffset;
      let hasMore = true;

      while (hasMore) {
        const response = await productService.getProductsPaged({
          limit: PRODUCTS_PAGE_SIZE,
          offset,
        });
        const pageItems = Array.isArray(response?.results) ? response.results : [];

        if (pageItems.length > 0) {
          setProducts((prev) => mergeProducts([...prev, ...pageItems]));
          offset += pageItems.length;
        }

        hasMore = Boolean(response?.has_more) && pageItems.length > 0;
      }
    } catch (error) {
      console.error('Background product loading failed:', error);
    } finally {
      productsBgLoadingRef.current = false;
    }
  };

  const ensureProductsLoaded = async () => {
    if (products.length > 0 || productsLoading) {
      return;
    }

    try {
      setProductsLoading(true);
      const response = await productService.getProductsPaged({
        limit: PRODUCTS_PAGE_SIZE,
        offset: 0,
      });

      const firstPage = Array.isArray(response?.results) ? response.results : [];
      setProducts(firstPage);

      if (firstPage.length > 0) {
        setNewVrack((prev) => ({
          ...prev,
          id_produit_id: prev.id_produit_id || firstPage[0].id_produit,
        }));
      }

      if (response?.has_more && firstPage.length > 0) {
        loadProductsInBackground(firstPage.length);
      }
    } catch (error) {
      console.error('Error loading products for vrack modal:', error);
      Alert.alert('Erreur', 'Impossible de charger les produits');
    } finally {
      setProductsLoading(false);
    }
  };

  const fetchData = async (warehouseIdOverride = null) => {
    try {
      setLoading(true);
      const normalizedOverrideId = warehouseIdOverride ? String(warehouseIdOverride).trim() : '';
      const warehouseData = await warehouseService.getWarehouses();

      const safeWarehouses = Array.isArray(warehouseData)
        ? warehouseData
            .filter((w) => w && w.id_entrepot)
            .map((w) => ({ ...w, id_entrepot: String(w.id_entrepot).trim() }))
        : [];

      const stateWarehouseId = selectedWarehouseId ? String(selectedWarehouseId).trim() : '';
      let effectiveWarehouseId = normalizedOverrideId || stateWarehouseId;
      const isKnownWarehouse = safeWarehouses.some((w) => String(w.id_entrepot) === String(effectiveWarehouseId));
      if (!isKnownWarehouse) {
        effectiveWarehouseId = '';
      }

      const [vrackData, locationData] = await Promise.all([
        warehouseService.getVracks(effectiveWarehouseId || null),
        effectiveWarehouseId ? warehouseService.getLocations(effectiveWarehouseId) : Promise.resolve([])
      ]);

      setSelectedWarehouseId(effectiveWarehouseId);
      setVracks(vrackData);
      setWarehouses(safeWarehouses);
      setLocations(locationData.filter(l => l.statut === 'AVAILABLE'));
      
      if (safeWarehouses.length > 0 && !newVrack.id_entrepot_id) {
        setNewVrack(prev => ({ ...prev, id_entrepot_id: effectiveWarehouseId || safeWarehouses[0].id_entrepot }));
      }
      if (locationData.length > 0) {
        setTransferData(prev => ({ ...prev, destination_location_id: locationData[0].id_emplacement }));
      }
    } catch (error) {
      console.error('Error fetching data:', error);
      Alert.alert('Erreur', 'Impossible de charger les données');
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

  const handleWarehouseFilterChange = async (warehouseId) => {
    setWarehouseFilterModalVisible(false);
    setFilterLoading(true);
    try {
      const selectedId = warehouseId ? String(warehouseId).trim() : '';
      setSelectedWarehouseId(selectedId);
      setRefreshing(true);
      await fetchData(selectedId);
    } catch (error) {
      console.error('Error changing vrack warehouse filter:', error);
      Alert.alert('Erreur', 'Impossible de changer le filtre entrepôt');
      setRefreshing(false);
    } finally {
      setFilterLoading(false);
    }
  };

  const handleSubmitVrack = async () => {
    if (!newVrack.id_entrepot_id || !newVrack.id_produit_id) {
      Alert.alert('Erreur', 'Veuillez sélectionner un entrepôt et un produit');
      return;
    }

    try {
      setSubmitting(true);
      if (isEditing) {
        await warehouseService.updateVrack(editingId, newVrack);
        Alert.alert('Succès', 'Vrack mis à jour avec succès');
      } else {
        await warehouseService.createVrack(newVrack);
        Alert.alert('Succès', 'Vrack ajouté avec succès');
      }
      closeModal();
      fetchData();
    } catch (error) {
      console.error('Error submitting vrack:', error);
      Alert.alert('Erreur', `Échec de l'opération: ${error.detail || 'Erreur serveur'}`);
    } finally {
      setSubmitting(false);
    }
  };

  const handleDeleteVrack = (id) => {
    Alert.alert(
      'Supprimer Vrack',
      'Êtes-vous sûr de vouloir supprimer cet enregistrement Vrack ?',
      [
        { text: 'Annuler', style: 'cancel' },
        { 
          text: 'Supprimer', 
          style: 'destructive',
          onPress: async () => {
            try {
              await warehouseService.deleteVrack(id);
              Alert.alert('Succès', 'Vrack supprimé avec succès');
              fetchData();
            } catch (error) {
              console.error('Error deleting vrack:', error);
              Alert.alert('Erreur', 'Échec de la suppression');
            }
          }
        }
      ]
    );
  };

  const openEditModal = (vrack) => {
    ensureProductsLoaded();
    setNewVrack({
      id_entrepot_id: vrack.id_entrepot.id_entrepot,
      id_produit_id: vrack.id_produit.id_produit,
      quantite: vrack.quantite.toString()
    });
    setEditingId(vrack.id_vrack);
    setIsEditing(true);
    setModalVisible(true);
  };

  const openAddModal = () => {
    ensureProductsLoaded();
    setNewVrack({
      id_entrepot_id: selectedWarehouseId || (warehouses.length > 0 ? warehouses[0].id_entrepot : ''),
      id_produit_id: products.length > 0 ? products[0].id_produit : '',
      quantite: '0'
    });
    setIsEditing(false);
    setEditingId(null);
    setModalVisible(true);
  };

  const closeModal = () => {
    setModalVisible(false);
    setIsEditing(false);
    setTransferModalVisible(false);
  };

  const openTransferModal = async (vrack) => {
    setSelectedVrack(vrack);
    try {
      const vrackWarehouseId = vrack?.id_entrepot?.id_entrepot || vrack?.id_entrepot_id;
      const locationData = await warehouseService.getLocations(vrackWarehouseId);
      const availableLocations = Array.isArray(locationData)
        ? locationData.filter((location) => location.statut === 'AVAILABLE')
        : [];
      setLocations(availableLocations);
      setTransferData({
        destination_location_id: availableLocations.length > 0 ? availableLocations[0].id_emplacement : '',
        quantity: '',
        notes: ''
      });
    } catch (error) {
      console.error('Error loading transfer locations:', error);
      setTransferData({ destination_location_id: '', quantity: '', notes: '' });
    }
    setTransferModalVisible(true);
  };

  const handleTransfer = async () => {
    if (!transferData.destination_location_id || !transferData.quantity) {
      Alert.alert('Erreur', 'Veuillez remplir la destination et la quantité');
      return;
    }

    try {
      setSubmitting(true);
      await warehouseService.transferFromVrack(selectedVrack.id_vrack, transferData);
      Alert.alert('Succès', 'Transfert effectué avec succès');
      closeModal();
      fetchData();
    } catch (error) {
      console.error('Error transferring from vrack:', error);
      Alert.alert('Erreur', `Échec du transfert: ${error.response?.data?.error || 'Erreur serveur'}`);
    } finally {
      setSubmitting(false);
    }
  };

  const renderVrackItem = ({ item }) => (
    <CollapsibleManagementCard
      title={item.id_produit.nom_produit}
      subtitle={`SKU: ${item.id_produit.sku}`}
      iconName="archive"
      iconColor="#673AB7"
      status={item.quantite > 0 ? "In Stock" : "Empty"}
      statusColor={item.quantite > 0 ? "#4CAF50" : "#F44336"}
      onEdit={() => openEditModal(item)}
      onDelete={() => handleDeleteVrack(item.id_vrack)}
      details={[
        { label: 'Entrepôt', value: item.id_entrepot.nom_entrepot },
        { label: 'Quantité', value: item.quantite.toString() },
      ]}
      customActions={[
        {
          icon: 'log-out',
          color: '#2196F3',
          onPress: () => openTransferModal(item),
          label: 'Transférer'
        }
      ]}
    />
  );

  const selectedWarehouseLabel = selectedWarehouseId
    ? (warehouses.find((warehouse) => String(warehouse.id_entrepot) === String(selectedWarehouseId))?.nom_entrepot || selectedWarehouseId)
    : 'Tous les entrepôts';
  const totalVrackQuantity = vracks.reduce((sum, vrack) => sum + Number(vrack.quantite || 0), 0);

  if (loading && !refreshing) {
    return (
      <View style={styles.centered}>
        <ActivityIndicator size="large" color={lightTheme.primary} />
      </View>
    );
  }

  return (
    <View style={styles.container}>
      <View style={styles.header}>
        <Text style={styles.title}>Gestion Vrack</Text>
        <TouchableOpacity style={styles.addButton} onPress={openAddModal}>
          <Feather name="plus" size={20} color="white" />
          <Text style={styles.addButtonText}>Ajouter</Text>
        </TouchableOpacity>
      </View>

      <View style={styles.filterCard}>
        <Text style={styles.filterLabel}>Filtre Entrepôt</Text>
        <TouchableOpacity
          style={styles.filterSelector}
          onPress={() => setWarehouseFilterModalVisible(true)}
          disabled={warehouses.length === 0 || filterLoading}
        >
          <Text style={styles.filterSelectorText}>{selectedWarehouseLabel}</Text>
          {filterLoading ? (
            <ActivityIndicator size="small" color={lightTheme.primary} />
          ) : (
            <Feather name="chevron-down" size={18} color="#666" />
          )}
        </TouchableOpacity>
      </View>

      <View style={styles.kpiRow}>
        <View style={styles.kpiCard}>
          <Text style={styles.kpiLabel}>Vracks</Text>
          <Text style={styles.kpiValue}>{vracks.length}</Text>
        </View>
        <View style={styles.kpiCard}>
          <Text style={styles.kpiLabel}>Quantité Totale</Text>
          <Text style={styles.kpiValue}>{totalVrackQuantity}</Text>
        </View>
      </View>
      
      <FlatList
        data={vracks}
        keyExtractor={(item) => item.id_vrack.toString()}
        renderItem={renderVrackItem}
        onRefresh={onRefresh}
        refreshing={refreshing}
        contentContainerStyle={styles.listContainer}
        ListEmptyComponent={
          <View style={styles.centered}>
            <Text style={styles.emptyText}>Aucun enregistrement Vrack trouvé</Text>
          </View>
        }
      />

      {/* Warehouse Filter Modal */}
      <ManagementModal
        visible={warehouseFilterModalVisible}
        onClose={() => setWarehouseFilterModalVisible(false)}
        title="Choisir Entrepôt"
        submitLabel="Appliquer"
        onSubmit={() => handleWarehouseFilterChange(selectedWarehouseId)}
      >
        <OptionSelector
          label="Entrepôt"
          options={[
            { label: "Tous les entrepôts", value: "" },
            ...warehouses.map(w => ({ 
              label: w.nom_entrepot || w.code_entrepot || String(w.id_entrepot), 
              value: String(w.id_entrepot) 
            }))
          ]}
          selectedValue={selectedWarehouseId}
          onValueChange={(val) => setSelectedWarehouseId(val)}
          icon="home"
        />
      </ManagementModal>

      {/* Add/Edit Modal */}
      <ManagementModal
        visible={modalVisible}
        onClose={closeModal}
        onSubmit={handleSubmitVrack}
        title={isEditing ? 'Modifier Vrack' : 'Ajouter Vrack'}
        submitting={submitting}
        submitLabel={isEditing ? 'Enregistrer' : 'Ajouter'}
      >
        <View style={styles.formGroup}>
          <OptionSelector
            label="Entrepôt *"
            options={warehouses.map(w => ({ label: w.nom_entrepot, value: w.id_entrepot }))}
            selectedValue={newVrack.id_entrepot_id}
            onValueChange={(val) => setNewVrack({...newVrack, id_entrepot_id: val})}
            disabled={isEditing}
            icon="home"
          />
        </View>

        <View style={styles.formGroup}>
          <OptionSelector
            label="Produit *"
            options={products.map(p => ({ label: `${p.nom_produit} (${p.sku})`, value: p.id_produit }))}
            selectedValue={newVrack.id_produit_id}
            onValueChange={(val) => setNewVrack({...newVrack, id_produit_id: val})}
            disabled={isEditing || productsLoading}
            loading={productsLoading}
            icon="package"
            placeholder={products.length === 0 ? "Aucun produit disponible" : "Sélectionner un produit"}
          />
        </View>

        <View style={styles.formGroup}>
          <Text style={styles.label}>Quantité</Text>
          <View style={styles.inputContainer}>
            <Feather name="plus-circle" size={18} color="#94A3B8" style={styles.inputIcon} />
            <TextInput
              style={styles.input}
              value={newVrack.quantite}
              onChangeText={(t) => setNewVrack({...newVrack, quantite: t})}
              placeholder="0.00"
              keyboardType="numeric"
              placeholderTextColor="#94A3B8"
            />
          </View>
        </View>
      </ManagementModal>

      {/* Transfer Modal */}
      <ManagementModal
        visible={transferModalVisible}
        onClose={closeModal}
        onSubmit={handleTransfer}
        title="Sortie de Vrack"
        submitting={submitting}
        submitLabel="Transférer"
      >
        <Text style={styles.formSubtitle}>
          {selectedVrack?.id_produit?.nom_produit} ({selectedVrack?.quantite} dispos)
        </Text>
        
        <View style={styles.formGroup}>
          <OptionSelector
            label="Emplacement Destination *"
            options={locations.map(l => ({ 
              label: `${l.code_emplacement} (${l.id_niveau})`, 
              value: l.id_emplacement 
            }))
            }
            selectedValue={transferData.destination_location_id}
            onValueChange={(val) => setTransferData({...transferData, destination_location_id: val})}
            icon="map-pin"
            placeholder={locations.length === 0 ? "Aucun emplacement disponible" : "Sélectionner un emplacement"}
          />
        </View>

        <View style={styles.formGroup}>
          <Text style={styles.label}>Quantité à déplacer *</Text>
          <View style={styles.inputContainer}>
            <Feather name="move" size={18} color="#94A3B8" style={styles.inputIcon} />
            <TextInput
              style={styles.input}
              value={transferData.quantity}
              onChangeText={(t) => setTransferData({...transferData, quantity: t})}
              placeholder="0.00"
              keyboardType="numeric"
              placeholderTextColor="#94A3B8"
            />
          </View>
        </View>

        <View style={styles.formGroup}>
          <Text style={styles.label}>Notes</Text>
          <View style={[styles.inputContainer, { height: 100, alignItems: 'flex-start', paddingTop: 12 }]}>
            <Feather name="edit-3" size={18} color="#94A3B8" style={[styles.inputIcon, { marginTop: 4 }]} />
            <TextInput
              style={[styles.input, { height: 80, textAlignVertical: 'top' }]}
              value={transferData.notes}
              onChangeText={(t) => setTransferData({...transferData, notes: t})}
              placeholder="Raison du transfert..."
              multiline
              placeholderTextColor="#94A3B8"
            />
          </View>
        </View>
      </ManagementModal>
    </View>
  );
};

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: lightTheme.white },
  centered: { flex: 1, justifyContent: 'center', alignItems: 'center' },
  emptyText: { color: '#94A3B8', marginTop: 20, fontSize: 16 },
  header: {
    paddingHorizontal: 24,
    paddingBottom: 24,
    backgroundColor: '#FFF',
    borderBottomWidth: 1,
    borderBottomColor: '#F1F5F9',
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  headerActions: { flexDirection: 'row', alignItems: 'center' },
  title: { fontSize: 28, fontWeight: '800', color: '#0F172A' },
  subtitle: { fontSize: 14, color: '#64748B', marginTop: 2 },
  addButton: {
    width: 100, height: 48, borderRadius: 14, backgroundColor: lightTheme.primary,
    justifyContent: 'center', alignItems: 'center', marginLeft: 12,
    flexDirection: 'row',
    elevation: 4, shadowColor: lightTheme.primary, shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.3, shadowRadius: 8
  },
  addButtonText: { color: '#FFF', fontWeight: '700', marginLeft: 8 },
  listContainer: { paddingVertical: 12, paddingBottom: 100 },
  filterCard: {
    backgroundColor: 'white',
    borderRadius: 16,
    padding: 16,
    marginHorizontal: 16,
    marginTop: 16,
    marginBottom: 16,
    elevation: 2,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.05,
    shadowRadius: 10,
  },
  filterLabel: {
    fontSize: 14,
    fontWeight: '700',
    color: '#475569',
    marginBottom: 8,
  },
  filterSelector: {
    backgroundColor: '#F8FAFC',
    borderRadius: 12,
    paddingHorizontal: 16,
    height: 52,
    alignItems: 'center',
    justifyContent: 'space-between',
    flexDirection: 'row',
    borderWidth: 1,
    borderColor: '#E2E8F0',
  },
  filterSelectorText: {
    fontSize: 16,
    color: '#1E293B',
    fontWeight: '600',
    flex: 1,
  },
  kpiRow: {
    flexDirection: 'row',
    gap: 12,
    paddingHorizontal: 16,
    marginBottom: 20,
  },
  kpiCard: {
    flex: 1,
    backgroundColor: 'white',
    borderRadius: 16,
    padding: 16,
    borderWidth: 1,
    borderColor: '#F1F5F9',
    elevation: 1,
  },
  kpiLabel: {
    fontSize: 13,
    color: '#64748B',
    marginBottom: 4,
    fontWeight: '600',
  },
  kpiValue: {
    fontSize: 24,
    fontWeight: '800',
    color: '#0F172A',
  },
  label: { fontSize: 14, fontWeight: '700', marginBottom: 8, color: '#475569' },
  formGroup: { marginBottom: 20 },
  formSubtitle: {
    fontSize: 15,
    color: '#64748B',
    textAlign: 'center',
    marginBottom: 20,
    lineHeight: 22,
    fontWeight: '500'
  },
  inputContainer: {
    backgroundColor: '#F8FAFC', borderRadius: 12, paddingHorizontal: 12,
    borderWidth: 1, borderColor: '#E2E8F0', flexDirection: 'row', alignItems: 'center',
    height: 54
  },
  inputIcon: { marginRight: 10 },
  pickerContainer: {
    backgroundColor: '#F8FAFC', borderRadius: 12, borderWidth: 1, borderColor: '#E2E8F0', 
    overflow: 'hidden', height: 54, justifyContent: 'center'
  },
  pickerWrapper: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingHorizontal: 12,
  },
  picker: {
    flex: 1,
    height: 54,
    marginLeft: -8, // Compensate for picker internal padding
  },
  input: { flex: 1, height: 54, fontSize: 16, color: '#1E293B' },
  productsLoadingRow: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 8,
  },
  productsLoadingText: {
    marginLeft: 10,
    color: '#94A3B8',
    fontSize: 14,
  },
});

export default VrackManagement;
