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
import { Picker } from '@react-native-picker/picker';
import { warehouseService } from '../../../services/warehouseService';
import { chariotService } from '../../../services/chariotService';

const ChariotManagement = () => {
  const [chariots, setChariots] = useState([]);
  const [warehouses, setWarehouses] = useState([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [modalVisible, setModalVisible] = useState(false);
  const [isEditing, setIsEditing] = useState(false);
  const [editingId, setEditingId] = useState(null);
  const [submitting, setSubmitting] = useState(false);

  const [newChariot, setNewChariot] = useState({
    code_chariot: '',
    id_entrepot_id: '',
    statut: 'AVAILABLE',
    capacite: ''
  });

  const fetchData = async () => {
    try {
      setLoading(true);
      const [chariotsData, warehousesData] = await Promise.all([
        chariotService.getChariots(),
        warehouseService.getWarehouses()
      ]);
      setChariots(chariotsData);
      setWarehouses(warehousesData);
    } catch (error) {
      console.error('Error fetching data:', error);
      Alert.alert('Error', 'Failed to load chariots or warehouses');
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
    fetchData();
  };

  const handleSubmitChariot = async () => {
    if (!newChariot.code_chariot || !newChariot.id_entrepot_id) {
      Alert.alert('Error', 'Please fill in required fields (Code and Warehouse)');
      return;
    }

    try {
      setSubmitting(true);
      if (isEditing) {
        await chariotService.updateChariot(editingId, newChariot);
        Alert.alert('Success', 'Chariot updated successfully');
      } else {
        await chariotService.createChariot(newChariot);
        Alert.alert('Success', 'Chariot added successfully');
      }
      closeModal();
      fetchData();
    } catch (error) {
      console.error('Error submitting chariot:', error);
      Alert.alert('Error', `Failed to ${isEditing ? 'update' : 'add'} chariot`);
    } finally {
      setSubmitting(false);
    }
  };

  const handleMaintenance = async (id) => {
    try {
      await chariotService.setMaintenance(id);
      Alert.alert('Success', 'Chariot set to maintenance');
      fetchData();
    } catch (error) {
      Alert.alert('Error', 'Failed to update status');
    }
  };

  const handleRelease = async (id) => {
    try {
      await chariotService.releaseChariot(id);
      Alert.alert('Success', 'Chariot released');
      fetchData();
    } catch (error) {
      Alert.alert('Error', 'Failed to release chariot');
    }
  };

  const handleDeleteChariot = (id) => {
    Alert.alert(
      'Delete Chariot',
      'Are you sure you want to delete this chariot?',
      [
        { text: 'Cancel', style: 'cancel' },
        { 
          text: 'Delete', 
          style: 'destructive',
          onPress: async () => {
            try {
              await chariotService.deleteChariot(id);
              Alert.alert('Success', 'Chariot deleted successfully');
              fetchData();
            } catch (error) {
              console.error('Error deleting chariot:', error);
              Alert.alert('Error', 'Failed to delete chariot');
            }
          }
        }
      ]
    );
  };

  const openEditModal = (chariot) => {
    setNewChariot({
      code_chariot: chariot.code_chariot,
      id_entrepot_id: chariot.id_entrepot?.id_entrepot || chariot.id_entrepot,
      statut: chariot.statut,
      capacite: chariot.capacite ? chariot.capacite.toString() : ''
    });
    setEditingId(chariot.id_chariot);
    setIsEditing(true);
    setModalVisible(true);
  };

  const openAddModal = () => {
    setNewChariot({
      code_chariot: '',
      id_entrepot_id: warehouses.length > 0 ? warehouses[0].id_entrepot : '',
      statut: 'AVAILABLE',
      capacite: ''
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
      case 'IN_USE': return '#2196F3';
      case 'MAINTENANCE': return '#FF9800';
      case 'INACTIVE': return '#F44336';
      default: return '#757575';
    }
  };

  const renderChariotItem = ({ item }) => (
    <View style={styles.card}>
      <View style={styles.infoContainer}>
        <View style={styles.row}>
          <Text style={styles.codeText}>{item.code_chariot}</Text>
          <View style={[styles.statusBadge, { backgroundColor: getStatusColor(item.statut) }]}>
            <Text style={styles.statusText}>{item.statut}</Text>
          </View>
        </View>
        <Text style={styles.subText}>
          <Feather name="home" size={12} /> {item.id_entrepot?.nom_entrepot || 'N/A'}
        </Text>
        {item.capacite ? (
          <Text style={styles.capaciteText}>Capacity: {item.capacite} kg</Text>
        ) : null}
      </View>
      
      <View style={styles.actionButtons}>
        {item.statut === 'IN_USE' && (
          <TouchableOpacity 
            style={styles.actionButton} 
            onPress={() => handleRelease(item.id_chariot)}
          >
            <Feather name="unlock" size={18} color="#4CAF50" />
          </TouchableOpacity>
        )}
        {item.statut === 'AVAILABLE' && (
          <TouchableOpacity 
            style={styles.actionButton} 
            onPress={() => handleMaintenance(item.id_chariot)}
          >
            <Feather name="tool" size={18} color="#FF9800" />
          </TouchableOpacity>
        )}
        <TouchableOpacity 
          style={styles.actionButton} 
          onPress={() => openEditModal(item)}
        >
          <Feather name="edit-2" size={18} color="#2196F3" />
        </TouchableOpacity>
        <TouchableOpacity 
          style={styles.actionButton} 
          onPress={() => handleDeleteChariot(item.id_chariot)}
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
        <Text style={styles.title}>Chariots</Text>
        <TouchableOpacity 
          style={styles.addButton} 
          onPress={openAddModal}
        >
          <Text style={styles.addButtonText}>+ Add Chariot</Text>
        </TouchableOpacity>
      </View>
      
      {chariots.length === 0 ? (
        <View style={styles.centered}>
          <Text>No chariots found</Text>
        </View>
      ) : (
        <FlatList
          data={chariots}
          keyExtractor={(item) => item.id_chariot}
          renderItem={renderChariotItem}
          onRefresh={onRefresh}
          refreshing={refreshing}
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
              {isEditing ? 'Edit Chariot' : 'Add New Chariot'}
            </Text>
            
            <ScrollView style={styles.form}>
              <Text style={styles.label}>Warehouse *</Text>
              <View style={styles.pickerContainer}>
                <Picker
                  selectedValue={newChariot.id_entrepot_id}
                  onValueChange={(val) => setNewChariot({...newChariot, id_entrepot_id: val})}
                  style={styles.picker}
                >
                  {warehouses.map(w => (
                    <Picker.Item key={w.id_entrepot} label={w.nom_entrepot} value={w.id_entrepot} />
                  ))}
                </Picker>
              </View>

              <Text style={styles.label}>Chariot Code * (e.g., C-01, CHAR-01)</Text>
              <TextInput
                style={styles.input}
                value={newChariot.code_chariot}
                onChangeText={(t) => setNewChariot({...newChariot, code_chariot: t})}
                placeholder="Enter unique code"
              />

              <Text style={styles.label}>Capacity (optional)</Text>
              <TextInput
                style={styles.input}
                value={newChariot.capacite}
                onChangeText={(t) => setNewChariot({...newChariot, capacite: t})}
                placeholder="Capacity in kg"
                keyboardType="numeric"
              />

              <Text style={styles.label}>Status</Text>
              <View style={styles.pickerContainer}>
                <Picker
                  selectedValue={newChariot.statut}
                  onValueChange={(val) => setNewChariot({...newChariot, statut: val})}
                  style={styles.picker}
                >
                  <Picker.Item label="Available" value="AVAILABLE" />
                  <Picker.Item label="In Use" value="IN_USE" />
                  <Picker.Item label="Maintenance" value="MAINTENANCE" />
                  <Picker.Item label="Inactive" value="INACTIVE" />
                </Picker>
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
                onPress={handleSubmitChariot}
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
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#f8f9fa',
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
  },
  addButtonText: {
    color: 'white',
    fontWeight: 'bold',
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
  capaciteText: {
    fontSize: 14,
    color: '#7f8c8d',
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
    maxHeight: '80%',
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
});

export default ChariotManagement;
