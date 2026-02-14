import React, { useState, useEffect } from 'react';
import { 
  View, 
  Text, 
  StyleSheet, 
  FlatList, 
  TouchableOpacity, 
  Modal, 
  TextInput, 
  ScrollView, 
  Alert, 
  ActivityIndicator,
  SafeAreaView
} from 'react-native';
import { Feather } from '@expo/vector-icons';
import { lightTheme } from '../../../constants/theme.js';
import TopHeader from '../../../components/AdminHeader';
import PredictionCard from '../../../components/PredictionCard';

import ManagementModal from '../../../components/ManagementModal';

const AIActions = ({ user, onOpenDrawer }) => {
  const [predictions, setPredictions] = useState([]);
  const [loading, setLoading] = useState(true);
  const [modalVisible, setModalVisible] = useState(false);
  const [selectedPrediction, setSelectedPrediction] = useState(null);
  const [overrideValue, setOverrideValue] = useState('');
  const [justification, setJustification] = useState('');
  const [submitting, setSubmitting] = useState(false);

  // Normalize role check for flexibility (api returns user_role)
  const userRole = (user?.user_role || user?.role || '').toUpperCase();
  const canOverride = userRole === 'ADMIN' || userRole === 'ADMINISTRATOR' || userRole === 'SUPERVISOR' || userRole === 'MANAGER';

  useEffect(() => {
    fetchPredictions();
  }, []);

  const fetchPredictions = async () => {
    // Simulated fetch - predictions for the next 3 days
    setLoading(true);
    setTimeout(() => {
      const mockData = [
        {
          id: '1',
          date: 'Tomorrow, Feb 14',
          type: 'Stock Replenishment',
          predictedValue: '150 units',
          currentValue: '150 units',
          status: 'AI Predicted',
          justification: '',
          confidence: 92,
          reasoning: 'Based on 14-day moving average and upcoming promotional campaign. Historical data shows 23% increase during similar events.',
        },
        {
          id: '2',
          date: 'Feb 15, 2026',
          type: 'Production Demand',
          predictedValue: '420 units',
          currentValue: '420 units',
          status: 'AI Predicted',
          justification: '',
          confidence: 87,
          reasoning: 'Seasonal trend analysis + order backlog pattern. Peak production period detected with 15% variance.',
        },
        {
          id: '3',
          date: 'Feb 16, 2026',
          type: 'Space Allocation',
          predictedValue: 'Zone B (20% free)',
          currentValue: 'Zone B (20% free)',
          status: 'AI Predicted',
          justification: '',
          confidence: 78,
          reasoning: 'Zone B optimal due to proximity to shipping dock and current inventory turnover rate. Reduces pick time by 18%.',
        },
      ];
      setPredictions(mockData);
      setLoading(false);
    }, 800);
  };

  const handleAccept = (prediction) => {
    Alert.alert(
      'Accept Prediction',
      'Are you sure you want to accept this AI prediction as the effective value?',
      [
        { text: 'Cancel', style: 'cancel' },
        {
          text: 'Accept',
          onPress: () => {
            const updatedPredictions = predictions.map(p => {
              if (p.id === prediction.id) {
                return {
                  ...p,
                  status: 'Accepted',
                  acceptedBy: user?.nom_complet || 'Authorized User',
                  acceptDate: new Date().toLocaleString()
                };
              }
              return p;
            });
            setPredictions(updatedPredictions);
            Alert.alert('Success', 'AI prediction accepted.');
          }
        }
      ]
    );
  };

  const handleOverrideClick = (prediction) => {
    setSelectedPrediction(prediction);
    setOverrideValue(prediction.currentValue.toString());
    setJustification('');
    setModalVisible(true);
  };

  const handleSaveOverride = () => {
    if (!overrideValue.trim() || !justification.trim()) {
      Alert.alert('Missing Information', 'Please provide both the new value and a justification.');
      return;
    }

    const updatedPredictions = predictions.map(p => {
      if (p.id === selectedPrediction.id) {
        return {
          ...p,
          currentValue: overrideValue,
          status: 'Overridden',
          justification: justification,
          overriddenBy: user?.nom_complet || 'Authorized User',
          overrideDate: new Date().toLocaleString()
        };
      }
      return p;
    });

    setPredictions(updatedPredictions);
    setModalVisible(false);
    Alert.alert('Success', 'Prediction has been overridden successfully.');
  };

  const handleReset = (prediction) => {
    const updated = predictions.map(p => 
      p.id === prediction.id ? { ...p, status: 'AI Predicted', currentValue: p.predictedValue, justification: '' } : p
    );
    setPredictions(updated);
  };

  const renderPredictionItem = ({ item }) => (
    <PredictionCard 
      item={item} 
      canOverride={canOverride} 
      onAccept={handleAccept} 
      onOverride={handleOverrideClick} 
      onReset={handleReset} 
    />
  );

  return (
    <SafeAreaView style={styles.container}>
      
      <View style={styles.contentHeader}>
        <Text style={styles.title}>AI Logistics Actions</Text>
        <Text style={styles.subtitle}>Forecast and optimization for the next 3 days</Text>
      </View>

      {loading ? (
        <View style={styles.loaderContainer}>
          <ActivityIndicator size="large" color={lightTheme.primary} />
          <Text style={styles.loadingText}>Analyzing data...</Text>
        </View>
      ) : (
        <FlatList
          data={predictions}
          keyExtractor={(item) => item.id}
          renderItem={renderPredictionItem}
          contentContainerStyle={styles.listContainer}
          showsVerticalScrollIndicator={false}
          ListEmptyComponent={
            <View style={styles.emptyContainer}>
              <Feather name="database" size={50} color="#CBD5E0" />
              <Text style={styles.emptyText}>No predictions found</Text>
            </View>
          }
        />
      )}

      <ManagementModal
        visible={modalVisible}
        onClose={() => setModalVisible(false)}
        onSave={handleSaveOverride}
        title="Override Forecast"
        submitting={submitting}
        saveLabel="Confirm Changes"
      >
        <View style={styles.predictionSummary}>
          <Text style={styles.summaryLabel}>Category</Text>
          <Text style={styles.summaryValue}>{selectedPrediction?.type}</Text>
          
          <Text style={styles.summaryLabel}>Scheduled Date</Text>
          <Text style={styles.summaryValue}>{selectedPrediction?.date}</Text>

          <View style={styles.aiForecastBox}>
            <Text style={styles.aiForecastLabel}>Initial AI Prediction</Text>
            <Text style={styles.aiForecastValue}>{selectedPrediction?.predictedValue}</Text>
          </View>
        </View>

        <Text style={styles.formLabel}>New Effective Value</Text>
        <TextInput
          style={styles.textInput}
          value={overrideValue}
          onChangeText={setOverrideValue}
          placeholder="e.g. 180 units"
          placeholderTextColor="#A0AEC0"
        />

        <Text style={styles.formLabel}>Reason for Override</Text>
        <TextInput
          style={[styles.textInput, styles.textArea]}
          value={justification}
          onChangeText={setJustification}
          placeholder="Please explain why the AI prediction is being changed..."
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
  contentHeader: {
    paddingHorizontal: 25,
    paddingVertical: 20,
  },
  title: {
    fontSize: 24,
    fontWeight: '800',
    color: '#04324C',
  },
  subtitle: {
    fontSize: 14,
    color: '#718096',
    marginTop: 5,
  },
  loaderContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
  },
  loadingText: {
    marginTop: 10,
    color: '#718096',
  },
  listContainer: {
    paddingHorizontal: 20,
    paddingBottom: 30,
  },
  emptyContainer: {
    alignItems: 'center',
    marginTop: 100,
  },
  emptyText: {
    marginTop: 20,
    fontSize: 16,
    color: '#A0AEC0',
  },
  predictionSummary: {
    marginBottom: 25,
  },
  summaryLabel: {
    fontSize: 12,
    color: '#A0AEC0',
    marginBottom: 2,
  },
  summaryValue: {
    fontSize: 16,
    fontWeight: '600',
    color: '#2D3748',
    marginBottom: 12,
  },
  aiForecastBox: {
    backgroundColor: '#EBF8FF',
    padding: 15,
    borderRadius: 12,
    marginTop: 10,
  },
  aiForecastLabel: {
    fontSize: 11,
    color: '#3182CE',
    fontWeight: '700',
    textTransform: 'uppercase',
  },
  aiForecastValue: {
    fontSize: 18,
    fontWeight: '800',
    color: '#2B6CB0',
    marginTop: 5,
  },
  formLabel: {
    fontSize: 14,
    fontWeight: '700',
    color: '#4A5568',
    marginBottom: 8,
    marginTop: 10,
  },
  textInput: {
    backgroundColor: '#F7FAFC',
    borderWidth: 1,
    borderColor: '#E2E8F0',
    borderRadius: 12,
    padding: 15,
    fontSize: 16,
    color: '#2D3748',
    marginBottom: 20,
  },
  textArea: {
    height: 100,
  },
});

export default AIActions;

