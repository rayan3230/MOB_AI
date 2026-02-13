import React, { useState, useEffect } from 'react';
import { 
  View, 
  Text, 
  StyleSheet, 
  FlatList, 
  TouchableOpacity, 
  ActivityIndicator,
  SafeAreaView,
  RefreshControl,
  TextInput
} from 'react-native';
import { Feather } from '@expo/vector-icons';
import { lightTheme } from '../../../constants/theme.js';
import { apiCall } from '../../../services/api';

const ListActions = () => {
  const [actions, setActions] = useState([]);
  const [filteredActions, setFilteredActions] = useState([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');

  useEffect(() => {
    fetchActions();
  }, []);

  const fetchActions = async () => {
    try {
      setLoading(true);
      // We'll fetch transactions as they represent warehouse actions
      const data = await apiCall('/transactions/transactions/', 'GET');
      
      // If data is empty, use mock data for demonstration
      if (!data || data.length === 0) {
        const mockData = [
          {
            id_transaction: 'T0842',
            type_transaction: 'RECEIPT',
            cree_le: '2025-02-13T10:30:00Z',
            statut: 'COMPLETED',
            notes: 'Reception of 500 units from Supplier A',
          },
          {
            id_transaction: 'T0843',
            type_transaction: 'TRANSFER',
            cree_le: '2025-02-13T11:45:00Z',
            statut: 'PENDING',
            notes: 'Moving stock from Zone A to Zone B',
          },
          {
            id_transaction: 'T0844',
            type_transaction: 'ISSUE',
            cree_le: '2025-02-13T14:20:00Z',
            statut: 'CANCELLED',
            notes: 'Defective units return',
          },
        ];
        setActions(mockData);
        setFilteredActions(mockData);
      } else {
        setActions(data);
        setFilteredActions(data);
      }
    } catch (error) {
      console.error('Error fetching actions:', error);
    } finally {
      setLoading(false);
    }
  };

  const onRefresh = () => {
    setRefreshing(true);
    fetchActions().finally(() => setRefreshing(false));
  };

  const handleSearch = (text) => {
    setSearchQuery(text);
    if (!text) {
      setFilteredActions(actions);
      return;
    }
    const filtered = actions.filter(action => 
      action.id_transaction.toLowerCase().includes(text.toLowerCase()) ||
      action.type_transaction.toLowerCase().includes(text.toLowerCase()) ||
      (action.notes && action.notes.toLowerCase().includes(text.toLowerCase()))
    );
    setFilteredActions(filtered);
  };

  const getStatusColor = (status) => {
    switch (status) {
      case 'COMPLETED': return '#4CAF50';
      case 'PENDING': return '#FF9800';
      case 'CANCELLED': return '#F44336';
      default: return '#2196F3';
    }
  };

  const getTypeIcon = (type) => {
    switch (type) {
      case 'RECEIPT': return 'download';
      case 'TRANSFER': return 'repeat';
      case 'ISSUE': return 'upload';
      case 'ADJUSTMENT': return 'settings';
      default: return 'activity';
    }
  };

  const renderActionItem = ({ item }) => (
    <View style={styles.card}>
      <View style={styles.cardHeader}>
        <View style={[styles.iconContainer, { backgroundColor: getStatusColor(item.statut) + '20' }]}>
          <Feather name={getTypeIcon(item.type_transaction)} size={20} color={getStatusColor(item.statut)} />
        </View>
        <View style={styles.headerInfo}>
          <Text style={styles.actionId}>{item.id_transaction}</Text>
          <Text style={styles.actionDate}>{new Date(item.cree_le).toLocaleString('fr-FR')}</Text>
        </View>
        <View style={[styles.statusBadge, { backgroundColor: getStatusColor(item.statut) + '15' }]}>
          <Text style={[styles.statusText, { color: getStatusColor(item.statut) }]}>{item.statut}</Text>
        </View>
      </View>
      
      <View style={styles.cardBody}>
        <Text style={styles.actionType}>{item.type_transaction}</Text>
        <Text style={styles.actionNotes}>{item.notes || 'No description provided'}</Text>
      </View>

      <TouchableOpacity style={styles.detailsButton}>
        <Text style={styles.detailsButtonText}>View Details</Text>
        <Feather name="chevron-right" size={16} color="#2196F3" />
      </TouchableOpacity>
    </View>
  );

  return (
    <SafeAreaView style={styles.container}>
      <View style={styles.headerSection}>
        <Text style={styles.screenTitle}>Activity History</Text>
        <Text style={styles.screenSubtitle}>Tracking all warehouse operations</Text>
        
        <View style={styles.searchBar}>
          <Feather name="search" size={20} color="#94A3B8" />
          <TextInput
            style={styles.searchInput}
            placeholder="Search transactions..."
            value={searchQuery}
            onChangeText={handleSearch}
          />
        </View>
      </View>

      {loading && !refreshing ? (
        <View style={styles.centerContainer}>
          <ActivityIndicator size="large" color="#2196F3" />
        </View>
      ) : (
        <FlatList
          data={filteredActions}
          renderItem={renderActionItem}
          keyExtractor={(item) => item.id_transaction}
          contentContainerStyle={styles.listContent}
          refreshControl={
            <RefreshControl refreshing={refreshing} onRefresh={onRefresh} colors={["#2196F3"]} />
          }
          ListEmptyComponent={
            <View style={styles.centerContainer}>
              <Feather name="inbox" size={50} color="#CBD5E0" />
              <Text style={styles.emptyText}>No activities found</Text>
            </View>
          }
        />
      )}
    </SafeAreaView>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#F8FAFC',
  },
  headerSection: {
    padding: 24,
    backgroundColor: '#FFF',
    borderBottomWidth: 1,
    borderBottomColor: '#F1F5F9',
  },
  screenTitle: {
    fontSize: 28,
    fontWeight: '800',
    color: '#0F172A',
  },
  screenSubtitle: {
    fontSize: 14,
    color: '#64748B',
    marginTop: 4,
    marginBottom: 20,
  },
  searchBar: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#F1F5F9',
    borderRadius: 12,
    paddingHorizontal: 12,
    height: 48,
  },
  searchInput: {
    flex: 1,
    marginLeft: 8,
    fontSize: 16,
    color: '#1E293B',
  },
  listContent: {
    padding: 20,
    paddingBottom: 40,
  },
  card: {
    backgroundColor: '#FFF',
    borderRadius: 20,
    padding: 16,
    marginBottom: 16,
    elevation: 2,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.05,
    shadowRadius: 15,
  },
  cardHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 12,
  },
  iconContainer: {
    width: 40,
    height: 40,
    borderRadius: 12,
    justifyContent: 'center',
    alignItems: 'center',
  },
  headerInfo: {
    flex: 1,
    marginLeft: 12,
  },
  actionId: {
    fontSize: 16,
    fontWeight: '700',
    color: '#1E293B',
  },
  actionDate: {
    fontSize: 12,
    color: '#94A3B8',
    marginTop: 2,
  },
  statusBadge: {
    paddingVertical: 4,
    paddingHorizontal: 8,
    borderRadius: 8,
  },
  statusText: {
    fontSize: 11,
    fontWeight: '700',
  },
  cardBody: {
    paddingVertical: 8,
  },
  actionType: {
    fontSize: 13,
    fontWeight: '600',
    color: '#64748B',
    textTransform: 'uppercase',
    letterSpacing: 0.5,
    marginBottom: 4,
  },
  actionNotes: {
    fontSize: 15,
    color: '#334155',
    lineHeight: 22,
  },
  detailsButton: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    paddingTop: 12,
    marginTop: 12,
    borderTopWidth: 1,
    borderTopColor: '#F1F5F9',
  },
  detailsButtonText: {
    fontSize: 14,
    fontWeight: '600',
    color: '#2196F3',
    marginRight: 4,
  },
  centerContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    marginTop: 100,
  },
  emptyText: {
    marginTop: 16,
    fontSize: 16,
    color: '#94A3B8',
  }
});

export default ListActions;
