import React, { useState, useEffect } from 'react';
import { View, Text, StyleSheet, FlatList, ActivityIndicator, TouchableOpacity, Alert } from 'react-native';
import { warehouseService } from '../../../services/warehouseService';

const WarehouseManagement = () => {
  const [warehouses, setWarehouses] = useState([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);

  const fetchWarehouses = async () => {
    try {
      setLoading(true);
      const data = await warehouseService.getWarehouses();
      setWarehouses(data);
    } catch (error) {
      console.error('Error fetching warehouses:', error);
      Alert.alert('Error', 'Failed to fetch warehouse list');
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  };

  useEffect(() => {
    fetchWarehouses();
  }, []);

  const onRefresh = () => {
    setRefreshing(true);
    fetchWarehouses();
  };

  const renderWarehouseItem = ({ item }) => (
    <View style={styles.warehouseCard}>
      <View style={styles.warehouseInfo}>
        <Text style={styles.warehouseName}>{item.nom_entrepot}</Text>
        <Text style={styles.warehouseCode}>{item.code_entrepot}</Text>
        <Text style={styles.warehouseDetails}>
          {item.ville}{item.adresse ? ` - ${item.adresse}` : ''}
        </Text>
      </View>
      <View style={[styles.statusBadge, { backgroundColor: item.actif ? '#4CAF50' : '#F44336' }]}>
        <Text style={styles.statusText}>{item.actif ? 'Active' : 'Inactive'}</Text>
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
        <Text style={styles.title}>Warehouses</Text>
        <TouchableOpacity style={styles.refreshButton} onPress={fetchWarehouses}>
          <Text style={styles.refreshButtonText}>Refresh</Text>
        </TouchableOpacity>
      </View>
      
      {warehouses.length === 0 ? (
        <View style={styles.centered}>
          <Text style={styles.text}>No warehouses found</Text>
        </View>
      ) : (
        <FlatList
          data={warehouses}
          keyExtractor={(item) => item.id_entrepot}
          renderItem={renderWarehouseItem}
          contentContainerStyle={styles.listContent}
          onRefresh={onRefresh}
          refreshing={refreshing}
        />
      )}
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#f5f5f5',
    padding: 16,
  },
  header: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 20,
    marginTop: 10,
  },
  title: {
    fontSize: 24,
    fontWeight: 'bold',
    color: '#333',
  },
  refreshButton: {
    backgroundColor: '#2196F3',
    paddingHorizontal: 12,
    paddingVertical: 6,
    borderRadius: 4,
  },
  refreshButtonText: {
    color: 'white',
    fontWeight: '600',
  },
  centered: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
  },
  listContent: {
    paddingBottom: 20,
  },
  warehouseCard: {
    backgroundColor: 'white',
    borderRadius: 8,
    padding: 16,
    marginBottom: 12,
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    elevation: 2,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 1 },
    shadowOpacity: 0.2,
    shadowRadius: 1,
  },
  warehouseInfo: {
    flex: 1,
  },
  warehouseName: {
    fontSize: 18,
    fontWeight: 'bold',
    color: '#333',
    marginBottom: 2,
  },
  warehouseCode: {
    fontSize: 14,
    color: '#2196F3',
    fontWeight: '600',
    marginBottom: 4,
  },
  warehouseDetails: {
    fontSize: 14,
    color: '#666',
  },
  statusBadge: {
    paddingHorizontal: 8,
    paddingVertical: 4,
    borderRadius: 12,
  },
  statusText: {
    color: 'white',
    fontSize: 12,
    fontWeight: 'bold',
  },
  text: {
    fontSize: 16,
    color: '#666',
  },
});

export default WarehouseManagement;
