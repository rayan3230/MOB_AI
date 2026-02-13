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
import { Picker } from '@react-native-picker/picker';
import { warehouseService } from '../../../services/warehouseService';

const PAGE_SIZE = 20;
const PRELOAD_INDEX = 13;

const LocationManagement = () => {
  const [locations, setLocations] = useState([]);
  const [warehouses, setWarehouses] = useState([]);
  const [selectedWarehouseId, setSelectedWarehouseId] = useState('');
  const [warehouseFilterModalVisible, setWarehouseFilterModalVisible] = useState(false);
  const [floors, setFloors] = useState([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [filterLoading, setFilterLoading] = useState(false);
  const [loadingMore, setLoadingMore] = useState(false);
  const [currentOffset, setCurrentOffset] = useState(0);
  const [hasMore, setHasMore] = useState(false);
  const [modalVisible, setModalVisible] = useState(false);
  const [isEditing, setIsEditing] = useState(false);
  const [editingId, setEditingId] = useState(null);
  const [submitting, setSubmitting] = useState(false);

  const [newLocation, setNewLocation] = useState({
    code_emplacement: '',
    id_entrepot_id: '',
    id_niveau_id: '',
    zone: '',
    type_emplacement: 'STORAGE',
    statut: 'AVAILABLE',
    actif: true
  });

  const paginationStateRef = useRef({
    loading: true,
    refreshing: false,
    loadingMore: false,
    hasMore: false,
    currentOffset: 0,
    selectedWarehouseId: '',
    locationsLength: 0,
  });
  const viewabilityConfig = useRef({ itemVisiblePercentThreshold: 40 });

  paginationStateRef.current = {
    loading,
    refreshing,
    loadingMore,
    hasMore,
    currentOffset,
    selectedWarehouseId,
    locationsLength: locations.length,
  };

  const fetchData = async (warehouseIdOverride = null) => {
    try {
      setLoading(true);
      const normalizedOverrideId = warehouseIdOverride
        ? String(warehouseIdOverride).trim().replace(/^"|"$/g, '')
        : '';

      const whData = await warehouseService.getWarehouses();
      const safeWarehouses = Array.isArray(whData)
        ? whData
            .filter((w) => w && (w.id_entrepot || w.id))
            .map((w) => ({
              ...w,
              id_entrepot: String(w.id_entrepot || w.id).trim(),
              nom_entrepot: w.nom_entrepot || w.code_entrepot || String(w.id_entrepot || w.id),
            }))
        : [];
      setWarehouses(safeWarehouses);

      const stateWarehouseId = selectedWarehouseId
        ? String(selectedWarehouseId).trim().replace(/^"|"$/g, '')
        : '';
      let effectiveWarehouseId = normalizedOverrideId || stateWarehouseId;
      const isKnownWarehouse = safeWarehouses.some((w) => String(w.id_entrepot) === String(effectiveWarehouseId));
      if (!isKnownWarehouse) {
        effectiveWarehouseId = '';
      }

      setSelectedWarehouseId(effectiveWarehouseId || '');

      if (!effectiveWarehouseId) {
        setLocations([]);
        setFloors([]);
        return;
      }

      const [locsResponse, stockFloors, pickingFloors] = await Promise.all([
        warehouseService.getLocationsPaged(effectiveWarehouseId, { limit: PAGE_SIZE, offset: 0 }),
        warehouseService.getFloors(effectiveWarehouseId),
        warehouseService.getPickingFloors(effectiveWarehouseId)
      ]);

      const firstPageLocations = Array.isArray(locsResponse?.results) ? locsResponse.results : [];
      setLocations(firstPageLocations);
      setCurrentOffset(firstPageLocations.length);
      setHasMore(Boolean(locsResponse?.has_more));
      
      const safeStockFloors = Array.isArray(stockFloors) ? stockFloors : [];
      const safePickingFloors = Array.isArray(pickingFloors) ? pickingFloors : [];
      
      const allFloors = [
        ...safeStockFloors.map(f => ({ ...f, id_niveau: f.id_niveau })),
        ...safePickingFloors.map(f => ({ ...f, id_niveau: f.id_niveau_picking }))
      ];
      
      setFloors(allFloors);
      setNewLocation((prev) => ({
        ...prev,
        id_entrepot_id: prev.id_entrepot_id || effectiveWarehouseId,
      }));
    } catch (error) {
      console.error('Error fetching data:', error);
      Alert.alert('Error', 'Failed to load locations, warehouses or floors');
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

  const loadMoreLocations = useCallback(async () => {
    const state = paginationStateRef.current;
    if (state.loading || state.refreshing || state.loadingMore || !state.hasMore || !state.selectedWarehouseId) {
      return;
    }

    try {
      setLoadingMore(true);
      const response = await warehouseService.getLocationsPaged(state.selectedWarehouseId, {
        limit: PAGE_SIZE,
        offset: state.currentOffset,
      });

      const nextLocations = Array.isArray(response?.results) ? response.results : [];
      if (nextLocations.length > 0) {
        setLocations((prev) => [...prev, ...nextLocations]);
        setCurrentOffset((prev) => prev + nextLocations.length);
      }
      setHasMore(Boolean(response?.has_more));
    } catch (error) {
      console.error('Error loading more locations:', error);
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

    const preloadTrigger = Math.max(PRELOAD_INDEX, state.locationsLength - (PAGE_SIZE - PRELOAD_INDEX));
    if (maxVisibleIndex >= preloadTrigger) {
      loadMoreLocations();
    }
  }, [loadMoreLocations]);

  const handleWarehouseFilterChange = async (warehouseId) => {
    setFilterLoading(true);
    try {
      const normalizedWarehouseId = warehouseId ? String(warehouseId).trim() : '';
      setSelectedWarehouseId(normalizedWarehouseId);

      setNewLocation((prev) => ({
        ...prev,
        id_entrepot_id: normalizedWarehouseId,
        id_niveau_id: '',
      }));

      setRefreshing(true);
      await fetchData(normalizedWarehouseId);
    } catch (error) {
      console.error('Error changing warehouse filter:', error);
      setRefreshing(false);
      Alert.alert('Error', 'Failed to change warehouse filter');
    } finally {
      setFilterLoading(false);
    }
  };

  const handleSubmitLocation = async () => {
    if (!newLocation.code_emplacement || !newLocation.id_entrepot_id) {
      Alert.alert('Error', 'Please fill in required fields (Code and Warehouse)');
      return;
    }

    try {
      setSubmitting(true);
      
      // Determine which floor field to use
      const selectedFloor = floors.find(f => f.id_niveau === newLocation.id_niveau_id);
      const submissionData = { ...newLocation };
      
      if (selectedFloor) {
        if (selectedFloor.type_niveau === 'PICKING') {
          submissionData.picking_floor_id = selectedFloor.id_niveau;
          delete submissionData.id_niveau_id;
        } else {
          submissionData.storage_floor_id = selectedFloor.id_niveau;
          delete submissionData.id_niveau_id;
        }
      } else {
        delete submissionData.id_niveau_id;
      }

      if (isEditing) {
        await warehouseService.updateLocation(editingId, submissionData);
        Alert.alert('Success', 'Location updated successfully');
      } else {
        await warehouseService.createLocation(submissionData);
        Alert.alert('Success', 'Location added successfully');
      }
      closeModal();
      fetchData();
    } catch (error) {
      console.error('Error submitting location:', error);
      Alert.alert('Error', `Failed to ${isEditing ? 'update' : 'add'} location`);
    } finally {
      setSubmitting(false);
    }
  };

  const handleDeleteLocation = (id) => {
    Alert.alert(
      'Delete Location',
      'Are you sure you want to delete this location?',
      [
        { text: 'Cancel', style: 'cancel' },
        { 
          text: 'Delete', 
          style: 'destructive',
          onPress: async () => {
            try {
              await warehouseService.deleteLocation(id);
              Alert.alert('Success', 'Location deleted successfully');
              fetchData();
            } catch (error) {
              console.error('Error deleting location:', error);
              Alert.alert('Error', 'Failed to delete location');
            }
          }
        }
      ]
    );
  };

  const openEditModal = (loc) => {
    setNewLocation({
      code_emplacement: loc.code_emplacement,
      id_entrepot_id: loc.id_entrepot?.id_entrepot || loc.id_entrepot,
      id_niveau_id: loc.storage_floor?.id_niveau || loc.picking_floor?.id_niveau_picking || '',
      zone: loc.zone || '',
      type_emplacement: loc.type_emplacement || 'STORAGE',
      statut: loc.statut || 'AVAILABLE',
      actif: loc.actif ?? true
    });
    setEditingId(loc.id_emplacement);
    setIsEditing(true);
    setModalVisible(true);
  };

  const openAddModal = () => {
    setNewLocation({
      code_emplacement: '',
      id_entrepot_id: selectedWarehouseId || (warehouses.length > 0 ? warehouses[0].id_entrepot : ''),
      id_niveau_id: '',
      zone: '',
      type_emplacement: 'STORAGE',
      statut: 'AVAILABLE',
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

  const getStatusColor = (status) => {
    switch (status) {
      case 'AVAILABLE': return '#4CAF50';
      case 'OCCUPIED': return '#2196F3';
      case 'BLOCKED': return '#F44336';
      default: return '#757575';
    }
  };

  const renderLocationItem = ({ item }) => (
    <View style={styles.card}>
      <View style={styles.infoContainer}>
        <View style={styles.row}>
          <Text style={styles.codeText}>{item.code_emplacement}</Text>
          <View style={[styles.statusBadge, { backgroundColor: getStatusColor(item.statut) }]}>
            <Text style={styles.statusText}>{item.statut}</Text>
          </View>
        </View>
        
        <Text style={styles.subText}>
          <Feather name="home" size={12} /> {item.id_entrepot?.nom_entrepot || 'N/A'} 
          {item.storage_floor ? ` • ${item.storage_floor.code_niveau}` : (item.picking_floor ? ` • ${item.picking_floor.code_niveau}` : '')}
        </Text>
        
        {item.zone ? (
          <Text style={styles.zoneText}>Zone: {item.zone}</Text>
        ) : null}
        
        <Text style={styles.typeText}>{item.type_emplacement}</Text>
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
          onPress={() => handleDeleteLocation(item.id_emplacement)}
        >
          <Feather name="trash-2" size={18} color="#F44336" />
        </TouchableOpacity>
      </View>
    </View>
  );

  const filteredFloors = floors.filter((f) => {
    const floorWarehouseId = f.id_entrepot?.id_entrepot || f.id_entrepot;
    return String(floorWarehouseId) === String(newLocation.id_entrepot_id);
  });

  const selectedWarehouseLabel = warehouses.find(
    (w) => String(w.id_entrepot) === String(selectedWarehouseId)
  )?.nom_entrepot || 'Select a warehouse';

  if (loading && !refreshing) {
    return (
      <View style={styles.centered}>
        <ActivityIndicator size="large" color="#2196F3" />
      </View>
    );
  }

  // Check if active warehouse is selected
  return (
    <View style={styles.container}>
      <View style={styles.header}>
        <Text style={styles.title}>Locations</Text>
        <TouchableOpacity 
          style={styles.addButton} 
          onPress={openAddModal}
        >
          <Text style={styles.addButtonText}>+ Add Location</Text>
        </TouchableOpacity>
      </View>

      <View style={styles.filterCard}>
        <Text style={styles.filterLabel}>Warehouse Filter</Text>
        <TouchableOpacity
          style={styles.filterSelector}
          onPress={() => setWarehouseFilterModalVisible(true)}
          disabled={warehouses.length === 0 || filterLoading}
        >
          <Text style={styles.filterSelectorText}>{selectedWarehouseLabel}</Text>
          {filterLoading ? (
            <ActivityIndicator size="small" color="#2196F3" />
          ) : (
            <Feather name="chevron-down" size={18} color="#666" />
          )}
        </TouchableOpacity>
      </View>

      {filterLoading ? (
        <View style={styles.switchLoadingContainer}>
          <ActivityIndicator size="small" color="#2196F3" />
          <Text style={styles.switchLoadingText}>Loading locations...</Text>
        </View>
      ) : null}
      
      {locations.length === 0 ? (
        <View style={styles.centered}>
          <Feather name="layers" size={48} color="#ccc" />
          <Text style={styles.emptyText}>
            {floors.length === 0 ? "No warehouse selected or no floors found. Please select a warehouse in Warehouse Management." : "No locations found"}
          </Text>
        </View>
      ) : (
        <FlatList
          data={locations}
          keyExtractor={(item) => String(item.id_emplacement)}
          renderItem={renderLocationItem}
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
        animationType="slide"
        transparent={true}
        visible={modalVisible}
        onRequestClose={closeModal}
      >
        <View style={styles.modalOverlay}>
          <View style={styles.modalContent}>
            <View style={styles.modalHandle} />
            <Text style={styles.modalTitle}>
              {isEditing ? 'Edit Location' : 'Add New Location'}
            </Text>
            
            <ScrollView style={styles.form}>
              <Text style={styles.label}>Warehouse *</Text>
              <View style={styles.pickerContainer}>
                <Picker
                  selectedValue={newLocation.id_entrepot_id}
                  onValueChange={(val) => setNewLocation({...newLocation, id_entrepot_id: val, id_niveau_id: ''})}
                  style={styles.picker}
                  mode="dialog"
                >
                  {warehouses.map(w => (
                    <Picker.Item key={String(w.id_entrepot)} label={w.nom_entrepot || w.code_entrepot || String(w.id_entrepot)} value={String(w.id_entrepot)} />
                  ))}
                </Picker>
              </View>

              <Text style={styles.label}>Floor (Optional)</Text>
              <View style={styles.pickerContainer}>
                <Picker
                  selectedValue={newLocation.id_niveau_id}
                  onValueChange={(val) => {
                    const selectedFloor = floors.find(f => f.id_niveau === val);
                    const newType = (selectedFloor && selectedFloor.type_niveau === 'PICKING') ? 'PICKING' : 'STORAGE';
                    setNewLocation({
                      ...newLocation, 
                      id_niveau_id: val,
                      type_emplacement: newType
                    });
                  }}
                  style={styles.picker}
                >
                  <Picker.Item label="Non Assigned" value="" />
                  {filteredFloors.map(f => (
                    <Picker.Item key={f.id_niveau} label={f.code_niveau} value={f.id_niveau} />
                  ))}
                </Picker>
              </View>

              <Text style={styles.label}>Location Code * (e.g., FR-17, A-01-01)</Text>
              <TextInput
                style={styles.input}
                value={newLocation.code_emplacement}
                onChangeText={(t) => setNewLocation({...newLocation, code_emplacement: t})}
                placeholder="Enter unique code"
              />

              <Text style={styles.label}>Zone</Text>
              <TextInput
                style={styles.input}
                value={newLocation.zone}
                onChangeText={(t) => setNewLocation({...newLocation, zone: t})}
                placeholder="e.g., Receiving, Picking"
              />

              <Text style={styles.label}>Type</Text>
              <View style={styles.pickerContainer}>
                <Picker
                  selectedValue={newLocation.type_emplacement}
                  onValueChange={(val) => setNewLocation({...newLocation, type_emplacement: val})}
                  style={styles.picker}
                >
                  <Picker.Item label="Storage" value="STORAGE" />
                  <Picker.Item label="Picking" value="PICKING" />
                </Picker>
              </View>

              <Text style={styles.label}>Status</Text>
              <View style={styles.pickerContainer}>
                <Picker
                  selectedValue={newLocation.statut}
                  onValueChange={(val) => setNewLocation({...newLocation, statut: val})}
                  style={styles.picker}
                >
                  <Picker.Item label="Available" value="AVAILABLE" />
                  <Picker.Item label="Occupied" value="OCCUPIED" />
                  <Picker.Item label="Blocked" value="BLOCKED" />
                </Picker>
              </View>

              <View style={styles.switchRow}>
                <Text style={styles.label}>Active</Text>
                <Switch
                  value={newLocation.actif}
                  onValueChange={(val) => setNewLocation({...newLocation, actif: val})}
                />
              </View>
            </ScrollView>

            <View style={styles.modalButtons}>
              <TouchableOpacity 
                style={[styles.modalButton, styles.cancelButton]} 
                onPress={closeModal}
                disabled={submitting}
              >
                <Text style={styles.cancelButtonText}>Cancel</Text>
              </TouchableOpacity>
              <TouchableOpacity 
                style={[styles.modalButton, styles.saveButton]} 
                onPress={handleSubmitLocation}
                disabled={submitting}
              >
                {submitting ? (
                  <ActivityIndicator color="white" size="small" />
                ) : (
                  <Text style={styles.saveButtonText}>{isEditing ? 'Update' : 'Save'}</Text>
                )}
              </TouchableOpacity>
            </View>
          </View>
        </View>
      </Modal>

      <Modal
        animationType="fade"
        transparent={true}
        visible={warehouseFilterModalVisible}
        onRequestClose={() => setWarehouseFilterModalVisible(false)}
      >
        <View style={styles.filterModalOverlay}>
          <View style={styles.filterModalContent}>
            <Text style={styles.filterModalTitle}>Select Warehouse</Text>
            <ScrollView>
              {warehouses.length > 0 ? (
                warehouses.map((warehouse) => {
                  const warehouseId = String(warehouse.id_entrepot);
                  const isSelected = warehouseId === String(selectedWarehouseId);
                  return (
                    <TouchableOpacity
                      key={warehouseId}
                      style={[styles.filterOption, isSelected && styles.filterOptionSelected]}
                      onPress={async () => {
                        setWarehouseFilterModalVisible(false);
                        await handleWarehouseFilterChange(warehouseId);
                      }}
                    >
                      <Text style={[styles.filterOptionText, isSelected && styles.filterOptionTextSelected]}>
                        {warehouse.nom_entrepot || warehouse.code_entrepot || warehouseId}
                      </Text>
                    </TouchableOpacity>
                  );
                })
              ) : (
                <Text style={styles.filterEmptyText}>No warehouses available</Text>
              )}
            </ScrollView>
            <TouchableOpacity
              style={styles.filterCloseButton}
              onPress={() => setWarehouseFilterModalVisible(false)}
            >
              <Text style={styles.filterCloseButtonText}>Close</Text>
            </TouchableOpacity>
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
    padding: 20,
  },
  emptyText: {
    fontSize: 16,
    color: '#666',
    textAlign: 'center',
    marginTop: 12,
  },
  header: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 16,
    marginTop: 8,
  },
  title: {
    fontSize: 24,
    fontWeight: 'bold',
    color: '#333',
  },
  addButton: {
    backgroundColor: '#4CAF50',
    paddingHorizontal: 12,
    paddingVertical: 8,
    borderRadius: 8,
    elevation: 2,
  },
  addButtonText: {
    color: 'white',
    fontWeight: 'bold',
  },
  listContainer: {
    paddingBottom: 20,
  },
  filterCard: {
    backgroundColor: 'white',
    borderRadius: 10,
    padding: 12,
    marginBottom: 12,
    elevation: 1,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 1 },
    shadowOpacity: 0.06,
    shadowRadius: 2,
  },
  filterLabel: {
    fontSize: 13,
    fontWeight: '600',
    color: '#555',
    marginBottom: 6,
  },
  filterSelector: {
    backgroundColor: '#f8f9fa',
    borderWidth: 1,
    borderColor: '#e9ecef',
    borderRadius: 8,
    paddingHorizontal: 12,
    height: 48,
    alignItems: 'center',
    justifyContent: 'space-between',
    flexDirection: 'row',
  },
  filterSelectorText: {
    fontSize: 15,
    color: '#333',
    flex: 1,
    marginRight: 8,
  },
  switchLoadingContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 10,
    paddingHorizontal: 4,
  },
  switchLoadingText: {
    marginLeft: 8,
    color: '#666',
    fontSize: 13,
  },
  filterModalOverlay: {
    flex: 1,
    backgroundColor: 'rgba(0,0,0,0.45)',
    justifyContent: 'center',
    padding: 20,
  },
  filterModalContent: {
    backgroundColor: 'white',
    borderRadius: 12,
    maxHeight: '70%',
    padding: 16,
  },
  filterModalTitle: {
    fontSize: 18,
    fontWeight: '700',
    color: '#333',
    marginBottom: 12,
  },
  filterOption: {
    paddingVertical: 12,
    paddingHorizontal: 10,
    borderRadius: 8,
    marginBottom: 6,
    backgroundColor: '#f8f9fa',
  },
  filterOptionSelected: {
    backgroundColor: '#E3F2FD',
  },
  filterOptionText: {
    fontSize: 15,
    color: '#333',
  },
  filterOptionTextSelected: {
    color: '#1565C0',
    fontWeight: '600',
  },
  filterEmptyText: {
    fontSize: 14,
    color: '#666',
    textAlign: 'center',
    paddingVertical: 16,
  },
  filterCloseButton: {
    marginTop: 10,
    paddingVertical: 10,
    borderRadius: 8,
    backgroundColor: '#f1f3f5',
    alignItems: 'center',
  },
  filterCloseButtonText: {
    color: '#495057',
    fontWeight: '600',
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
  codeText: {
    fontSize: 18,
    fontWeight: 'bold',
    color: '#2c3e50',
    marginRight: 8,
  },
  statusBadge: {
    paddingHorizontal: 8,
    paddingVertical: 2,
    borderRadius: 4,
  },
  statusText: {
    color: 'white',
    fontSize: 10,
    fontWeight: 'bold',
  },
  subText: {
    fontSize: 14,
    color: '#666',
    marginBottom: 4,
  },
  zoneText: {
    fontSize: 14,
    color: '#7f8c8d',
    fontStyle: 'italic',
  },
  typeText: {
    fontSize: 12,
    color: '#95a5a6',
    fontWeight: '600',
    marginTop: 4,
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
    color: '#333',
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
  pickerContainer: {
    backgroundColor: '#f8f9fa',
    borderWidth: 1,
    borderColor: '#e9ecef',
    borderRadius: 8,
    overflow: 'hidden',
  },
  picker: {
    height: 50,
    width: '100%',
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
    fontSize: 16,
  },
  cancelButtonText: {
    color: '#495057',
    fontWeight: 'bold',
    fontSize: 16,
  },
  footerLoader: {
    paddingVertical: 12,
  },
});

export default LocationManagement;
