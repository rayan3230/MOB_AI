import React, { useState, useEffect } from 'react';
import { View, Text, StyleSheet, ScrollView, TouchableOpacity, Dimensions, Image, ActivityIndicator, RefreshControl, Modal } from 'react-native';
import { Feather, FontAwesome, Ionicons } from '@expo/vector-icons';
import Svg, { Circle, G } from 'react-native-svg';
import TopHeader from '../../components/AdminHeader';
import Logo from '../../components/Logo';
import { warehouseService } from '../../services/warehouseService';
import { lightTheme } from '../../constants/theme';

const { width } = Dimensions.get('window');

const DashboardContent = ({ navigation, onNavigate }) => {
  const [stats, setStats] = useState(null);
  const [warehouses, setWarehouses] = useState([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [selectedWarehouseId, setSelectedWarehouseId] = useState('');
  const [warehouseFilterModalVisible, setWarehouseFilterModalVisible] = useState(false);

  const fetchStats = async (warehouseId = '') => {
    try {
      const normalizedWarehouseId = warehouseId ? String(warehouseId).trim() : '';
      const data = await warehouseService.getDashboardStats(normalizedWarehouseId || null);
      setStats(data);
    } catch (error) {
      console.error('Error fetching dashboard stats:', error);
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  };

  const fetchInitialData = async () => {
    try {
      setLoading(true);
      const whData = await warehouseService.getWarehouses();
      const safeWarehouses = Array.isArray(whData)
        ? whData
            .filter((w) => w && (w.id_entrepot || w.id))
            .map((w) => ({
              ...w,
              id_entrepot: String(w.id_entrepot || w.id).trim(),
              nom_entrepot: w.nom_entrepot || w.code_entrepot || String(w.id_entrepot || w.id),
            }))
        : [];
      setWarehouses(safeWarehouses);
      setSelectedWarehouseId('');
      await fetchStats('');
    } catch (error) {
      console.error('Error fetching dashboard initial data:', error);
      setLoading(false);
      setRefreshing(false);
    }
  };

  useEffect(() => {
    fetchInitialData();
  }, []);

  const onRefresh = () => {
    setRefreshing(true);
    fetchStats(selectedWarehouseId);
  };

  const handleWarehouseFilterChange = async (warehouseId) => {
    const normalizedWarehouseId = warehouseId ? String(warehouseId).trim() : '';
    setWarehouseFilterModalVisible(false);
    setSelectedWarehouseId(normalizedWarehouseId);
    setRefreshing(true);
    await fetchStats(normalizedWarehouseId);
  };

  const selectedWarehouseLabel = selectedWarehouseId
    ? (warehouses.find((w) => String(w.id_entrepot) === String(selectedWarehouseId))?.nom_entrepot || selectedWarehouseId)
    : 'All Warehouses';

  const productsSubtitle = selectedWarehouseId
    ? `SKUs in ${selectedWarehouseLabel}`
    : 'Unique SKUs (all warehouses)';

  const chartData = stats ? [
    { name: 'Occupied', value: stats.warehouse.occupied || 0, color: lightTheme.primary },
    { name: 'Available', value: stats.warehouse.available || 1, color: lightTheme.thirdary },
    { name: 'Blocked', value: stats.warehouse.blocked || 0, color: lightTheme.error },
  ] : [
    { name: 'Loading', value: 100, color: '#eee' }
  ];

  const total = chartData.reduce((acc, curr) => acc + curr.value, 0);

  // For the Donut Chart
  const radius = 60;
  const strokeWidth = 18;
  const circumference = 2 * Math.PI * radius;

  let cumulativeOffset = 0;

  if (loading && !refreshing) {
    return (
      <View style={[styles.container, { backgroundColor: lightTheme.white, justifyContent: 'center' }]}>
        <ActivityIndicator size="large" color={lightTheme.primary} />
      </View>
    );
  }

  return (
    <View style={styles.container}>
      <ScrollView 
        style={styles.content} 
        showsVerticalScrollIndicator={false}
        refreshControl={
          <RefreshControl refreshing={refreshing} onRefresh={onRefresh} />
        }
      >
        {/* Main Stat Card */}
        <View style={styles.filterCard}>
          <Text style={styles.filterLabel}>Dashboard Filter</Text>
          <TouchableOpacity
            style={styles.filterSelector}
            onPress={() => setWarehouseFilterModalVisible(true)}
          >
            <Text style={styles.filterSelectorText}>{selectedWarehouseLabel}</Text>
            <Feather name="chevron-down" size={18} color="#666" />
          </TouchableOpacity>
        </View>

        <View style={styles.mainCard}>
          <View>
            <Text style={styles.mainCardTitle}>
              {selectedWarehouseId ? `Warehouse: ${selectedWarehouseId}` : 'Total Warehouses'}
            </Text>
            <Text style={styles.mainCardValue}>
              {selectedWarehouseId ? (stats?.warehouse?.locations || 0) : (stats?.warehouse?.count || 0)}
            </Text>
            {selectedWarehouseId && <Text style={styles.mainCardSubtitle}>Locations managed</Text>}
          </View>
          <View style={styles.mainCardIcon}>
            <Logo width={120} height={120} colorTop="rgba(0,122,140,0.2)" colorBottom="rgba(255,221,28,0.2)" />
          </View>
        </View>

        {/* Stats Grid */}
        <View style={styles.statsGrid}>
          <View style={styles.gridRow}>
            <StatBox 
              icon="building" 
              title="Locations" 
              subtitle="Total storage slots" 
              value={stats?.warehouse?.locations || 0} 
            />
            <StatBox 
              icon="cubes" 
              title="Products" 
              subtitle={productsSubtitle}
              value={stats?.inventory?.products || 0} 
            />
          </View>
          <View style={styles.gridRow}>
            <StatBox 
              icon="users" 
              title="Staff Members" 
              subtitle="Total registered users" 
              value={stats?.users?.total || 0} 
            />
            <StatBox 
              icon="truck" 
              title="Chariots" 
              subtitle="Available trolleys" 
              value={`${stats?.chariots?.available || 0}/${stats?.chariots?.total || 0}`} 
            />
          </View>
        </View>

        {/* Quick Management Links */}
        <View style={styles.quickLinksCard}>
          <Text style={styles.quickLinksTitle}>Quick Management</Text>
          <View style={styles.quickLinksGrid}>
            <TouchableOpacity 
              style={styles.quickLinkItem} 
              activeOpacity={0.7}
              onPress={() => onNavigate && onNavigate('User_managment')}
            >
              <Feather name="users" size={20} color={lightTheme.primary} />
              <Text style={styles.quickLinkText}>Manage Users</Text>
            </TouchableOpacity>
            <TouchableOpacity 
              style={styles.quickLinkItem} 
              activeOpacity={0.7}
              onPress={() => onNavigate && onNavigate('StockingUnit_management')}
            >
              <Feather name="box" size={20} color={lightTheme.thirdary} />
              <Text style={styles.quickLinkText}>Add Product</Text>
            </TouchableOpacity>
            <TouchableOpacity 
              style={styles.quickLinkItem} 
              activeOpacity={0.7}
              onPress={() => onNavigate && onNavigate('Location_managment')}
            >
              <Feather name="map-pin" size={20} color="#F59E0B" />
              <Text style={styles.quickLinkText}>Locations</Text>
            </TouchableOpacity>
            <TouchableOpacity style={styles.quickLinkItem} activeOpacity={0.7} onPress={() => onNavigate && onNavigate('AI_Actions')}>
              <Feather name="zap" size={20} color="#8B5CF6" />
              <Text style={styles.quickLinkText}>AI Actions</Text>
            </TouchableOpacity>
          </View>
        </View>

        {/* Analytics Section */}
        <View style={styles.analyticsCard}>
          <Text style={styles.analyticsTitle}>Warehouse Occupancy</Text>
          
          <View style={styles.chartContainer}>
            <View style={styles.chartWrapper}>
                <Svg height="160" width="160" viewBox="0 0 160 160">
                <G rotation="-90" origin="80, 80">
                    {chartData.map((item, index) => {
                    const strokeDashoffset = circumference - (item.value / total) * circumference;
                    const rotation = (cumulativeOffset / total) * 360;
                    const result = (
                        <Circle
                        key={index}
                        cx="80"
                        cy="80"
                        r={radius}
                        stroke={item.color}
                        strokeWidth={strokeWidth}
                        strokeDasharray={`${circumference} ${circumference}`}
                        strokeDashoffset={strokeDashoffset}
                        rotation={rotation}
                        origin="80, 80"
                        fill="transparent"
                        />
                    );
                    cumulativeOffset += item.value;
                    return result;
                    })}
                </G>
                </Svg>
                <View style={[StyleSheet.absoluteFill, styles.chartLabel]}>
                    <Text style={styles.totalLabel}>{Math.round(stats?.warehouse?.occupancy_rate || 0)}%</Text>
                    <Text style={styles.totalValue}>Occupancy</Text>
                </View>
            </View>

            <View style={styles.legendContainer}>
              {chartData.map((item, index) => (
                <View key={index} style={styles.legendItem}>
                  <View style={[styles.legendColor, { backgroundColor: item.color }]} />
                  <Text style={styles.legendText}>{item.name}</Text>
                </View>
              ))}
            </View>
          </View>
        </View>

        {/* Tasks Section */}
        <View style={styles.tasksSection}>
          <Text style={styles.tasksTitle}>System Activity (24h)</Text>
          <View style={styles.taskCard}>
            <View style={styles.taskIcon}>
              <FontAwesome name="exchange" size={20} color={lightTheme.primary} />
            </View>
            <View style={styles.taskInfo}>
              <Text style={styles.taskName}>{stats?.activity?.total_movements_24h || 0} Movements</Text>
              <Text style={styles.taskTime}>Receptions: {stats?.activity?.receptions_24h || 0} | Pickings: {stats?.activity?.pickings_24h || 0}</Text>
            </View>
            <View style={[styles.taskBadge, { backgroundColor: '#E8F5E9' }]}>
              <Text style={[styles.taskBadgeText, { color: '#2E7D32' }]}>Live</Text>
            </View>
          </View>
        </View>
        
        <View style={{ height: 40 }} />
      </ScrollView>

      <Modal
        animationType="fade"
        transparent={true}
        visible={warehouseFilterModalVisible}
        onRequestClose={() => setWarehouseFilterModalVisible(false)}
      >
        <View style={styles.filterModalOverlay}>
          <View style={styles.filterModalContent}>
            <Text style={styles.filterModalTitle}>Select Warehouse Filter</Text>
            <ScrollView>
              <TouchableOpacity
                style={[styles.filterOption, !selectedWarehouseId && styles.filterOptionSelected]}
                onPress={() => handleWarehouseFilterChange('')}
              >
                <Text style={[styles.filterOptionText, !selectedWarehouseId && styles.filterOptionTextSelected]}>All Warehouses</Text>
              </TouchableOpacity>

              {warehouses.map((warehouse) => {
                const warehouseId = String(warehouse.id_entrepot);
                const isSelected = warehouseId === String(selectedWarehouseId);
                return (
                  <TouchableOpacity
                    key={warehouseId}
                    style={[styles.filterOption, isSelected && styles.filterOptionSelected]}
                    onPress={() => handleWarehouseFilterChange(warehouseId)}
                  >
                    <Text style={[styles.filterOptionText, isSelected && styles.filterOptionTextSelected]}>
                      {warehouse.nom_entrepot || warehouse.code_entrepot || warehouseId}
                    </Text>
                  </TouchableOpacity>
                );
              })}
            </ScrollView>

            <TouchableOpacity
              style={styles.filterCloseButton}
              onPress={() => setWarehouseFilterModalVisible(false)}
            >
              <Text style={styles.filterCloseButtonText}>Close</Text>
            </TouchableOpacity>
          </View>
        </View>
      </Modal>
    </View>
  );
};

const StatBox = ({ icon, title, subtitle, value, percentage }) => (
  <View style={styles.statBox}>
    <View style={styles.statHeader}>
      <FontAwesome name={icon} size={12} color="#888" />
      <Text style={styles.statTitle}>{title}</Text>
    </View>
    <Text style={styles.statSubtitle}>{subtitle}</Text>
    <View style={styles.statFooter}>
      <Text style={styles.statValue}>{value}</Text>
      {percentage && <Text style={styles.statPercentage}>{percentage}</Text>}
    </View>
  </View>
);

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: lightTheme.primary,
  },
  content: {
    flex: 1,
    paddingHorizontal: 20,
    backgroundColor: lightTheme.white,
  },
  filterCard: {
    marginBottom: 14,
  },
  filterLabel: {
    fontSize: 13,
    fontWeight: '600',
    color: '#666',
    marginBottom: 6,
  },
  filterSelector: {
    backgroundColor: '#f8f9fa',
    borderWidth: 1,
    borderColor: '#e9ecef',
    borderRadius: 8,
    paddingHorizontal: 12,
    height: 44,
    alignItems: 'center',
    justifyContent: 'space-between',
    flexDirection: 'row',
  },
  filterSelectorText: {
    fontSize: 15,
    color: '#333',
    flex: 1,
    marginRight: 8,
  },
  filterModalOverlay: {
    position: 'absolute',
    top: 0,
    right: 0,
    bottom: 0,
    left: 0,
    backgroundColor: 'rgba(0,0,0,0.45)',
    justifyContent: 'center',
    padding: 20,
  },
  filterModalContent: {
    backgroundColor: '#fff',
    borderRadius: 12,
    maxHeight: '70%',
    padding: 16,
  },
  filterModalTitle: {
    fontSize: 18,
    fontWeight: '700',
    color: '#333',
    marginBottom: 12,
  },
  filterOption: {
    paddingVertical: 12,
    paddingHorizontal: 10,
    borderRadius: 8,
    marginBottom: 6,
    backgroundColor: '#f8f9fa',
  },
  filterOptionSelected: {
    backgroundColor: '#E3F2FD',
  },
  filterOptionText: {
    fontSize: 15,
    color: '#333',
  },
  filterOptionTextSelected: {
    color: '#1565C0',
    fontWeight: '600',
  },
  filterCloseButton: {
    marginTop: 10,
    paddingVertical: 10,
    borderRadius: 8,
    backgroundColor: '#f1f3f5',
    alignItems: 'center',
  },
  filterCloseButtonText: {
    color: '#495057',
    fontWeight: '600',
  },
  mainCard: {
    backgroundColor: lightTheme.primary,
    borderRadius: 15,
    padding: 25,
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 20,
    overflow: 'hidden',
  },
  mainCardTitle: {
    color: '#fff',
    fontSize: 16,
    fontWeight: '500',
    marginBottom: 10,
    opacity: 0.9,
  },
  mainCardValue: {
    color: '#fff',
    fontSize: 36,
    fontWeight: 'bold',
  },
  mainCardIcon: {
    position: 'absolute',
    right: -20,
    top: -10,
    opacity: 0.8,
  },
  statsGrid: {
    marginBottom: 25,
    borderRadius: 15,
    borderWidth: 2,
    borderColor: '#00A3FF',
    borderStyle: 'dashed',
    overflow: 'hidden',
  },
  gridRow: {
    flexDirection: 'row',
  },
  statBox: {
    flex: 1,
    padding: 20,
    borderWidth: 0.5,
    borderColor: '#eee',
    backgroundColor: '#fff',
  },
  statHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 4,
  },
  statTitle: {
    fontSize: 13,
    fontWeight: '600',
    color: '#333',
    marginLeft: 8,
  },
  statSubtitle: {
    fontSize: 10,
    color: '#999',
    marginBottom: 10,
  },
  statFooter: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
  },
  statValue: {
    fontSize: 22,
    fontWeight: 'bold',
    color: '#1a1a1a',
  },
  statPercentage: {
    fontSize: 11,
    color: '#4CAF50',
    fontWeight: '600',
  },
  quickLinksCard: {
    backgroundColor: '#fff',
    borderRadius: 18,
    padding: 18,
    borderWidth: 1,
    borderColor: '#f0f0f0',
    marginBottom: 20,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.05,
    shadowRadius: 8,
    elevation: 2,
  },
  quickLinksTitle: {
    fontSize: 16,
    fontWeight: '700',
    color: '#1a1a1a',
    marginBottom: 14,
  },
  quickLinksGrid: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 10,
  },
  quickLinkItem: {
    flex: 1,
    minWidth: '47%',
    flexDirection: 'row',
    alignItems: 'center',
    gap: 10,
    paddingVertical: 12,
    paddingHorizontal: 14,
    backgroundColor: '#f8f9fa',
    borderRadius: 12,
    borderWidth: 1,
    borderColor: '#e9ecef',
  },
  quickLinkText: {
    fontSize: 13,
    fontWeight: '600',
    color: '#333',
  },
  analyticsCard: {
    backgroundColor: '#fff',
    borderRadius: 20,
    padding: 20,
    borderWidth: 1,
    borderColor: '#f5f5f5',
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.05,
    shadowRadius: 10,
    elevation: 2,
    marginBottom: 20,
  },
  analyticsTitle: {
    fontSize: 15,
    fontWeight: '600',
    color: '#333',
    marginBottom: 25,
  },
  chartContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-around',
  },
  chartWrapper: {
    width: 160,
    height: 160,
    justifyContent: 'center',
    alignItems: 'center',
  },
  chartLabel: {
    justifyContent: 'center',
    alignItems: 'center',
  },
  totalLabel: {
    fontSize: 16,
    fontWeight: 'bold',
    color: '#1a1a1a',
  },
  totalValue: {
    fontSize: 11,
    color: '#888',
    marginTop: 2,
  },
  legendContainer: {
    marginLeft: 10,
  },
  legendItem: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 18,
  },
  legendColor: {
    width: 16,
    height: 16,
    borderRadius: 8,
    marginRight: 12,
  },
  legendText: {
    fontSize: 13,
    color: '#444',
  },
  tasksSection: {
    marginTop: 10,
    marginBottom: 20,
  },
  tasksTitle: {
    fontSize: 18,
    fontWeight: 'bold',
    color: '#333',
    marginBottom: 15,
  },
  taskCard: {
    backgroundColor: '#fff',
    borderRadius: 15,
    padding: 15,
    flexDirection: 'row',
    alignItems: 'center',
    borderWidth: 1,
    borderColor: '#f0f0f0',
  },
  taskIcon: {
    width: 40,
    height: 40,
    borderRadius: 20,
    backgroundColor: '#eef4ff',
    justifyContent: 'center',
    alignItems: 'center',
    marginRight: 15,
  },
  taskInfo: {
    flex: 1,
  },
  taskName: {
    fontSize: 14,
    fontWeight: '600',
    color: '#333',
  },
  taskTime: {
    fontSize: 12,
    color: '#888',
    marginTop: 2,
  },
  taskBadge: {
    paddingHorizontal: 10,
    paddingVertical: 5,
    borderRadius: 10,
    backgroundColor: '#FFF4E5',
  },
  taskBadgeText: {
    fontSize: 10,
    color: '#FF9800',
    fontWeight: '600',
  },
});

export default DashboardContent;
