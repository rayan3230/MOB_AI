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
  TextInput,
  Alert
} from 'react-native';
import { Feather } from '@expo/vector-icons';
import { lightTheme } from '../../../constants/theme.js';
import { apiCall } from '../../../services/api';
import { taskService } from '../../../services/taskService';
import ManagementModal from '../../../components/ManagementModal';
import OptionSelector from '../../../components/OptionSelector';

const ListActions = () => {
  const [actions, setActions] = useState([]);
  const [filteredActions, setFilteredActions] = useState([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');
  
  // Task Creation State
  const [modalVisible, setModalVisible] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [newTask, setNewTask] = useState({
    type: 'RECEIPT',
    reference: '',
    notes: ''
  });

  useEffect(() => {
    fetchActions();
  }, []);

  const fetchActions = async () => {
    try {
      setLoading(true);
      // We'll fetch transactions as they represent warehouse actions
      const data = await apiCall('/api/transaction-management/', 'GET');
      
      // If data is empty or fetch fails (offline), use mock/cached data logic
      if (!data || data.length === 0) {
        // ... existing mock data logic ...
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

  const handleCreateTask = async () => {
    if (!newTask.reference) {
      Alert.alert('Error', 'Reference is required');
      return;
    }

    setSubmitting(true);
    try {
      const result = await taskService.createTask(newTask);
      
      if (result?._queued) {
        Alert.alert('Offline Mode', 'Task has been queued and will be created when you are online.');
        
        // Optimistically add to list
        const localTask = {
          id_transaction: `TEMP-${Date.now()}`,
          type_transaction: newTask.type,
          cree_le: new Date().toISOString(),
          statut: 'PENDING',
          notes: newTask.notes,
          _offline: true
        };
        setActions([localTask, ...actions]);
        setFilteredActions([localTask, ...filteredActions]);
      } else {
        Alert.alert('Success', 'Task created successfully');
        fetchActions();
      }
      
      setModalVisible(false);
      setNewTask({ type: 'RECEIPT', reference: '', notes: '' });
    } catch (error) {
      Alert.alert('Error', 'Failed to create task');
      console.error(error);
    } finally {
      setSubmitting(false);
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
      (action.id_transaction && action.id_transaction.toLowerCase().includes(text.toLowerCase())) ||
      (action.type_transaction && action.type_transaction.toLowerCase().includes(text.toLowerCase())) ||
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
    <View style={[styles.card, item._offline && { borderLeftWidth: 4, borderLeftColor: '#F6AD55' }]}>
      <View style={styles.cardHeader}>
        <View style={[styles.iconContainer, { backgroundColor: getStatusColor(item.statut) + '20' }]}>
          <Feather name={getTypeIcon(item.type_transaction)} size={20} color={getStatusColor(item.statut)} />
        </View>
        <View style={styles.headerInfo}>
          <Text style={styles.actionId}>{item.id_transaction} {item._offline && '(Offline)'}</Text>
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
        <View style={styles.headerTop}>
          <View>
            <Text style={styles.screenTitle}>Activity History</Text>
            <Text style={styles.screenSubtitle}>Tracking all warehouse operations</Text>
          </View>
          <TouchableOpacity 
            style={styles.addButton}
            onPress={() => setModalVisible(true)}
          >
            <Feather name="plus" size={24} color="#FFF" />
          </TouchableOpacity>
        </View>
        
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
          <ActivityIndicator size="large" color={lightTheme.primary} />
        </View>
      ) : (
        <FlatList
          data={filteredActions}
          renderItem={renderActionItem}
          keyExtractor={(item) => item.id_transaction || String(Math.random())}
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

      {/* Task Creation Modal */}
      <ManagementModal
        visible={modalVisible}
        onClose={() => setModalVisible(false)}
        onSave={handleCreateTask}
        title="Assign New Task"
        submitting={submitting}
        saveLabel="Assign Task"
      >
        <Text style={styles.formLabel}>Transaction Type</Text>
        <OptionSelector
          options={[
            { label: 'Receipt', value: 'RECEIPT' },
            { label: 'Transfer', value: 'TRANSFER' },
            { label: 'Issue', value: 'ISSUE' },
            { label: 'Adjustment', value: 'ADJUSTMENT' },
          ]}
          selected={newTask.type}
          onSelect={(val) => setNewTask({ ...newTask, type: val })}
        />

        <Text style={styles.formLabel}>Reference / SKU</Text>
        <TextInput
          style={styles.textInput}
          value={newTask.reference}
          onChangeText={(val) => setNewTask({ ...newTask, reference: val })}
          placeholder="e.g. PO-7892 or SKU-882"
          placeholderTextColor="#A0AEC0"
        />

        <Text style={styles.formLabel}>Assignment Notes</Text>
        <TextInput
          style={[styles.textInput, styles.textArea]}
          value={newTask.notes}
          onChangeText={(val) => setNewTask({ ...newTask, notes: val })}
          placeholder="Detailed instructions for the employee..."
          placeholderTextColor="#A0AEC0"
          multiline
          numberOfLines={4}
          textAlignVertical="top"
        />
      </ManagementModal>
    </SafeAreaView>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: lightTheme.primary,
  },
  headerSection: {
    padding: 24,
    backgroundColor: '#FFF',
    borderBottomWidth: 1,
    borderBottomColor: '#F1F5F9',
  },
  headerTop: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'flex-start',
  },
  addButton: {
    backgroundColor: '#2196F3',
    width: 48,
    height: 48,
    borderRadius: 14,
    justifyContent: 'center',
    alignItems: 'center',
    elevation: 4,
    shadowColor: '#2196F3',
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.3,
    shadowRadius: 8,
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
  centerContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    paddingVertical: 100,
  },
  emptyText: {
    marginTop: 12,
    fontSize: 16,
    color: '#94A3B8',
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
    color: '#64748B',
    marginTop: 2,
  },
  statusBadge: {
    paddingHorizontal: 10,
    paddingVertical: 4,
    borderRadius: 8,
  },
  statusText: {
    fontSize: 11,
    fontWeight: '700',
  },
  cardBody: {
    backgroundColor: '#F8FAFC',
    borderRadius: 12,
    padding: 12,
    marginBottom: 12,
  },
  actionType: {
    fontSize: 14,
    fontWeight: '700',
    color: '#475569',
    marginBottom: 4,
  },
  actionNotes: {
    fontSize: 13,
    color: '#64748B',
    lineHeight: 18,
  },
  detailsButton: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    paddingVertical: 8,
  },
  detailsButtonText: {
    fontSize: 14,
    fontWeight: '600',
    color: '#2196F3',
    marginRight: 4,
  },
  formLabel: {
    fontSize: 14,
    fontWeight: '700',
    color: '#475569',
    marginTop: 16,
    marginBottom: 8,
  },
  textInput: {
    backgroundColor: '#F1F5F9',
    borderRadius: 12,
    paddingHorizontal: 16,
    paddingVertical: 12,
    fontSize: 15,
    color: '#1E293B',
  },
  textArea: {
    height: 100,
  }
});

export default ListActions;
