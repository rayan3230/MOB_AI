import React, { useState, useEffect } from 'react';
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
import AsyncStorage from '@react-native-async-storage/async-storage';
import { warehouseService } from '../../../services/warehouseService';
import CollapsibleManagementCard from '../../../components/CollapsibleManagementCard';
import ManagementModal from '../../../components/ManagementModal';

const WarehouseManagement = () => {
  const [warehouses, setWarehouses] = useState([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [modalVisible, setModalVisible] = useState(false);
  const [isEditing, setIsEditing] = useState(false);
  const [editingId, setEditingId] = useState(null);
  const [activeWarehouse, setActiveWarehouse] = useState(null);
  const [newWarehouse, setNewWarehouse] = useState({
    code_entrepot: '',
    nom_entrepot: '',
    ville: '',
    adresse: ''
  });
  const [submitting, setSubmitting] = useState(false);

  const fetchWarehouses = async () => {
    try {
      setLoading(true);
      const data = await warehouseService.getWarehouses();
      setWarehouses(data);
      const activeId = await AsyncStorage.getItem('activeWarehouseId');
      if (activeId) {
        setActiveWarehouse(Number(activeId));
      }
    } catch (error) {
      console.error('Error fetching warehouses:', error);
      Alert.alert('Error', 'Failed to fetch warehouse list');
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  };

  const handleSelectWarehouse = async (id) => {
    try {
      await AsyncStorage.setItem('activeWarehouseId', String(id));
      setActiveWarehouse(id);
      Alert.alert('Success', `Warehouse ${id} is now set as active`);
    } catch (error) {
      Alert.alert('Error', 'Failed to set active warehouse');
    }
  };

  useEffect(() => {
    fetchWarehouses();
  }, []);

  const onRefresh = () => {
    setRefreshing(true);
    fetchWarehouses();
  };

  const handleSubmitWarehouse = async () => {
    if (!newWarehouse.code_entrepot || !newWarehouse.nom_entrepot) {
      Alert.alert('Error', 'Please fill in required fields (Code and Name)');
      return;
    }

    try {
      setSubmitting(true);
      if (isEditing) {
        await warehouseService.updateWarehouse(editingId, newWarehouse);
        Alert.alert('Success', 'Warehouse updated successfully');
      } else {
        await warehouseService.createWarehouse(newWarehouse);
        Alert.alert('Success', 'Warehouse added successfully');
      }
      closeModal();
      fetchWarehouses();
    } catch (error) {
      console.error('Error submitting warehouse:', error);
      Alert.alert('Error', `Failed to ${isEditing ? 'update' : 'add'} warehouse`);
    } finally {
      setSubmitting(false);
    }
  };

  const handleDeleteWarehouse = (id) => {
    Alert.alert(
      'Delete Warehouse',
      'Are you sure you want to delete this warehouse?',
      [
        { text: 'Cancel', style: 'cancel' },
        { 
          text: 'Delete', 
          style: 'destructive',
          onPress: async () => {
            try {
              await warehouseService.deleteWarehouse(id);
              Alert.alert('Success', 'Warehouse deleted successfully');
              fetchWarehouses();
            } catch (error) {
              console.error('Error deleting warehouse:', error);
              Alert.alert('Error', 'Failed to delete warehouse');
            }
          }
        }
      ]
    );
  };

  const openEditModal = (warehouse) => {
    setNewWarehouse({
      code_entrepot: warehouse.code_entrepot,
      nom_entrepot: warehouse.nom_entrepot,
      ville: warehouse.ville || '',
      adresse: warehouse.adresse || ''
    });
    setEditingId(warehouse.id_entrepot);
    setIsEditing(true);
    setModalVisible(true);
  };

  const openAddModal = () => {
    setNewWarehouse({
      code_entrepot: '',
      nom_entrepot: '',
      ville: '',
      adresse: ''
    });
    setIsEditing(false);
    setEditingId(null);
    setModalVisible(true);
  };

  const closeModal = () => {
    setModalVisible(false);
  };

  const renderWarehouseItem = ({ item }) => {
    const isActive = activeWarehouse === item.id_entrepot;
    
    return (
      <CollapsibleManagementCard
        title={item.nom_entrepot}
        subtitle={item.code_entrepot}
        status={item.actif ? 'Active' : 'Inactive'}
        icon="home"
        iconColor={isActive ? "#007AFF" : "#666"}
        details={[
          { label: 'City', value: item.ville },
          { label: 'Address', value: item.adresse },
          { label: 'ID', value: String(item.id_entrepot) },
          { label: 'Status', value: item.actif ? 'Active' : 'Inactive' }
        ]}
        onEdit={() => openEditModal(item)}
        onDelete={() => handleDeleteWarehouse(item.id_entrepot)}
        extraActions={[
          {
            label: isActive ? 'Selected' : 'Select',
            icon: isActive ? 'check-circle' : 'circle',
            color: isActive ? '#4CAF50' : '#007AFF',
            onPress: () => handleSelectWarehouse(item.id_entrepot)
          }
        ]}
      />
    );
  };

  return (
    <View style={styles.container}>
      <StatusBar barStyle="dark-content" />
      <View style={styles.header}>
        <View>
          <Text style={styles.title}>Warehouses</Text>
          <Text style={styles.subtitle}>Manage your storage facilities</Text>
        </View>
        <TouchableOpacity style={styles.addButton} onPress={openAddModal}>
          <Feather name="plus" size={24} color="#FFF" />
        </TouchableOpacity>
      </View>
      
      {loading && !refreshing ? (
        <View style={styles.centered}>
          <ActivityIndicator size="large" color="#007AFF" />
          <Text style={styles.loadingText}>Loading warehouses...</Text>
        </View>
      ) : warehouses.length === 0 ? (
        <View style={styles.centered}>
          <Feather name="box" size={50} color="#DDD" />
          <Text style={styles.noDataText}>No warehouses found</Text>
          <TouchableOpacity style={styles.refreshButton} onPress={onRefresh}>
            <Text style={styles.refreshButtonText}>Refresh</Text>
          </TouchableOpacity>
        </View>
      ) : (
        <FlatList
          data={warehouses}
          keyExtractor={(item) => String(item.id_entrepot)}
          renderItem={renderWarehouseItem}
          contentContainerStyle={styles.listContent}
          onRefresh={onRefresh}
          refreshing={refreshing}
        />
      )}

      <ManagementModal
        visible={modalVisible}
        onClose={closeModal}
        title={isEditing ? 'Update Warehouse' : 'New Warehouse'}
        onSubmit={handleSubmitWarehouse}
        submitting={submitting}
        submitLabel={isEditing ? 'Update' : 'Create'}
      >
        <View style={styles.formGroup}>
          <Text style={styles.label}>Warehouse Code *</Text>
          <View style={styles.inputContainer}>
            <Feather name="hash" size={18} color="#94A3B8" style={styles.inputIcon} />
            <TextInput
              style={styles.input}
              placeholder="e.g., MAIN_WH_01"
              value={newWarehouse.code_entrepot}
              onChangeText={(text) => setNewWarehouse({...newWarehouse, code_entrepot: text})}
              placeholderTextColor="#94A3B8"
            />
          </View>
        </View>

        <View style={styles.formGroup}>
          <Text style={styles.label}>Warehouse Name *</Text>
          <View style={styles.inputContainer}>
            <Feather name="tag" size={18} color="#94A3B8" style={styles.inputIcon} />
            <TextInput
              style={styles.input}
              placeholder="e.g., Central Logistics"
              value={newWarehouse.nom_entrepot}
              onChangeText={(text) => setNewWarehouse({...newWarehouse, nom_entrepot: text})}
              placeholderTextColor="#94A3B8"
            />
          </View>
        </View>

        <View style={styles.formGroup}>
          <Text style={styles.label}>City</Text>
          <View style={styles.inputContainer}>
            <Feather name="map-pin" size={18} color="#94A3B8" style={styles.inputIcon} />
            <TextInput
              style={styles.input}
              placeholder="City name"
              value={newWarehouse.ville}
              onChangeText={(text) => setNewWarehouse({...newWarehouse, ville: text})}
              placeholderTextColor="#94A3B8"
            />
          </View>
        </View>

        <View style={styles.formGroup}>
          <Text style={styles.label}>Address</Text>
          <View style={[styles.inputContainer, { height: 100, alignItems: 'flex-start', paddingTop: 12 }]}>
            <Feather name="map" size={18} color="#94A3B8" style={[styles.inputIcon, { marginTop: 4 }]} />
            <TextInput
              style={[styles.input, { height: 80, textAlignVertical: 'top' }]}
              placeholder="Full address"
              multiline
              numberOfLines={3}
              value={newWarehouse.adresse}
              onChangeText={(text) => setNewWarehouse({...newWarehouse, adresse: text})}
              placeholderTextColor="#94A3B8"
            />
          </View>
        </View>
      </ManagementModal>
    </View>
  );
};

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: '#F8F9FA' },
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
  title: { fontSize: 28, fontWeight: '800', color: '#0F172A' },
  subtitle: { fontSize: 14, color: '#64748B', marginTop: 2 },
  addButton: {
    width: 48, height: 48, borderRadius: 14, backgroundColor: '#2196F3',
    justifyContent: 'center', alignItems: 'center', marginLeft: 12,
    elevation: 4, shadowColor: '#2196F3', shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.3, shadowRadius: 8
  },
  listContent: { paddingVertical: 12, paddingBottom: 100 },
  centered: { flex: 1, justifyContent: 'center', alignItems: 'center' },
  loadingText: { marginTop: 12, color: '#64748B', fontSize: 16 },
  noDataText: { marginTop: 12, color: '#94A3B8', fontSize: 18, fontWeight: '600' },
  refreshButton: {
    marginTop: 20, paddingHorizontal: 24, paddingVertical: 12,
    borderRadius: 12, backgroundColor: '#F1F5F9'
  },
  refreshButtonText: { color: '#2196F3', fontWeight: '700' },
  label: { fontSize: 14, fontWeight: '700', marginBottom: 8, color: '#475569' },
  formGroup: { marginBottom: 20 },
  inputContainer: {
    backgroundColor: '#F8FAFC', borderRadius: 12, paddingHorizontal: 12,
    borderWidth: 1, borderColor: '#E2E8F0', flexDirection: 'row', alignItems: 'center',
    height: 54
  },
  inputIcon: { marginRight: 10 },
  input: { flex: 1, height: 54, fontSize: 16, color: '#1E293B' },
});

export default WarehouseManagement;
