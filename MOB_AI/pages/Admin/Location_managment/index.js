import React, { useState, useEffect, useCallback, useRef } from 'react';
import { 
  View, 
  Text, 
  StyleSheet, 
  FlatList, 
  ActivityIndicator, 
  TouchableOpacity, 
  Alert, 
  TextInput,
  Switch,
  StatusBar
} from 'react-native';
import { Feather } from '@expo/vector-icons';
import { warehouseService } from '../../../services/warehouseService';
import CollapsibleManagementCard from '../../../components/CollapsibleManagementCard';
import ManagementModal from '../../../components/ManagementModal';
import OptionSelector from '../../../components/OptionSelector';
import { lightTheme } from '../../../constants/theme';

const PAGE_SIZE = 20;

const LocationManagement = () => {
  const [locations, setLocations] = useState([]);
  const [warehouses, setWarehouses] = useState([]);
  const [selectedWarehouseId, setSelectedWarehouseId] = useState('');
  const [warehouseFilterModalVisible, setWarehouseFilterModalVisible] = useState(false);
  const [floors, setFloors] = useState([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
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

  const fetchData = async (warehouseIdOverride = null) => {
    try {
      setLoading(true);
      const whData = await warehouseService.getWarehouses();
      const safeWarehouses = Array.isArray(whData) ? whData : [];
      setWarehouses(safeWarehouses);

      const effectiveWhId = (warehouseIdOverride || selectedWarehouseId || '').toString().trim();
      setSelectedWarehouseId(effectiveWhId);

      if (!effectiveWhId) {
        setLocations([]);
        setFloors([]);
        return;
      }

      const [locsResponse, stockFloors, pickingFloors] = await Promise.all([
        warehouseService.getLocationsPaged(effectiveWhId, { limit: PAGE_SIZE, offset: 0 }),
        warehouseService.getFloors(effectiveWhId),
        warehouseService.getPickingFloors(effectiveWhId)
      ]);

      setLocations(locsResponse?.results || []);
      setCurrentOffset(locsResponse?.results?.length || 0);
      setHasMore(Boolean(locsResponse?.has_more));
      
      const allFloors = [
        ...(stockFloors || []).map(f => ({ ...f, id_niveau: f.id_niveau, displayType: 'STOCK' })),
        ...(pickingFloors || []).map(f => ({ ...f, id_niveau: f.id_niveau_picking, displayType: 'PICKING' }))
      ];
      setFloors(allFloors);
    } catch (error) {
      console.error('Error fetching locations:', error);
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

  const loadMore = async () => {
    if (loadingMore || !hasMore || !selectedWarehouseId) return;

    try {
      setLoadingMore(true);
      const response = await warehouseService.getLocationsPaged(selectedWarehouseId, {
        limit: PAGE_SIZE,
        offset: currentOffset,
      });

      const nextLocs = response?.results || [];
      if (nextLocs.length > 0) {
        setLocations(prev => [...prev, ...nextLocs]);
        setCurrentOffset(prev => prev + nextLocs.length);
      }
      setHasMore(Boolean(response?.has_more));
    } catch (error) {
      console.error('Error loading more:', error);
    } finally {
      setLoadingMore(false);
    }
  };

  const handleSubmit = async () => {
    if (!newLocation.code_emplacement || !newLocation.id_entrepot_id) {
      Alert.alert('Error', 'Please fill in required fields');
      return;
    }

    try {
      setSubmitting(true);
      const selectedFloor = floors.find(f => f.id_niveau === newLocation.id_niveau_id);
      const submissionData = { ...newLocation };
      
      if (selectedFloor) {
        if (selectedFloor.displayType === 'PICKING') {
          submissionData.picking_floor_id = selectedFloor.id_niveau;
        } else {
          submissionData.storage_floor_id = selectedFloor.id_niveau;
        }
      }
      delete submissionData.id_niveau_id;

      if (isEditing) {
        await warehouseService.updateLocation(editingId, submissionData);
      } else {
        await warehouseService.createLocation(submissionData);
      }
      setModalVisible(false);
      fetchData(selectedWarehouseId);
      Alert.alert('Success', `Location ${isEditing ? 'updated' : 'added'} successfully`);
    } catch (error) {
      Alert.alert('Error', 'Failed to save location');
    } finally {
      setSubmitting(false);
    }
  };

  const handleDelete = (id) => {
    Alert.alert('Delete Location', 'Delete this location?', [
      { text: 'Cancel', style: 'cancel' },
      { text: 'Delete', style: 'destructive', onPress: async () => {
        try {
          await warehouseService.deleteLocation(id);
          fetchData(selectedWarehouseId);
        } catch (error) {
          Alert.alert('Error', 'Failed to delete');
        }
      }}
    ]);
  };

  const openEdit = (loc) => {
    setNewLocation({
      code_emplacement: loc.code_emplacement,
      id_entrepot_id: String(loc.id_entrepot?.id_entrepot || loc.id_entrepot),
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

  const renderItem = ({ item }) => (
    <CollapsibleManagementCard
      title={item.code_emplacement}
      subtitle={item.id_entrepot?.nom_entrepot || 'N/A'}
      status={item.statut}
      icon="map-pin"
      iconColor={item.actif ? '#4CAF50' : '#8E8E93'}
      details={[
        { label: 'Type', value: item.type_emplacement },
        { label: 'Zone', value: item.zone || 'None' },
        { label: 'Level', value: item.storage_floor?.code_niveau || item.picking_floor?.code_niveau || 'N/A' },
        { label: 'Status', value: item.statut },
        { label: 'Active', value: item.actif ? 'Yes' : 'No' },
        { label: 'ID', value: String(item.id_emplacement) }
      ]}
      onEdit={() => openEdit(item)}
      onDelete={() => handleDelete(item.id_emplacement)}
    />
  );

  return (
    <View style={styles.container}>
      <StatusBar barStyle="dark-content" />
      <View style={styles.header}>
        <View>
          <Text style={styles.title}>Locations</Text>
          <Text style={styles.subtitle}>{selectedWarehouseId ? warehouses.find(w => String(w.id_entrepot) === selectedWarehouseId)?.nom_entrepot : 'Select Warehouse'}</Text>
        </View>
        <View style={styles.headerActions}>
          <TouchableOpacity style={styles.filterButton} onPress={() => setWarehouseFilterModalVisible(true)}>
            <Feather name="filter" size={20} color="#007AFF" />
          </TouchableOpacity>
          <TouchableOpacity style={styles.addButton} onPress={() => {
            if (!selectedWarehouseId) {
              Alert.alert('No Warehouse Selected', 'Please select a warehouse first before adding a location.');
              return;
            }
            setNewLocation({
              code_emplacement: '',
              id_entrepot_id: selectedWarehouseId,
              id_niveau_id: '',
              zone: '',
              type_emplacement: 'STORAGE',
              statut: 'AVAILABLE',
              actif: true
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
          data={locations}
          keyExtractor={(item) => String(item.id_emplacement)}
          renderItem={renderItem}
          contentContainerStyle={styles.listContent}
          onRefresh={onRefresh}
          refreshing={refreshing}
          onEndReached={loadMore}
          onEndReachedThreshold={0.5}
          ListFooterComponent={loadingMore ? <ActivityIndicator size="small" color={lightTheme.primary} style={{ padding: 10 }} /> : null}
          ListEmptyComponent={!loading && <View style={styles.centered}><Text style={styles.emptyText}>No locations found. Select a warehouse.</Text></View>}
        />
      )}

      <ManagementModal
        visible={warehouseFilterModalVisible}
        onClose={() => setWarehouseFilterModalVisible(false)}
        title="Filter Warehouse"
        submitLabel="Apply"
        onSubmit={() => {
          setWarehouseFilterModalVisible(false);
          fetchData(selectedWarehouseId);
        }}
      >
        <OptionSelector
          label="Warehouse"
          options={warehouses.map(w => ({ label: w.nom_entrepot, value: String(w.id_entrepot) }))}
          selectedValue={selectedWarehouseId}
          onValueChange={(val) => setSelectedWarehouseId(val)}
          placeholder="Select a warehouse"
          icon="home"
        />
      </ManagementModal>

      <ManagementModal
        visible={modalVisible}
        onClose={() => setModalVisible(false)}
        title={isEditing ? 'Update Location' : 'New Location'}
        onSubmit={handleSubmit}
        submitting={submitting}
        submitLabel={isEditing ? 'Update' : 'Create'}
      >
        <View style={styles.formGroup}>
          <Text style={styles.label}>Location Code *</Text>
          <View style={styles.inputContainer}>
            <Feather name="hash" size={18} color="#94A3B8" style={styles.inputIcon} />
            <TextInput
              style={styles.input}
              placeholder="e.g., A-01-01"
              value={newLocation.code_emplacement}
              onChangeText={(t) => setNewLocation({...newLocation, code_emplacement: t})}
              placeholderTextColor="#94A3B8"
            />
          </View>
        </View>

        <View style={styles.formGroup}>
          <OptionSelector
            label="Level / Floor"
            options={floors.map(f => ({ label: `${f.code_niveau} (${f.displayType})`, value: f.id_niveau }))}
            selectedValue={newLocation.id_niveau_id}
            onValueChange={(val) => setNewLocation({...newLocation, id_niveau_id: val})}
            placeholder="No Level Assigned"
            icon="layers"
          />
        </View>

        <View style={styles.row}>
          <View style={[styles.formGroup, { flex: 1, marginRight: 10 }]}>
            <Text style={styles.label}>Zone</Text>
            <View style={styles.inputContainer}>
              <Feather name="grid" size={18} color="#94A3B8" style={styles.inputIcon} />
              <TextInput
                style={styles.input}
                placeholder="Zone"
                value={newLocation.zone}
                onChangeText={(t) => setNewLocation({...newLocation, zone: t})}
                placeholderTextColor="#94A3B8"
              />
            </View>
          </View>
          <View style={[styles.formGroup, { flex: 1 }]}>
            <OptionSelector
              label="Type"
              options={[
                { label: "Storage", value: "STORAGE" },
                { label: "Picking", value: "PICKING" },
                { label: "Shipping", value: "EXPEDITION" },
                { label: "Dock", value: "QUAI" },
              ]}
              selectedValue={newLocation.type_emplacement}
              onValueChange={(val) => setNewLocation({...newLocation, type_emplacement: val})}
              icon="tag"
            />
          </View>
        </View>

        <View style={styles.formGroup}>
          <OptionSelector
            label="Status"
            options={[
              { label: "Available", value: "AVAILABLE" },
              { label: "Full", value: "FULL" },
              { label: "Reserved", value: "RESERVED" },
              { label: "Blocked", value: "BLOCKED" },
            ]}
            selectedValue={newLocation.statut}
            onValueChange={(val) => setNewLocation({...newLocation, statut: val})}
            icon="info"
          />
        </View>

        <View style={styles.switchGroup}>
          <View style={styles.switchInfo}>
            <Text style={styles.label}>Active Status</Text>
            <Text style={styles.switchSubtitle}>Visible in warehouse operations</Text>
          </View>
          <Switch
            value={newLocation.actif}
            onValueChange={(v) => setNewLocation({...newLocation, actif: v})}
            trackColor={{ false: '#D1D1D6', true: '#34C759' }}
            thumbColor="#FFF"
          />
        </View>
      </ManagementModal>
    </View>
  );
};

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: lightTheme.primary },
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
    width: 48, height: 48, borderRadius: 14, backgroundColor: lightTheme.primary,
    justifyContent: 'center', alignItems: 'center', marginLeft: 12,
    elevation: 4, shadowColor: lightTheme.primary, shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.3, shadowRadius: 8
  },
  filterButton: {
    width: 48, height: 48, borderRadius: 14, backgroundColor: '#F1F5F9',
    justifyContent: 'center', alignItems: 'center'
  },
  listContent: { paddingVertical: 12, paddingBottom: 100 },
  centered: { flex: 1, justifyContent: 'center', alignItems: 'center' },
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
    color: '#1a1a1a',
  },
  input: { flex: 1, height: 54, fontSize: 16, color: '#1E293B' },
  row: { flexDirection: 'row', alignItems: 'center' },
  switchGroup: { 
    flexDirection: 'row', 
    justifyContent: 'space-between', 
    alignItems: 'center', 
    paddingVertical: 15,
    backgroundColor: '#F8FAFC',
    paddingHorizontal: 15,
    borderRadius: 12,
    borderWidth: 1,
    borderColor: '#E2E8F0'
  },
  switchInfo: { flex: 1 },
  switchSubtitle: { fontSize: 12, color: '#94A3B8', marginTop: -4 },
  emptyText: { color: '#94A3B8', marginTop: 20, fontSize: 16 },
});

export default LocationManagement;
