import React, { useState, useEffect } from 'react';
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
import { warehouseService } from '../../../services/warehouseService';

const WarehouseManagement = () => {
  const [warehouses, setWarehouses] = useState([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [modalVisible, setModalVisible] = useState(false);
  const [isEditing, setIsEditing] = useState(false);
  const [editingId, setEditingId] = useState(null);
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
    } catch (error) {
      console.error('Error fetching warehouses:', error);
      Alert.alert('Error', 'Failed to fetch warehouse list');
    } finally {
      setLoading(false);
      setRefreshing(false);
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
    setNewWarehouse({
      code_entrepot: '',
      nom_entrepot: '',
      ville: '',
      adresse: ''
    });
    setIsEditing(false);
    setEditingId(null);
  };

  const renderWarehouseItem = ({ item }) => (
    <View style={styles.warehouseCard}>
      <View style={styles.warehouseInfo}>
        <Text style={styles.warehouseName}>{item.nom_entrepot}</Text>
        <Text style={styles.warehouseCode}>{item.code_entrepot}</Text>
        <Text style={styles.warehouseDetails}>
          {item.ville}{item.adresse ? ` - ${item.adresse}` : ''}
        </Text>
        <View style={[styles.statusBadge, { backgroundColor: item.actif ? '#4CAF50' : '#F44336', alignSelf: 'flex-start', marginTop: 8 }]}>
          <Text style={styles.statusText}>{item.actif ? 'Active' : 'Inactive'}</Text>
        </View>
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
          onPress={() => handleDeleteWarehouse(item.id_entrepot)}
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

  return (
    <View style={styles.container}>
      <View style={styles.header}>
        <Text style={styles.title}>Warehouses</Text>
        <View style={styles.headerButtons}>
          <TouchableOpacity 
            style={[styles.headerButton, styles.addButton]} 
            onPress={openAddModal}
          >
            <Text style={styles.buttonText}>+ Add</Text>
          </TouchableOpacity>
        </View>
      </View>
      
      {warehouses.length === 0 ? (
        <View style={styles.centered}>
          <Text style={styles.text}>No warehouses found</Text>
        </View>
      ) : (
        <FlatList
          data={warehouses}
          keyExtractor={(item) => item.id_entrepot}
          renderItem={renderWarehouseItem}
          contentContainerStyle={styles.listContent}
          onRefresh={onRefresh}
          refreshing={refreshing}
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
            <Text style={styles.modalTitle}>{isEditing ? 'Edit Warehouse' : 'Add New Warehouse'}</Text>
            <ScrollView style={styles.modalForm}>
              <Text style={styles.label}>Warehouse Code *</Text>
              <TextInput
                style={styles.input}
                placeholder="e.g., MAIN_ST_WH"
                value={newWarehouse.code_entrepot}
                onChangeText={(text) => setNewWarehouse({...newWarehouse, code_entrepot: text})}
              />

              <Text style={styles.label}>Warehouse Name *</Text>
              <TextInput
                style={styles.input}
                placeholder="e.g., Central Warehouse"
                value={newWarehouse.nom_entrepot}
                onChangeText={(text) => setNewWarehouse({...newWarehouse, nom_entrepot: text})}
              />

              <Text style={styles.label}>City</Text>
              <TextInput
                style={styles.input}
                placeholder="e.g., Paris"
                value={newWarehouse.ville}
                onChangeText={(text) => setNewWarehouse({...newWarehouse, ville: text})}
              />

              <Text style={styles.label}>Address</Text>
              <TextInput
                style={styles.input}
                placeholder="e.g., 123 Rue de Rivoli"
                value={newWarehouse.adresse}
                onChangeText={(text) => setNewWarehouse({...newWarehouse, adresse: text})}
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
                onPress={handleSubmitWarehouse}
                disabled={submitting}
              >
                {submitting ? (
                  <ActivityIndicator size="small" color="white" />
                ) : (
                  <Text style={styles.saveButtonText}>{isEditing ? 'Update Warehouse' : 'Add Warehouse'}</Text>
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
    backgroundColor: '#f5f5f5',
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
  warehouseCard: {
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
  warehouseInfo: {
    flex: 1,
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
  editButton: {
    // Custom edit styles if needed
  },
  deleteButton: {
    // Custom delete styles if needed
  },
  warehouseName: {
    fontSize: 18,
    fontWeight: 'bold',
    color: '#333',
    marginBottom: 2,
  },
  warehouseCode: {
    fontSize: 14,
    color: '#2196F3',
    fontWeight: '600',
    marginBottom: 4,
  },
  warehouseDetails: {
    fontSize: 14,
    color: '#666',
  },
  statusBadge: {
    paddingHorizontal: 8,
    paddingVertical: 4,
    borderRadius: 12,
  },
  statusText: {
    color: 'white',
    fontSize: 12,
    fontWeight: 'bold',
  },
  text: {
    fontSize: 16,
    color: '#666',
  },
  // Modal Styles
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
    shadowColor: '#000',
    shadowOffset: { width: 0, height: -2 },
    shadowOpacity: 0.25,
    shadowRadius: 3.84,
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
});

export default WarehouseManagement;
