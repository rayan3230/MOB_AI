import React, { useEffect, useState } from 'react';
import { View, Text, StyleSheet, ActivityIndicator, ScrollView, TouchableOpacity } from 'react-native';
import { Feather } from '@expo/vector-icons';
import { warehouseService } from '../../../services/warehouseService';
import { lightTheme } from '../../../constants/theme';
import WarehouseMap from '../../../components/WarehouseMap';
import OptionSelector from '../../../components/OptionSelector';
import ManagementModal from '../../../components/ManagementModal';

const VisualWarehouse = () => {
  const [loading, setLoading] = useState(true);
  const [warehouses, setWarehouses] = useState([]);
  const [selectedWarehouseId, setSelectedId] = useState('');
  const [warehouseFilterModalVisible, setWarehouseFilterModalVisible] = useState(false);
  const [floors, setFloors] = useState([]);
  const [isOffline, setIsOffline] = useState(false);
  const [floorIdx, setFloorIdx] = useState(0);

  const selectedWarehouse = warehouses.find(w => String(w.id_entrepot) === selectedWarehouseId);
  const floorOptions = [
    { label: 'Ground / Picking', value: 0 },
    { label: 'Level 1 & 2', value: 1 },
    { label: 'Level 3 & 4', value: 2 },
  ];

  useEffect(() => {
    loadWarehouses();
  }, []);

  const loadWarehouses = async () => {
    try {
      setLoading(true);
      const whs = await warehouseService.getWarehouses();
      setWarehouses(whs);
      if (whs.length > 0) {
        setSelectedId(String(whs[0].id_entrepot));
        loadMapData(String(whs[0].id_entrepot));
      }
    } catch (error) {
      console.error('Error loading warehouses:', error);
    } finally {
      setLoading(false);
    }
  };

  const loadMapData = async (whId) => {
    try {
      const floorData = await warehouseService.getWarehouseFloors(whId);
      setFloors(floorData);
      setIsOffline(false);
    } catch (error) {
      setIsOffline(true);
      console.log('Using cached map data');
    }
  };

  const handleApplyFilter = () => {
    setWarehouseFilterModalVisible(false);
    if (selectedWarehouseId) {
      loadMapData(selectedWarehouseId);
    }
  };

  if (loading) {
    return (
      <View style={styles.center}>
        <ActivityIndicator size="large" color={lightTheme.primary} />
        <Text style={styles.loadingText}>Loading warehouse data...</Text>
      </View>
    );
  }

  return (
    <View style={styles.container}>
      {isOffline && (
        <View style={styles.offlineBanner}>
          <Feather name="wifi-off" size={16} color={lightTheme.white} />
          <Text style={styles.offlineText}>Viewing cached map data (Offline)</Text>
        </View>
      )}
      
      <ScrollView contentContainerStyle={styles.content}>
        <View style={styles.header}>
          <View>
            <Text style={styles.title}>Visual Warehouse</Text>
            <Text style={styles.subtitle}>
              {selectedWarehouse ? selectedWarehouse.nom_entrepot : 'Select Warehouse'}
            </Text>
          </View>
          <View style={styles.headerActions}>
            <TouchableOpacity 
              style={styles.filterButton} 
              onPress={() => setWarehouseFilterModalVisible(true)}
            >
              <Feather name="filter" size={20} color="#007AFF" />
            </TouchableOpacity>
          </View>
        </View>

        <View style={styles.controls}>
          <View style={styles.selectorContainer}>
            <OptionSelector
              label="Select Floor"
              options={floorOptions}
              selectedValue={floorIdx}
              onValueChange={setFloorIdx}
              icon="layers"
            />
          </View>
        </View>

        {/* Map Visualization Container */}
        <View style={styles.mapContainer}>
          <WarehouseMap 
            warehouseId={selectedWarehouseId}
            floorIdx={floorIdx} 
          />
        </View>

        <View style={styles.statsRow}>
          <View style={styles.statCard}>
            <Text style={styles.statLabel}>Selected Floor</Text>
            <Text style={styles.statValue}>{floorOptions.find(f => f.value === floorIdx)?.label}</Text>
          </View>
          <View style={styles.statCard}>
            <Text style={styles.statLabel}>Status</Text>
            <Text style={[styles.statValue, { color: isOffline ? lightTheme.warning : lightTheme.success }]}>
              {isOffline ? 'Cached' : 'Live'}
            </Text>
          </View>
        </View>
        
        <View style={styles.legendContainer}>
          <Text style={styles.legendTitle}>Rack Status Legend</Text>
          <View style={styles.legendRow}>
            <View style={[styles.legendDot, { backgroundColor: '#2ecc71' }]} />
            <Text style={styles.legendText}>OCCUPIED (Contains Products)</Text>
          </View>
          <View style={styles.legendRow}>
            <View style={[styles.legendDot, { backgroundColor: '#3498db' }]} />
            <Text style={styles.legendText}>FREE (Available Space)</Text>
          </View>
          <View style={styles.legendRow}>
            <View style={[styles.legendDot, { backgroundColor: '#9b59b6' }]} />
            <Text style={styles.legendText}>Transitions / Stairs</Text>
          </View>
          <View style={styles.legendRow}>
            <View style={[styles.legendDot, { backgroundColor: '#fbc531' }]} />
            <Text style={styles.legendText}>Loading & Shipping Zones</Text>
          </View>
        </View>
      </ScrollView>

      <ManagementModal
        visible={warehouseFilterModalVisible}
        onClose={() => setWarehouseFilterModalVisible(false)}
        title="Select Warehouse"
        submitLabel="Apply"
        onSubmit={handleApplyFilter}
      >
        <OptionSelector
          label="Warehouse"
          options={warehouses.map(w => ({ label: w.nom_entrepot, value: String(w.id_entrepot) }))}
          selectedValue={selectedWarehouseId}
          onValueChange={(val) => setSelectedId(val)}
          placeholder="Select a warehouse"
          icon="home"
        />
      </ManagementModal>
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: lightTheme.background,
  },
  center: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    backgroundColor: lightTheme.background,
  },
  content: {
    padding: 16,
    paddingBottom: 40,
  },
  offlineBanner: {
    backgroundColor: lightTheme.warning,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    paddingVertical: 8,
    gap: 8,
  },
  offlineText: {
    color: lightTheme.white,
    fontSize: 12,
    fontWeight: '600',
  },
  header: {
    marginBottom: 20,
    marginTop: 40,
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingHorizontal: 8,
  },
  headerActions: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  filterButton: {
    width: 44,
    height: 44,
    borderRadius: 12,
    backgroundColor: '#FFF',
    justifyContent: 'center',
    alignItems: 'center',
    borderWidth: 1,
    borderColor: '#E2E8F0',
  },
  title: {
    fontSize: 24,
    fontWeight: '700',
    color: lightTheme.textPrimary,
  },
  subtitle: {
    fontSize: 16,
    color: lightTheme.textSecondary,
    marginTop: 4,
  },
  controls: {
    marginBottom: 20,
    gap: 12,
  },
  selectorContainer: {
    backgroundColor: '#FFF',
    borderRadius: 12,
    borderWidth: 1,
    borderColor: '#E2E8F0',
  },
  modeToggle: {
    flexDirection: 'row',
    backgroundColor: '#E2E8F0',
    padding: 4,
    borderRadius: 10,
  },
  modeButton: {
    flex: 1,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    paddingVertical: 8,
    gap: 8,
    borderRadius: 8,
  },
  activeMode: {
    backgroundColor: lightTheme.primary,
  },
  modeText: {
    fontSize: 14,
    fontWeight: '600',
    color: '#64748B',
  },
  activeModeText: {
    color: '#FFF',
  },
  mapContainer: {
    height: 400,
    backgroundColor: lightTheme.white,
    borderRadius: 16,
    borderWidth: 1,
    borderColor: lightTheme.border,
    justifyContent: 'center',
    alignItems: 'center',
    overflow: 'hidden',
    marginBottom: 16,
  },
  statsRow: {
    flexDirection: 'row',
    gap: 12,
    marginBottom: 16,
  },
  statCard: {
    flex: 1,
    backgroundColor: lightTheme.white,
    padding: 16,
    borderRadius: 12,
    borderWidth: 1,
    borderColor: lightTheme.border,
  },
  statLabel: {
    fontSize: 12,
    color: lightTheme.textSecondary,
    textTransform: 'uppercase',
    letterSpacing: 1,
  },
  statValue: {
    fontSize: 16,
    fontWeight: '700',
    color: lightTheme.textPrimary,
    marginTop: 4,
  },
  legendContainer: {
    backgroundColor: lightTheme.white,
    padding: 16,
    borderRadius: 12,
    borderWidth: 1,
    borderColor: lightTheme.border,
  },
  legendTitle: {
    fontSize: 14,
    fontWeight: '700',
    color: lightTheme.textPrimary,
    marginBottom: 12,
  },
  legendRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 12,
    marginBottom: 8,
  },
  legendDot: {
    width: 12,
    height: 12,
    borderRadius: 6,
  },
  legendText: {
    fontSize: 13,
    color: lightTheme.textSecondary,
  },
  loadingText: {
    marginTop: 12,
    color: lightTheme.textSecondary,
  }
});

export default VisualWarehouse;

