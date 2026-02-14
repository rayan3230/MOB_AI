import React from 'react';
import { View, Text, StyleSheet } from 'react-native';

const SupervisorListActions = () => {
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
      const data = await apiCall('/api/transaction-management/', 'GET');
      
      if (!data || data.length === 0) {
        // Fallback for demo
        const mockData = [
          {
            id_transaction: 'T0842',
            type_transaction: 'RECEIPT',
            cree_le: '2025-02-13T10:30:00Z',
            statut: 'COMPLETED',
            notes: 'Reception of 500 units from Supplier A',
          }
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
            <Text style={styles.screenTitle}>Supervisor Activities</Text>
            <Text style={styles.screenSubtitle}>Manage warehouse tasks and assignments</Text>
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
            placeholder="Search activities..."
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
          placeholder="e.g. PO-7892"
          placeholderTextColor="#A0AEC0"
        />

        <Text style={styles.formLabel}>Assignment Notes</Text>
        <TextInput
          style={[styles.textInput, styles.textArea]}
          value={newTask.notes}
          onChangeText={(val) => setNewTask({ ...newTask, notes: val })}
          placeholder="Detailed instructions..."
          placeholderTextColor="#A0AEC0"
          multiline
          numberOfLines={4}
        />
      </ManagementModal>
    </SafeAreaView>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    backgroundColor: '#fff',
  },
  text: {
    fontSize: 18,
    fontWeight: '600',
  },
});

export default SupervisorListActions;
