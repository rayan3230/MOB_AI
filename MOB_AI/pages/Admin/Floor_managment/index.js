import React, { useState, useEffect, useRef } from 'react';
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
  ScrollView
} from 'react-native';
import { Feather } from '@expo/vector-icons';
import { Picker } from '@react-native-picker/picker';
import { warehouseService } from '../../../services/warehouseService';

const FLOOR_CACHE_TTL_MS = 2 * 60 * 1000;

const FloorManagement = () => {
  const [floors, setFloors] = useState([]);
  const [warehouses, setWarehouses] = useState([]);
  const [selectedWarehouseId, setSelectedWarehouseId] = useState('');
  const [warehouseFilterModalVisible, setWarehouseFilterModalVisible] = useState(false);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [filterLoading, setFilterLoading] = useState(false);
  const [modalVisible, setModalVisible] = useState(false);
  const [isEditing, setIsEditing] = useState(false);
  const [editingId, setEditingId] = useState(null);
  const [submitting, setSubmitting] = useState(false);

  const [newFloor, setNewFloor] = useState({
    code_niveau: '',
    type_niveau: 'STOCK',
    description: '',
    id_entrepot_id: ''
  });

  const floorsCacheRef = useRef({});

  const normalizeFloors = (floors) => {
    if (!Array.isArray(floors)) {
      return [];
    }

    return floors.map((floor) => ({
      ...floor,
      id_niveau: floor.id_niveau || floor.id_niveau_picking,
      type_niveau: floor.type_niveau || (floor.id_niveau_picking ? 'PICKING' : 'STOCK'),
    }));
  };

  const getCachedFloors = (warehouseId) => {
    const cacheEntry = floorsCacheRef.current[String(warehouseId)];
    if (!cacheEntry) {
      return null;
    }

    const isFresh = Date.now() - cacheEntry.cachedAt < FLOOR_CACHE_TTL_MS;
    return isFresh ? cacheEntry.data : null;
  };

  const setCachedFloors = (warehouseId, floors) => {
    floorsCacheRef.current[String(warehouseId)] = {
      data: floors,
      cachedAt: Date.now(),
    };
  };

  const fetchFloorsForWarehouse = async (warehouseId, { forceRefresh = false } = {}) => {
    const key = String(warehouseId);

    if (!forceRefresh) {
      const cached = getCachedFloors(key);
      if (cached) {
        return cached;
      }
    }

    const rawFloors = await warehouseService.getWarehouseFloors(key);
    const normalized = normalizeFloors(rawFloors);
    setCachedFloors(key, normalized);
    return normalized;
  };

  const fetchData = async (warehouseIdOverride = null, { forceRefresh = false } = {}) => {
    try {
      setLoading(true);
      const normalizedOverrideWhId = warehouseIdOverride
        ? String(warehouseIdOverride).trim().replace(/^"|"$/g, '')
        : '';

      const warehousesData = await warehouseService.getWarehouses();
      const safeWarehouses = Array.isArray(warehousesData) ? warehousesData : [];
      setWarehouses(safeWarehouses);

      const normalizedSelectedWhId = selectedWarehouseId
        ? String(selectedWarehouseId).trim().replace(/^"|"$/g, '')
        : '';
      const effectiveWhId = normalizedOverrideWhId || normalizedSelectedWhId;
      const isKnownWarehouse = safeWarehouses.some((w) => String(w.id_entrepot) === String(effectiveWhId));

      if (safeWarehouses.length === 0) {
        setFloors([]);
        setSelectedWarehouseId('');
        setNewFloor((prev) => ({ ...prev, id_entrepot_id: '' }));
        return;
      }

      if (!effectiveWhId || !isKnownWarehouse) {
        const floorsByWarehouse = await Promise.all(
          safeWarehouses.map((warehouse) =>
            fetchFloorsForWarehouse(String(warehouse.id_entrepot), { forceRefresh })
          )
        );
        setSelectedWarehouseId('');
        setFloors(floorsByWarehouse.flat());
        setNewFloor((prev) => ({ ...prev, id_entrepot_id: prev.id_entrepot_id || String(safeWarehouses[0].id_entrepot) }));
        return;
      }

      const warehouseFloors = await fetchFloorsForWarehouse(effectiveWhId, { forceRefresh });
      setSelectedWarehouseId(effectiveWhId);
      setFloors(warehouseFloors);
      setNewFloor((prev) => ({ ...prev, id_entrepot_id: effectiveWhId }));
    } catch (error) {
      console.error('Error fetching data:', error);
      Alert.alert('Error', 'Failed to load floors or warehouses');
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
    fetchData(selectedWarehouseId, { forceRefresh: true });
  };

  const handleWarehouseFilterChange = async (warehouseId) => {
    setWarehouseFilterModalVisible(false);
    setFilterLoading(true);
    try {
      const selectedId = warehouseId ? String(warehouseId) : '';
      setSelectedWarehouseId(selectedId);
      setRefreshing(true);
      await fetchData(selectedId, { forceRefresh: false });
    } catch (error) {
      console.error('Error changing floor warehouse filter:', error);
      setRefreshing(false);
      Alert.alert('Error', 'Failed to change warehouse filter');
    } finally {
      setFilterLoading(false);
    }
  };

  const handleSubmitFloor = async () => {
    if (!newFloor.code_niveau || !newFloor.id_entrepot_id) {
      Alert.alert('Error', 'Please fill in required fields (Code and Warehouse)');
      return;
    }

    try {
      setSubmitting(true);
      if (isEditing) {
        await warehouseService.updateFloor(editingId, newFloor);
        Alert.alert('Success', 'Floor updated successfully');
      } else {
        await warehouseService.createFloor(newFloor);
        Alert.alert('Success', 'Floor added successfully');
      }
      floorsCacheRef.current = {};
      closeModal();
      fetchData(selectedWarehouseId, { forceRefresh: true });
    } catch (error) {
      console.error('Error submitting floor:', error);
      // Display the specific error message from the backend if available
      const backendError = error.error || error.detail || error.non_field_errors?.[0];
      Alert.alert('Error', backendError || `Failed to ${isEditing ? 'update' : 'add'} floor`);
    } finally {
      setSubmitting(false);
    }
  };

  const handleDeleteFloor = (id, type) => {
    Alert.alert(
      'Delete Floor',
      'Are you sure you want to delete this floor?',
      [
        { text: 'Cancel', style: 'cancel' },
        { 
          text: 'Delete', 
          style: 'destructive',
          onPress: async () => {
            try {
              await warehouseService.deleteFloor(id, type);
              Alert.alert('Success', 'Floor deleted successfully');
              floorsCacheRef.current = {};
              fetchData(selectedWarehouseId, { forceRefresh: true });
            } catch (error) {
              console.error('Error deleting floor:', error);
              Alert.alert('Error', 'Failed to delete floor');
            }
          }
        }
      ]
    );
  };

  const openEditModal = (floor) => {
    setNewFloor({
      code_niveau: floor.code_niveau,
      type_niveau: floor.type_niveau || 'STOCK',
      description: floor.description || '',
      id_entrepot_id: floor.id_entrepot?.id_entrepot || floor.id_entrepot
    });
    setEditingId(floor.id_niveau);
    setIsEditing(true);
    setModalVisible(true);
  };

  const openAddModal = () => {
    setNewFloor({
      code_niveau: '',
      type_niveau: 'STOCK',
      description: '',
      id_entrepot_id: selectedWarehouseId || (warehouses.length > 0 ? warehouses[0].id_entrepot : '')
    });
    setIsEditing(false);
    setEditingId(null);
    setModalVisible(true);
  };

  const closeModal = () => {
    setModalVisible(false);
    setNewFloor({
      code_niveau: '',
      type_niveau: 'STOCK',
      description: '',
      id_entrepot_id: ''
    });
    setIsEditing(false);
    setEditingId(null);
  };

  const renderFloorItem = ({ item }) => (
    <View style={styles.floorCard}>
      <View style={styles.floorInfo}>
        <View style={styles.row}>
          <Text style={styles.floorCode}>{item.code_niveau}</Text>
          <View style={[styles.typeBadge, { backgroundColor: item.type_niveau === 'PICKING' ? '#FF9800' : '#4CAF50' }]}>
            <Text style={styles.typeText}>{item.type_niveau}</Text>
          </View>
        </View>
        <Text style={styles.warehouseName}>
          {item.id_entrepot?.nom_entrepot || 'Unknown Warehouse'}
        </Text>
        {item.description ? (
          <Text style={styles.description}>{item.description}</Text>
        ) : null}
      </View>
      
      <View style={styles.actionButtons}>
        <TouchableOpacity 
          style={[styles.actionButton, styles.editButton]} 
          onPress={() => openEditModal(item)}
        >
          <Feather name="edit-2" size={18} color="#2196F3" />
        </TouchableOpacity>
        <TouchableOpacity 
          style={[styles.actionButton, styles.deleteButton]} 
          onPress={() => handleDeleteFloor(item.id_niveau, item.type_niveau)}
        >
          <Feather name="trash-2" size={18} color="#F44336" />
        </TouchableOpacity>
      </View>
    </View>
  );

  const selectedWarehouseLabel = selectedWarehouseId
    ? (warehouses.find((warehouse) => String(warehouse.id_entrepot) === String(selectedWarehouseId))?.nom_entrepot || selectedWarehouseId)
    : 'All Warehouses';

  if (loading && !refreshing) {
    return (
      <View style={styles.centered}>
        <ActivityIndicator size="large" color="#2196F3" />
      </View>
    );
  }

  return (
    <View style={styles.container}>
      <View style={styles.header}>
        <Text style={styles.title}>Floors</Text>
        <View style={styles.headerButtons}>
          <TouchableOpacity 
            style={[styles.headerButton, styles.addButton]} 
            onPress={openAddModal}
          >
            <Text style={styles.buttonText}>+ Add</Text>
          </TouchableOpacity>
        </View>
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
          <Text style={styles.switchLoadingText}>Loading floors...</Text>
        </View>
      ) : null}
      
      {floors.length === 0 ? (
        <View style={styles.centered}>
          <Text style={styles.text}>No floors found</Text>
        </View>
      ) : (
        <FlatList
          data={floors}
          keyExtractor={(item) => item.id_niveau}
          renderItem={renderFloorItem}
          contentContainerStyle={styles.listContent}
          onRefresh={onRefresh}
          refreshing={refreshing}
        />
      )}

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
              <TouchableOpacity
                style={[styles.filterOption, !selectedWarehouseId && styles.filterOptionSelected]}
                onPress={() => handleWarehouseFilterChange('')}
              >
                <Text style={[styles.filterOptionText, !selectedWarehouseId && styles.filterOptionTextSelected]}>All Warehouses</Text>
              </TouchableOpacity>

              {warehouses.map((warehouse) => {
                const warehouseId = String(warehouse.id_entrepot);
                const isSelected = warehouseId === String(selectedWarehouseId);
                return (
                  <TouchableOpacity
                    key={warehouseId}
                    style={[styles.filterOption, isSelected && styles.filterOptionSelected]}
                    onPress={() => handleWarehouseFilterChange(warehouseId)}
                  >
                    <Text style={[styles.filterOptionText, isSelected && styles.filterOptionTextSelected]}>
                      {warehouse.nom_entrepot || warehouse.code_entrepot || warehouseId}
                    </Text>
                  </TouchableOpacity>
                );
              })}
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

      <Modal
        animationType="slide"
        transparent={true}
        visible={modalVisible}
        onRequestClose={closeModal}
      >
        <View style={styles.modalOverlay}>
          <View style={styles.modalContent}>
            <View style={styles.modalHandle} />
            <Text style={styles.modalTitle}>{isEditing ? 'Edit Floor' : 'Add New Floor'}</Text>
            <ScrollView style={styles.modalForm}>
              <Text style={styles.label}>Warehouse *</Text>
              <View style={styles.pickerContainer}>
                <Picker
                  selectedValue={newFloor.id_entrepot_id}
                  onValueChange={(value) => setNewFloor({...newFloor, id_entrepot_id: value})}
                  style={styles.picker}
                >
                  {warehouses.map((w) => (
                    <Picker.Item key={w.id_entrepot} label={w.nom_entrepot} value={w.id_entrepot} />
                  ))}
                </Picker>
              </View>

              <Text style={styles.label}>Floor Code * (e.g., N1, N2)</Text>
              <TextInput
                style={styles.input}
                placeholder="e.g., N1"
                value={newFloor.code_niveau}
                onChangeText={(text) => setNewFloor({...newFloor, code_niveau: text})}
              />

              <Text style={styles.label}>Floor Type</Text>
              <View style={styles.pickerContainer}>
                <Picker
                  selectedValue={newFloor.type_niveau}
                  onValueChange={(value) => setNewFloor({...newFloor, type_niveau: value})}
                  style={styles.picker}
                >
                  <Picker.Item label="Stocking Level" value="STOCK" />
                  <Picker.Item label="Picking Level" value="PICKING" />
                </Picker>
              </View>

              <Text style={styles.label}>Description</Text>
              <TextInput
                style={styles.input}
                placeholder="e.g., Ground Floor Storage"
                value={newFloor.description}
                onChangeText={(text) => setNewFloor({...newFloor, description: text})}
              />
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
                onPress={handleSubmitFloor}
                disabled={submitting}
              >
                {submitting ? (
                  <ActivityIndicator size="small" color="white" />
                ) : (
                  <Text style={styles.saveButtonText}>{isEditing ? 'Update Floor' : 'Add Floor'}</Text>
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
  header: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 20,
    marginTop: 10,
  },
  title: {
    fontSize: 24,
    fontWeight: 'bold',
    color: '#333',
  },
  headerButtons: {
    flexDirection: 'row',
  },
  headerButton: {
    paddingHorizontal: 12,
    paddingVertical: 8,
    borderRadius: 6,
    marginLeft: 8,
    elevation: 2,
  },
  addButton: {
    backgroundColor: '#4CAF50',
  },
  buttonText: {
    color: 'white',
    fontWeight: 'bold',
  },
  centered: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
  },
  listContent: {
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
  floorCard: {
    backgroundColor: 'white',
    borderRadius: 8,
    padding: 16,
    marginBottom: 12,
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    elevation: 2,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 1 },
    shadowOpacity: 0.2,
    shadowRadius: 1,
  },
  floorInfo: {
    flex: 1,
  },
  row: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 4,
  },
  typeBadge: {
    paddingHorizontal: 8,
    paddingVertical: 2,
    borderRadius: 4,
    marginLeft: 10,
  },
  typeText: {
    color: 'white',
    fontSize: 10,
    fontWeight: 'bold',
    textTransform: 'uppercase',
  },
  floorCode: {
    fontSize: 18,
    fontWeight: 'bold',
    color: '#2196F3',
  },
  warehouseName: {
    fontSize: 14,
    color: '#666',
    fontWeight: '600',
    marginBottom: 4,
  },
  description: {
    fontSize: 14,
    color: '#888',
    fontStyle: 'italic',
  },
  actionButtons: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  actionButton: {
    padding: 8,
    marginLeft: 4,
    borderRadius: 8,
    backgroundColor: '#F5F5F5',
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
    width: '100%',
    maxHeight: '85%',
    elevation: 5,
  },
  modalHandle: {
    width: 40,
    height: 5,
    backgroundColor: '#dbdbdb',
    borderRadius: 2.5,
    alignSelf: 'center',
    marginBottom: 15,
  },
  modalTitle: {
    fontSize: 20,
    fontWeight: 'bold',
    marginBottom: 20,
    textAlign: 'center',
    color: '#333',
  },
  modalForm: {
    marginBottom: 20,
  },
  label: {
    fontSize: 14,
    fontWeight: '600',
    color: '#666',
    marginBottom: 4,
    marginTop: 12,
  },
  input: {
    borderWidth: 1,
    borderColor: '#ddd',
    borderRadius: 6,
    padding: 10,
    fontSize: 16,
    color: '#333',
    backgroundColor: '#f9f9f9',
  },
  pickerContainer: {
    borderWidth: 1,
    borderColor: '#ddd',
    borderRadius: 6,
    backgroundColor: '#f9f9f9',
    overflow: 'hidden',
  },
  picker: {
    height: 50,
    width: '100%',
  },
  modalButtons: {
    flexDirection: 'row',
    justifyContent: 'space-between',
  },
  modalButton: {
    flex: 1,
    padding: 12,
    borderRadius: 6,
    alignItems: 'center',
    marginHorizontal: 4,
  },
  saveButton: {
    backgroundColor: '#4CAF50',
  },
  cancelButton: {
    backgroundColor: '#f1f1f1',
  },
  saveButtonText: {
    color: 'white',
    fontWeight: 'bold',
  },
  cancelButtonText: {
    color: '#666',
    fontWeight: 'bold',
  },
  text: {
    fontSize: 16,
    color: '#666',
  },
});

export default FloorManagement;
