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
  ScrollView,
  Switch
} from 'react-native';
import { Feather } from '@expo/vector-icons';
import { Picker } from '@react-native-picker/picker';
import { warehouseService } from '../../../services/warehouseService';

const LocationManagement = () => {
  const [locations, setLocations] = useState([]);
  const [warehouses, setWarehouses] = useState([]);
  const [floors, setFloors] = useState([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
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

  const fetchData = async () => {
    try {
      setLoading(true);
      const [locsData, whData, stockFloors, pickingFloors] = await Promise.all([
        warehouseService.getLocations(),
        warehouseService.getWarehouses(),
        warehouseService.getFloors(),
        warehouseService.getPickingFloors()
      ]);
      
      const allFloors = [
        ...stockFloors,
        ...pickingFloors.map(f => ({ ...f, id_niveau: f.id_niveau_picking }))
      ];
      
      setLocations(locsData);
      setWarehouses(whData);
      setFloors(allFloors);
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
    fetchData();
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
          submissionData.id_niveau_picking_id = selectedFloor.id_niveau;
          submissionData.id_niveau_id = null;
        } else {
          submissionData.id_niveau_id = selectedFloor.id_niveau;
          submissionData.id_niveau_picking_id = null;
        }
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
      id_niveau_id: loc.id_niveau?.id_niveau || loc.id_niveau || loc.id_niveau_picking?.id_niveau_picking || loc.id_niveau_picking || '',
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
      id_entrepot_id: warehouses.length > 0 ? warehouses[0].id_entrepot : '',
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
          {item.id_niveau ? ` • ${item.id_niveau.code_niveau}` : ''}
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

  const filteredFloors = floors.filter(f => 
    f.id_entrepot?.id_entrepot === newLocation.id_entrepot_id || 
    f.id_entrepot === newLocation.id_entrepot_id
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
        <Text style={styles.title}>Locations</Text>
        <TouchableOpacity 
          style={styles.addButton} 
          onPress={openAddModal}
        >
          <Text style={styles.addButtonText}>+ Add Location</Text>
        </TouchableOpacity>
      </View>
      
      {locations.length === 0 ? (
        <View style={styles.centered}>
          <Text>No locations found</Text>
        </View>
      ) : (
        <FlatList
          data={locations}
          keyExtractor={(item) => item.id_emplacement}
          renderItem={renderLocationItem}
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
              {isEditing ? 'Edit Location' : 'Add New Location'}
            </Text>
            
            <ScrollView style={styles.form}>
              <Text style={styles.label}>Warehouse *</Text>
              <View style={styles.pickerContainer}>
                <Picker
                  selectedValue={newLocation.id_entrepot_id}
                  onValueChange={(val) => setNewLocation({...newLocation, id_entrepot_id: val, id_niveau_id: ''})}
                  style={styles.picker}
                >
                  {warehouses.map(w => (
                    <Picker.Item key={w.id_entrepot} label={w.nom_entrepot} value={w.id_entrepot} />
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
    elevation: 2,
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
});

export default LocationManagement;
