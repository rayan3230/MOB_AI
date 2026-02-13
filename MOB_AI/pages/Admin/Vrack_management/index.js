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
import { productService } from '../../../services/productService';
import { Picker } from '@react-native-picker/picker';

const VrackManagement = () => {
  const [vracks, setVracks] = useState([]);
  const [warehouses, setWarehouses] = useState([]);
  const [products, setProducts] = useState([]);
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

  const fetchData = async () => {
    try {
      setLoading(true);
      const [vrackData, warehouseData, productData, locationData] = await Promise.all([
        warehouseService.getVracks(),
        warehouseService.getWarehouses(),
        productService.getProducts(),
        warehouseService.getLocations()
      ]);
      setVracks(vrackData);
      setWarehouses(warehouseData);
      setProducts(productData);
      setLocations(locationData.filter(l => l.statut === 'AVAILABLE'));
      
      if (warehouseData.length > 0 && !newVrack.id_entrepot_id) {
        setNewVrack(prev => ({ ...prev, id_entrepot_id: warehouseData[0].id_entrepot }));
      }
      if (productData.length > 0 && !newVrack.id_produit_id) {
        setNewVrack(prev => ({ ...prev, id_produit_id: productData[0].id_produit }));
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
    fetchData();
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
    setNewVrack({
      id_entrepot_id: warehouses.length > 0 ? warehouses[0].id_entrepot : '',
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

  const openTransferModal = (vrack) => {
    setSelectedVrack(vrack);
    setTransferData({
      destination_location_id: locations.length > 0 ? locations[0].id_emplacement : '',
      quantity: '',
      notes: ''
    });
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
    <View style={styles.card}>
      <View style={styles.infoContainer}>
        <View style={styles.row}>
          <Text style={styles.warehouseText}>{item.id_entrepot.nom_entrepot}</Text>
        </View>
        <Text style={styles.productName}>{item.id_produit.nom_produit}</Text>
        <Text style={styles.skuText}>SKU: {item.id_produit.sku}</Text>
        <View style={styles.quantityBadge}>
          <Text style={styles.quantityText}>Quantité: {item.quantite}</Text>
        </View>
      </View>
      
      <View style={styles.actionButtons}>
        <TouchableOpacity 
          style={[styles.actionButton, { backgroundColor: '#E3F2FD' }]} 
          onPress={() => openTransferModal(item)}
        >
          <Feather name="log-out" size={18} color="#2196F3" />
        </TouchableOpacity>
        <TouchableOpacity 
          style={styles.actionButton} 
          onPress={() => openEditModal(item)}
        >
          <Feather name="edit-2" size={18} color="#2196F3" />
        </TouchableOpacity>
        <TouchableOpacity 
          style={styles.actionButton} 
          onPress={() => handleDeleteVrack(item.id_vrack)}
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
        <Text style={styles.title}>Gestion Vrack</Text>
        <TouchableOpacity 
          style={styles.addButton} 
          onPress={openAddModal}
        >
          <Text style={styles.addButtonText}>+ Ajouter Vrack</Text>
        </TouchableOpacity>
      </View>
      
      {vracks.length === 0 ? (
        <View style={styles.centered}>
          <Text>Aucun enregistrement Vrack trouvé</Text>
        </View>
      ) : (
        <FlatList
          data={vracks}
          keyExtractor={(item) => item.id_vrack}
          renderItem={renderVrackItem}
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
              {isEditing ? 'Modifier Vrack' : 'Ajouter Nouveau Vrack'}
            </Text>
            
            <ScrollView style={styles.form}>
              <Text style={styles.label}>Entrepôt *</Text>
              <View style={styles.pickerContainer}>
                <Picker
                  selectedValue={newVrack.id_entrepot_id}
                  onValueChange={(val) => setNewVrack({...newVrack, id_entrepot_id: val})}
                  enabled={!isEditing}
                >
                  {warehouses.map(w => (
                    <Picker.Item key={w.id_entrepot} label={w.nom_entrepot} value={w.id_entrepot} />
                  ))}
                </Picker>
              </View>

              <Text style={styles.label}>Produit *</Text>
              <View style={styles.pickerContainer}>
                <Picker
                  selectedValue={newVrack.id_produit_id}
                  onValueChange={(val) => setNewVrack({...newVrack, id_produit_id: val})}
                  enabled={!isEditing}
                >
                  {products.map(p => (
                    <Picker.Item key={p.id_produit} label={`${p.nom_produit} (${p.sku})`} value={p.id_produit} />
                  ))}
                </Picker>
              </View>

              <Text style={styles.label}>Quantité</Text>
              <TextInput
                style={styles.input}
                value={newVrack.quantite}
                onChangeText={(t) => setNewVrack({...newVrack, quantite: t})}
                placeholder="0.00"
                keyboardType="numeric"
              />
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
                onPress={handleSubmitVrack}
                disabled={submitting}
              >
                {submitting ? (
                  <ActivityIndicator color="white" size="small" />
                ) : (
                  <Text style={styles.saveButtonText}>{isEditing ? 'Mettre à jour' : 'Enregistrer'}</Text>
                )}
              </TouchableOpacity>
            </View>
          </View>
        </View>
      </Modal>

      {/* Transfer Modal */}
      <Modal
        animationType="fade"
        transparent={true}
        visible={transferModalVisible}
        onRequestClose={closeModal}
      >
        <View style={styles.modalOverlay}>
          <View style={styles.modalContent}>
            <Text style={styles.modalTitle}>Sortie de Vrack</Text>
            <Text style={styles.subtitle}>
              {selectedVrack?.id_produit?.nom_produit} ({selectedVrack?.quantite} dispos)
            </Text>
            
            <ScrollView style={styles.form}>
              <Text style={styles.label}>Emplacement Destination *</Text>
              <View style={styles.pickerContainer}>
                <Picker
                  selectedValue={transferData.destination_location_id}
                  onValueChange={(val) => setTransferData({...transferData, destination_location_id: val})}
                >
                  {locations.map(l => (
                    <Picker.Item 
                      key={l.id_emplacement} 
                      label={`${l.code_emplacement} (${l.id_niveau})`} 
                      value={l.id_emplacement} 
                    />
                  ))}
                </Picker>
              </View>

              <Text style={styles.label}>Quantité à déplacer *</Text>
              <TextInput
                style={styles.input}
                value={transferData.quantity}
                onChangeText={(t) => setTransferData({...transferData, quantity: t})}
                placeholder="0.00"
                keyboardType="numeric"
              />

              <Text style={styles.label}>Notes</Text>
              <TextInput
                style={[styles.input, { height: 60 }]}
                value={transferData.notes}
                onChangeText={(t) => setTransferData({...transferData, notes: t})}
                placeholder="Raison du transfert..."
                multiline
              />
            </ScrollView>

            <View style={styles.modalButtons}>
              <TouchableOpacity 
                style={[styles.modalButton, styles.cancelButton]} 
                onPress={closeModal}
              >
                <Text style={styles.cancelButtonText}>Annuler</Text>
              </TouchableOpacity>
              <TouchableOpacity 
                style={[styles.modalButton, styles.saveButton]} 
                onPress={handleTransfer}
                disabled={submitting}
              >
                {submitting ? (
                  <ActivityIndicator color="white" size="small" />
                ) : (
                  <Text style={styles.saveButtonText}>Confirmer Transfert</Text>
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
  warehouseText: {
    fontSize: 14,
    fontWeight: 'bold',
    color: '#3498db',
    marginBottom: 4,
  },
  productName: {
    fontSize: 18,
    fontWeight: '600',
    color: '#2c3e50',
    marginBottom: 2,
  },
  skuText: {
    fontSize: 12,
    color: '#7f8c8d',
    marginBottom: 8,
  },
  quantityBadge: {
    backgroundColor: '#e8f5e9',
    paddingHorizontal: 8,
    paddingVertical: 4,
    borderRadius: 6,
    alignSelf: 'flex-start',
  },
  quantityText: {
    color: '#2e7d32',
    fontWeight: 'bold',
    fontSize: 14,
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
    marginBottom: 8,
    textAlign: 'center',
  },
  subtitle: {
    fontSize: 14,
    color: '#666',
    textAlign: 'center',
    marginBottom: 16,
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
    marginBottom: 8,
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

export default VrackManagement;
