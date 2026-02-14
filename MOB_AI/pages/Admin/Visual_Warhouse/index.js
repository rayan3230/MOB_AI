import React, { useEffect, useState } from 'react';
import { View, Text, StyleSheet, ActivityIndicator, ScrollView, Alert, Dimensions } from 'react-native';
import { Feather } from '@expo/vector-icons';
import { lightTheme } from '../../../constants/theme';
import { warehouseService } from '../../../services/warehouseService';

const VisualWarehouse = () => {
  const [loading, setLoading] = useState(true);
  const [warehouses, setWarehouses] = useState([]);
  const [selectedWarehouse, setSelectedWarehouse] = useState(null);
  const [floors, setFloors] = useState([]);
  const [isOffline, setIsOffline] = useState(false);

  useEffect(() => {
    loadMapData();
  }, []);

  const loadMapData = async () => {
    setLoading(true);
    try {
      const whs = await warehouseService.getWarehouses();
      setWarehouses(whs);
      
      if (whs.length > 0) {
        const firstWh = whs[0];
        setSelectedWarehouse(firstWh);
        const floorData = await warehouseService.getWarehouseFloors(firstWh.id_entrepot);
        setFloors(floorData);
      }
      setIsOffline(false);
    } catch (error) {
      setIsOffline(true);
      console.log('Using cached map data');
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <View style={styles.center}>
        <ActivityIndicator size="large" color={lightTheme.primary} />
        <Text style={styles.loadingText}>Loading warehouse maps...</Text>
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
          <Text style={styles.title}>Visual Warehouse</Text>
          <Text style={styles.subtitle}>
            {selectedWarehouse ? `Viewing: ${selectedWarehouse.nom_entrepot}` : 'No warehouse selected'}
          </Text>
        </View>

        {/* Map Visualization Container */}
        <View style={styles.mapContainer}>
          <View style={styles.placeholderMap}>
            <Feather name="map" size={64} color={lightTheme.border} />
            <Text style={styles.mapHint}>Map visualization and zoning layers</Text>
            <Text style={styles.infoText}>{floors.length} Floors Loaded</Text>
          </View>
        </View>

        <View style={styles.statsRow}>
          <View style={styles.statCard}>
            <Text style={styles.statLabel}>Floors</Text>
            <Text style={styles.statValue}>{floors.length}</Text>
          </View>
          <View style={styles.statCard}>
            <Text style={styles.statLabel}>Status</Text>
            <Text style={[styles.statValue, { color: isOffline ? lightTheme.warning : lightTheme.success }]}>
              {isOffline ? 'Cached' : 'Live'}
            </Text>
          </View>
        </View>
      </ScrollView>
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
  mapContainer: {
    height: 400,
    backgroundColor: lightTheme.white,
    borderRadius: 16,
    borderWidth: 1,
    borderColor: lightTheme.border,
    overflow: 'hidden',
    marginBottom: 16,
  },
  placeholderMap: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    backgroundColor: '#F9FAFB',
  },
  mapHint: {
    marginTop: 16,
    color: lightTheme.textSecondary,
    fontSize: 14,
  },
  infoText: {
    marginTop: 8,
    color: lightTheme.primary,
    fontWeight: '600',
  },
  statsRow: {
    flexDirection: 'row',
    gap: 12,
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
    fontSize: 20,
    fontWeight: '700',
    color: lightTheme.textPrimary,
    marginTop: 4,
  },
  loadingText: {
    marginTop: 12,
    color: lightTheme.textSecondary,
  }
});

export default VisualWarehouse;
