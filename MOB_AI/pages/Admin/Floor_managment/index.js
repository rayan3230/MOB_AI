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
import CollapsibleManagementCard from '../../../components/CollapsibleManagementCard';
import ManagementModal from '../../../components/ManagementModal';
import { lightTheme } from '../../../constants/theme';

const FLOOR_CACHE_TTL_MS = 2 * 60 * 1000;

const FloorManagement = () => {
  const [floors, setFloors] = useState([]);
  const [warehouses, setWarehouses] = useState([]);
  const [selectedWarehouseId, setSelectedWarehouseId] = useState('');
  const [warehouseFilterModalVisible, setWarehouseFilterModalVisible] = useState(false);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
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
    if (!Array.isArray(floors)) return [];
    return floors.map((floor) => ({
      ...floor,
      id_niveau: floor.id_niveau || floor.id_niveau_picking,
      type_niveau: floor.type_niveau || (floor.id_niveau_picking ? 'PICKING' : 'STOCK'),
    }));
  };

  const getCachedFloors = (warehouseId) => {
    const cacheEntry = floorsCacheRef.current[String(warehouseId)];
    return cacheEntry && (Date.now() - cacheEntry.cachedAt < FLOOR_CACHE_TTL_MS) ? cacheEntry.data : null;
  };

  const setCachedFloors = (warehouseId, floors) => {
    floorsCacheRef.current[String(warehouseId)] = { data: floors, cachedAt: Date.now() };
  };

  const fetchFloorsForWarehouse = async (warehouseId, { forceRefresh = false } = {}) => {
    const key = String(warehouseId);
    if (!forceRefresh) {
      const cached = getCachedFloors(key);
      if (cached) return cached;
    }
    const rawFloors = await warehouseService.getWarehouseFloors(key);
    const normalized = normalizeFloors(rawFloors);
    setCachedFloors(key, normalized);
    return normalized;
  };

  const fetchData = async (warehouseIdOverride = null, { forceRefresh = false } = {}) => {
    try {
      setLoading(true);
      const warehousesData = await warehouseService.getWarehouses();
      const safeWarehouses = Array.isArray(warehousesData) ? warehousesData : [];
      setWarehouses(safeWarehouses);

      const effectiveWhId = (warehouseIdOverride || selectedWarehouseId || '').toString().trim();
      const isKnown = safeWarehouses.some(w => String(w.id_entrepot) === effectiveWhId);

      if (safeWarehouses.length === 0) {
        setFloors([]);
        return;
      }

      if (!effectiveWhId || !isKnown) {
        const results = await Promise.all(safeWarehouses.map(w => fetchFloorsForWarehouse(w.id_entrepot, { forceRefresh })));
        setFloors(results.flat());
        setSelectedWarehouseId('');
      } else {
        const warehouseFloors = await fetchFloorsForWarehouse(effectiveWhId, { forceRefresh });
        setFloors(warehouseFloors);
        setSelectedWarehouseId(effectiveWhId);
      }
    } catch (error) {
      console.error('Error fetching floors:', error);
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  };

  useEffect(() => { fetchData(); }, []);

  const onRefresh = () => {
    setRefreshing(true);
    fetchData(selectedWarehouseId, { forceRefresh: true });
  };

  const handleSubmitFloor = async () => {
    if (!newFloor.code_niveau || !newFloor.id_entrepot_id) {
      Alert.alert('Erreur', 'Veuillez remplir les champs obligatoires');
      return;
    }

    try {
      setSubmitting(true);
      let result;
      if (isEditing) {
        result = await warehouseService.updateFloor(editingId, newFloor);
      } else {
        result = await warehouseService.createFloor(newFloor);
      }

      if (result?._queued) {
        Alert.alert('Buffered Change', 'Floor changes have been queued for sync.');
      } else {
        Alert.alert('Success', `Niveau ${isEditing ? 'mis à jour' : 'ajouté'} avec succès`);
      }

      floorsCacheRef.current = {};
      setModalVisible(false);
      fetchData(selectedWarehouseId, { forceRefresh: true });
    } catch (error) {
      Alert.alert('Erreur', error.detail || 'Échec de l\'opération');
    } finally {
      setSubmitting(false);
    }
  };

  const handleDeleteFloor = (id, type) => {
    Alert.alert('Supprimer Niveau', 'Êtes-vous sûr ?', [
      { text: 'Annuler', style: 'cancel' },
      { 
        text: 'Supprimer', style: 'destructive',
        onPress: async () => {
          try {
            const result = await warehouseService.deleteFloor(id, type);
            if (result?._queued) {
              Alert.alert('Buffered Deletion', 'Floor deletion queued for sync.');
            }
            floorsCacheRef.current = {};
            fetchData(selectedWarehouseId, { forceRefresh: true });
          } catch (error) {
            Alert.alert('Erreur', 'Échec de la suppression');
          }
        }
      }
    ]);
  };

  const openEditModal = (floor) => {
    setNewFloor({
      code_niveau: floor.code_niveau,
      type_niveau: floor.type_niveau || 'STOCK',
      description: floor.description || '',
      id_entrepot_id: String(floor.id_entrepot?.id_entrepot || floor.id_entrepot)
    });
    setEditingId(floor.id_niveau);
    setIsEditing(true);
    setModalVisible(true);
  };

  const renderFloorItem = ({ item }) => (
    <CollapsibleManagementCard
      title={item.code_niveau}
      subtitle={item.id_entrepot?.nom_entrepot || 'Entrepôt Inconnu'}
      status={item.type_niveau === 'PICKING' ? 'PICKING' : 'STOCKAGE'}
      iconName="layers"
      iconColor={item.type_niveau === 'PICKING' ? '#FF9800' : '#4CAF50'}
      details={[
        { label: 'Type', value: item.type_niveau },
        { label: 'Description', value: item.description || 'Pas de description' },
        { label: 'Entrepôt', value: item.id_entrepot?.nom_entrepot },
      ]}
      onEdit={() => openEditModal(item)}
      onDelete={() => handleDeleteFloor(item.id_niveau, item.type_niveau)}
    />
  );

  return (
    <View style={styles.container}>
      <StatusBar barStyle="dark-content" />
      <View style={styles.header}>
        <View>
          <Text style={styles.title}>Niveaux</Text>
          <Text style={styles.subtitle}>
            {selectedWarehouseId 
              ? warehouses.find(w => String(w.id_entrepot) === selectedWarehouseId)?.nom_entrepot 
              : 'Tous les entrepôts'}
          </Text>
        </View>
        <View style={styles.headerActions}>
          <TouchableOpacity 
            style={styles.filterButton} 
            onPress={() => setWarehouseFilterModalVisible(true)}
          >
            <Feather name="filter" size={20} color="#2196F3" />
          </TouchableOpacity>
          <TouchableOpacity style={styles.addButton} onPress={() => {
            setNewFloor({
              code_niveau: '',
              type_niveau: 'STOCK',
              description: '',
              id_entrepot_id: selectedWarehouseId || (warehouses[0]?.id_entrepot?.toString() || '')
            });
            setIsEditing(false);
            setModalVisible(true);
          }}>
            <Feather name="plus" size={24} color="#FFF" />
          </TouchableOpacity>
        </View>
      </View>

      {loading && !refreshing ? (
        <View style={styles.centered}><ActivityIndicator size="large" color={lightTheme.primary} /></View>
      ) : (
        <FlatList
          data={floors}
          keyExtractor={(item) => String(item.id_niveau)}
          renderItem={renderFloorItem}
          contentContainerStyle={styles.listContent}
          onRefresh={onRefresh}
          refreshing={refreshing}
          ListEmptyComponent={
            <View style={styles.centered}>
                <Text style={styles.emptyText}>Aucun niveau trouvé</Text>
            </View>
          }
        />
      )}

      {/* Filter Modal */}
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

      {/* Edit/Create Modal */}
      <ManagementModal
        visible={modalVisible}
        onClose={() => setModalVisible(false)}
        title={isEditing ? 'Modifier Niveau' : 'Nouveau Niveau'}
        onSave={handleSubmitFloor}
        submitting={submitting}
      >
        <View style={styles.formGroup}>
          <Text style={styles.label}>Code Niveau *</Text>
          <View style={styles.inputContainer}>
            <TextInput
              style={styles.input}
              placeholder="e.g., F1-STOCK"
              value={newFloor.code_niveau}
              onChangeText={(text) => setNewFloor({...newFloor, code_niveau: text})}
            />
          </View>
        </View>

        <View style={styles.formGroup}>
          <OptionSelector
            label="Entrepôt *"
            options={warehouses.map(w => ({ label: w.nom_entrepot, value: String(w.id_entrepot) }))}
            selectedValue={newFloor.id_entrepot_id}
            onValueChange={(val) => setNewFloor({...newFloor, id_entrepot_id: val})}
            icon="home"
          />
        </View>

        <View style={styles.formGroup}>
          <OptionSelector
            label="Type"
            options={[
              { label: "Stockage", value: "STOCK" },
              { label: "Picking", value: "PICKING" },
            ]}
            selectedValue={newFloor.type_niveau}
            onValueChange={(val) => setNewFloor({...newFloor, type_niveau: val})}
            icon="tag"
          />
        </View>

        <View style={styles.formGroup}>
          <Text style={styles.label}>Description</Text>
          <View style={[styles.inputContainer, { height: 100 }]}>
            <TextInput
              style={[styles.input, { textAlignVertical: 'top', paddingTop: 10 }]}
              placeholder="Description..."
              multiline
              numberOfLines={4}
              value={newFloor.description}
              onChangeText={(text) => setNewFloor({...newFloor, description: text})}
            />
          </View>
        </View>
      </ManagementModal>
    </View>
  );
};

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: lightTheme.primary },
  centered: { flex: 1, justifyContent: 'center', alignItems: 'center' },
  emptyText: { color: '#666', fontSize: 16 },
  header: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    paddingHorizontal: 20,
    paddingBottom: 20,
    backgroundColor: '#FFF',
    borderBottomWidth: 1,
    borderBottomColor: '#EEE'
  },
  headerActions: { flexDirection: 'row', alignItems: 'center' },
  title: { fontSize: 28, fontWeight: '700', color: '#1a1a1a' },
  subtitle: { fontSize: 14, color: '#666', marginTop: 2 },
  addButton: {
    width: 48, height: 48, borderRadius: 14, backgroundColor: lightTheme.primary,
    justifyContent: 'center', alignItems: 'center', marginLeft: 12, elevation: 4
  },
  filterButton: {
    width: 48, height: 48, borderRadius: 14, backgroundColor: '#F0F2F5',
    justifyContent: 'center', alignItems: 'center'
  },
  listContent: { padding: 16, paddingBottom: 100 },
  label: { fontSize: 15, fontWeight: '600', marginBottom: 8, color: '#444' },
  formGroup: { marginBottom: 16 },
  inputContainer: {
    backgroundColor: '#F8F9FA', borderRadius: 12, paddingHorizontal: 12,
    borderWidth: 1, borderColor: '#E9ECEF'
  },
  pickerContainer: {
    backgroundColor: '#F8F9FA', borderRadius: 12, borderWidth: 1, borderColor: '#E9ECEF', 
    overflow: 'hidden'
  },
  input: { height: 50, fontSize: 16, color: '#1a1a1a' }
});

export default FloorManagement;
