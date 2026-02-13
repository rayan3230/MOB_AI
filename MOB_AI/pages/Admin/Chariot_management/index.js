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
import OptionSelector from '../../../components/OptionSelector';
import { warehouseService } from '../../../services/warehouseService';
import { chariotService } from '../../../services/chariotService';
import CollapsibleManagementCard from '../../../components/CollapsibleManagementCard';
import ManagementModal from '../../../components/ManagementModal';

const ChariotManagement = () => {
  const [chariots, setChariots] = useState([]);
  const [warehouses, setWarehouses] = useState([]);
  const [selectedWarehouseId, setSelectedWarehouseId] = useState('');
  const [warehouseFilterModalVisible, setWarehouseFilterModalVisible] = useState(false);
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

  const fetchData = async (warehouseIdOverride = null) => {
    try {
      setLoading(true);
      const warehousesData = await warehouseService.getWarehouses();
      const safeWarehouses = Array.isArray(warehousesData) ? warehousesData : [];
      setWarehouses(safeWarehouses);

      const effectiveWhId = (warehouseIdOverride || selectedWarehouseId || '').toString().trim();
      const chariotsData = await chariotService.getChariots(effectiveWhId || null);
      
      setChariots(chariotsData);
      setSelectedWarehouseId(effectiveWhId);
    } catch (error) {
      console.error('Error fetching data:', error);
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  };

  useEffect(() => { fetchData(); }, []);

  const onRefresh = () => {
    setRefreshing(true);
    fetchData(selectedWarehouseId);
  };

  const handleSubmitChariot = async () => {
    if (!newChariot.code_chariot || !newChariot.id_entrepot_id) {
      Alert.alert('Erreur', 'Veuillez remplir les champs obligatoires');
      return;
    }

    try {
      setSubmitting(true);
      if (isEditing) {
        await chariotService.updateChariot(editingId, newChariot);
      } else {
        await chariotService.createChariot(newChariot);
      }
      setModalVisible(false);
      fetchData(selectedWarehouseId);
      Alert.alert('Succès', `Chariot ${isEditing ? 'mis à jour' : 'ajouté'} avec succès`);
    } catch (error) {
      Alert.alert('Erreur', 'Échec de l\'opération');
    } finally {
      setSubmitting(false);
    }
  };

  const handleMaintenance = async (id) => {
    try {
      await chariotService.setMaintenance(id);
      fetchData(selectedWarehouseId);
    } catch (error) {
      Alert.alert('Erreur', 'Impossible de mettre en maintenance');
    }
  };

  const handleRelease = async (id) => {
    try {
      await chariotService.releaseChariot(id);
      fetchData(selectedWarehouseId);
    } catch (error) {
      Alert.alert('Erreur', 'Impossible de libérer le chariot');
    }
  };

  const handleDeleteChariot = (id) => {
    Alert.alert('Supprimer Chariot', 'Êtes-vous sûr ?', [
      { text: 'Annuler', style: 'cancel' },
      { 
        text: 'Supprimer', style: 'destructive',
        onPress: async () => {
          try {
            await chariotService.deleteChariot(id);
            fetchData(selectedWarehouseId);
          } catch (error) {
            Alert.alert('Erreur', 'Échec de la suppression');
          }
        }
      }
    ]);
  };

  const openEditModal = (chariot) => {
    setNewChariot({
      code_chariot: chariot.code_chariot,
      id_entrepot_id: String(chariot.id_entrepot?.id_entrepot || chariot.id_entrepot),
      statut: chariot.statut,
      capacite: chariot.capacite ? chariot.capacite.toString() : ''
    });
    setEditingId(chariot.id_chariot);
    setIsEditing(true);
    setModalVisible(true);
  };

  const getStatusColor = (status) => {
    switch (status) {
      case 'AVAILABLE': return '#4CAF50';
      case 'IN_USE': return '#2196F3';
      case 'MAINTENANCE': return '#FF9800';
      default: return '#8E8E93';
    }
  };

  const renderChariotItem = ({ item }) => (
    <CollapsibleManagementCard
      title={item.code_chariot}
      subtitle={item.id_entrepot?.nom_entrepot || 'Entrepôt Inconnu'}
      status={item.statut}
      iconName="truck"
      iconColor={getStatusColor(item.statut)}
      details={[
        { label: 'Statut', value: item.statut },
        { label: 'Capacité', value: item.capacite ? `${item.capacite} kg` : 'N/A' },
        { label: 'Entrepôt', value: item.id_entrepot?.nom_entrepot },
      ]}
      onEdit={() => openEditModal(item)}
      onDelete={() => handleDeleteChariot(item.id_chariot)}
    >
      <View style={styles.cardActions}>
        {item.statut === 'IN_USE' && (
          <TouchableOpacity style={[styles.contextButton, { backgroundColor: '#E3F2FD' }]} onPress={() => handleRelease(item.id_chariot)}>
            <Feather name="unlock" size={14} color="#2196F3" />
            <Text style={[styles.contextButtonText, { color: '#2196F3' }]}>Libérer</Text>
          </TouchableOpacity>
        )}
        {item.statut === 'AVAILABLE' && (
          <TouchableOpacity style={[styles.contextButton, { backgroundColor: '#FFF3E0' }]} onPress={() => handleMaintenance(item.id_chariot)}>
            <Feather name="tool" size={14} color="#FF9800" />
            <Text style={[styles.contextButtonText, { color: '#FF9800' }]}>Maintenance</Text>
          </TouchableOpacity>
        )}
      </View>
    </CollapsibleManagementCard>
  );

  return (
    <View style={styles.container}>
      <StatusBar barStyle="dark-content" />
      <View style={styles.header}>
        <View>
          <Text style={styles.title}>Chariots</Text>
          <Text style={styles.subtitle}>{selectedWarehouseId ? warehouses.find(w => String(w.id_entrepot) === selectedWarehouseId)?.nom_entrepot : 'Tous les entrepôts'}</Text>
        </View>
        <View style={styles.headerActions}>
          <TouchableOpacity style={styles.filterButton} onPress={() => setWarehouseFilterModalVisible(true)}>
            <Feather name="filter" size={20} color="#2196F3" />
          </TouchableOpacity>
          <TouchableOpacity style={styles.addButton} onPress={() => {
            setNewChariot({
              code_chariot: '',
              id_entrepot_id: selectedWarehouseId || (warehouses[0]?.id_entrepot?.toString() || ''),
              statut: 'AVAILABLE',
              capacite: ''
            });
            setIsEditing(false);
            setModalVisible(true);
          }}>
            <Feather name="plus" size={24} color="#FFF" />
          </TouchableOpacity>
        </View>
      </View>

      {loading && !refreshing ? (
        <View style={styles.centered}><ActivityIndicator size="large" color="#2196F3" /></View>
      ) : (
        <FlatList
          data={chariots}
          keyExtractor={(item) => String(item.id_chariot)}
          renderItem={renderChariotItem}
          contentContainerStyle={styles.listContent}
          onRefresh={onRefresh}
          refreshing={refreshing}
          ListEmptyComponent={
            <View style={styles.centered}>
                <Text style={styles.emptyText}>Aucun chariot trouvé</Text>
            </View>
          }
        />
      )}

      <ManagementModal
        visible={warehouseFilterModalVisible}
        onClose={() => setWarehouseFilterModalVisible(false)}
        title="Filtrer par Entrepôt"
        submitLabel="Appliquer"
        onSubmit={() => {
          setWarehouseFilterModalVisible(false);
          fetchData(selectedWarehouseId);
        }}
      >
        <OptionSelector
          label="Entrepôt"
          options={[
            { label: "Tous les entrepôts", value: "" },
            ...warehouses.map(w => ({ label: w.nom_entrepot, value: String(w.id_entrepot) }))
          ]}
          selectedValue={selectedWarehouseId}
          onValueChange={(val) => setSelectedWarehouseId(val)}
          icon="home"
        />
      </ManagementModal>

      <ManagementModal
        visible={modalVisible}
        onClose={() => setModalVisible(false)}
        title={isEditing ? 'Modifier Chariot' : 'Nouveau Chariot'}
        onSubmit={handleSubmitChariot}
        submitting={submitting}
        submitLabel={isEditing ? 'Mettre à jour' : 'Créer'}
      >
        <View style={styles.formGroup}>
          <Text style={styles.label}>Code Chariot *</Text>
          <View style={styles.inputContainer}>
            <Feather name="hash" size={18} color="#94A3B8" style={styles.inputIcon} />
            <TextInput
              style={styles.input}
              placeholder="e.g., CH-001"
              value={newChariot.code_chariot}
              onChangeText={(text) => setNewChariot({...newChariot, code_chariot: text})}
              placeholderTextColor="#94A3B8"
            />
          </View>
        </View>

        <View style={styles.formGroup}>
          <OptionSelector
            label="Entrepôt *"
            options={warehouses.map(w => ({ label: w.nom_entrepot, value: String(w.id_entrepot) }))}
            selectedValue={newChariot.id_entrepot_id}
            onValueChange={(val) => setNewChariot({...newChariot, id_entrepot_id: val})}
            icon="home"
          />
        </View>

        <View style={styles.formGroup}>
          <Text style={styles.label}>Capacité (kg)</Text>
          <View style={styles.inputContainer}>
            <Feather name="box" size={18} color="#94A3B8" style={styles.inputIcon} />
            <TextInput
              style={styles.input}
              placeholder="e.g., 500"
              keyboardType="numeric"
              value={newChariot.capacite}
              onChangeText={(text) => setNewChariot({...newChariot, capacite: text})}
              placeholderTextColor="#94A3B8"
            />
          </View>
        </View>

        <View style={styles.formGroup}>
          <OptionSelector
            label="Statut"
            options={[
              { label: "Disponible", value: "AVAILABLE" },
              { label: "Maintenance", value: "MAINTENANCE" },
              { label: "En Cours", value: "IN_USE" },
              { label: "Inactif", value: "INACTIVE" },
            ]}
            selectedValue={newChariot.statut}
            onValueChange={(val) => setNewChariot({...newChariot, statut: val})}
            icon="info"
          />
        </View>
      </ManagementModal>
    </View>
  );
};

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: '#F8F9FA' },
  centered: { flex: 1, justifyContent: 'center', alignItems: 'center' },
  emptyText: { color: '#94A3B8', marginTop: 20, fontSize: 16 },
  header: {
    paddingHorizontal: 24,
    paddingTop: 60,
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
    width: 48, height: 48, borderRadius: 14, backgroundColor: '#2196F3',
    justifyContent: 'center', alignItems: 'center', marginLeft: 12,
    elevation: 4, shadowColor: '#2196F3', shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.3, shadowRadius: 8
  },
  filterButton: {
    width: 48, height: 48, borderRadius: 14, backgroundColor: '#F1F5F9',
    justifyContent: 'center', alignItems: 'center'
  },
  listContent: { paddingVertical: 12, paddingBottom: 100 },
  label: { fontSize: 14, fontWeight: '700', marginBottom: 8, color: '#475569' },
  formGroup: { marginBottom: 20 },
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
  cardActions: {
    flexDirection: 'row',
    marginTop: 12,
    paddingTop: 12,
    borderTopWidth: 1,
    borderTopColor: '#F0F2F5'
  },
  contextButton: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingHorizontal: 16,
    paddingVertical: 8,
    borderRadius: 10,
    marginRight: 10
  },
  contextButtonText: {
    fontSize: 13,
    fontWeight: '700',
    marginLeft: 6
  }
});

export default ChariotManagement;
