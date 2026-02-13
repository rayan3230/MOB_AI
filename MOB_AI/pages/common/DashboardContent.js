import React, { useState, useEffect } from 'react';
import { View, Text, StyleSheet, ScrollView, TouchableOpacity, Dimensions, Image, ActivityIndicator, RefreshControl } from 'react-native';
import { Feather, FontAwesome, Ionicons } from '@expo/vector-icons';
import AsyncStorage from '@react-native-async-storage/async-storage';
import Svg, { Circle, G } from 'react-native-svg';
import TopHeader from '../../components/AdminHeader';
import Logo from '../../components/Logo';
import { warehouseService } from '../../services/warehouseService';

const { width } = Dimensions.get('window');

const DashboardContent = ({ navigation }) => {
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [warehouseId, setWarehouseId] = useState(null);

  const fetchStats = async () => {
    try {
      const activeWhId = await AsyncStorage.getItem('activeWarehouseId');
      setWarehouseId(activeWhId);
      const data = await warehouseService.getDashboardStats(activeWhId);
      setStats(data);
    } catch (error) {
      console.error('Error fetching dashboard stats:', error);
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  };

  useEffect(() => {
    fetchStats();
  }, []);

  const onRefresh = () => {
    setRefreshing(true);
    fetchStats();
  };

  const chartData = stats ? [
    { name: 'Occupied', value: stats.warehouse.occupied || 0, color: '#0055FF' },
    { name: 'Available', value: stats.warehouse.available || 1, color: '#ADD8E6' },
    { name: 'Blocked', value: stats.warehouse.blocked || 0, color: '#FF4444' },
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
      <View style={[styles.container, { backgroundColor: '#fff', justifyContent: 'center' }]}>
        <ActivityIndicator size="large" color="#0055FF" />
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
        <View style={styles.mainCard}>
          <View>
            <Text style={styles.mainCardTitle}>
              {warehouseId ? `Warehouse: ${warehouseId}` : 'Total Warehouses'}
            </Text>
            <Text style={styles.mainCardValue}>
              {warehouseId ? (stats?.warehouse?.locations || 0) : (stats?.warehouse?.count || 0)}
            </Text>
            {warehouseId && <Text style={styles.mainCardSubtitle}>Locations managed</Text>}
          </View>
          <View style={styles.mainCardIcon}>
            <Logo width={120} height={120} color="rgba(255,255,255,0.2)" />
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
              subtitle="Unique SKUs" 
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
              <FontAwesome name="exchange" size={20} color="#0055FF" />
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
    backgroundColor: '#04324C', // Dark background behind the rounded header
  },
  content: {
    flex: 1,
    paddingHorizontal: 20,
    backgroundColor: '#fff', // White background for the actual content
  },
  mainCard: {
    backgroundColor: '#0055FF',
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
