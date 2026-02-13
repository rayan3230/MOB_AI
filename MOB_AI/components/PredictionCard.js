import React from 'react';
import { 
  View, 
  Text, 
  StyleSheet, 
  TouchableOpacity 
} from 'react-native';
import { Feather } from '@expo/vector-icons';
import { lightTheme } from '../constants/theme.js';

const PredictionCard = ({ item, canOverride, onAccept, onOverride, onReset }) => {
  return (
    <View style={styles.card}>
      <View style={styles.cardHeader}>
        <View style={styles.dateContainer}>
          <Feather name="calendar" size={16} color={lightTheme.primary} />
          <Text style={styles.dateText}>{item.date}</Text>
        </View>
        <View style={[
          styles.statusBadge, 
          item.status === 'Overridden' ? styles.statusBadgeOverridden : 
          item.status === 'Accepted' ? styles.statusBadgeAccepted : styles.statusBadgeAI
        ]}>
          <Text style={[
            styles.statusText, 
            item.status === 'Overridden' ? styles.statusTextOverridden : 
            item.status === 'Accepted' ? styles.statusTextAccepted : styles.statusTextAI
          ]}>
            {item.status === 'Overridden' ? 'OVERRIDDEN' : 
             item.status === 'Accepted' ? 'ACCEPTED' : 'AI PREDICTION'}
          </Text>
        </View>
      </View>

      <Text style={styles.predictionType}>{item.type}</Text>

      <View style={styles.valuesRow}>
        <View style={styles.valueItem}>
          <Text style={styles.valueLabel}>AI Forecast</Text>
          <Text style={styles.predictedValue}>{item.predictedValue}</Text>
        </View>
        
        <View style={styles.arrowContainer}>
          <Feather name="arrow-right" size={20} color="#CBD5E0" />
        </View>

        <View style={styles.valueItem}>
          <Text style={styles.valueLabel}>Effective Value</Text>
          <Text style={[
            styles.currentValue, 
            item.status === 'Overridden' ? styles.overriddenText : 
            item.status === 'Accepted' ? styles.acceptedText : null
          ]}>
            {item.currentValue}
          </Text>
        </View>
      </View>

      {item.status === 'Overridden' && (
        <View style={styles.justificationContainer}>
          <View style={styles.justificationHeader}>
            <Feather name="info" size={14} color="#718096" />
            <Text style={styles.justificationTitle}>Justification</Text>
          </View>
          <Text style={styles.justificationText}>"{item.justification}"</Text>
          <Text style={styles.overriddenInfo}>
            Overridden by {item.overriddenBy} on {item.overrideDate}
          </Text>
        </View>
      )}

      {item.status === 'Accepted' && (
        <View style={styles.acceptedInfoContainer}>
          <Feather name="check-circle" size={14} color="#38A169" />
          <Text style={styles.acceptedInfoText}>
            Accepted by {item.acceptedBy} on {item.acceptDate}
          </Text>
        </View>
      )}

      {canOverride && item.status === 'AI Predicted' && (
        <View style={styles.actionButtonsRow}>
          <TouchableOpacity 
            style={[styles.actionBtn, styles.acceptBtn]} 
            onPress={() => onAccept(item)}
          >
            <Feather name="check" size={18} color="#fff" />
            <Text style={styles.actionBtnText}>Accept</Text>
          </TouchableOpacity>

          <TouchableOpacity 
            style={[styles.actionBtn, styles.overrideBtn]} 
            onPress={() => onOverride(item)}
          >
            <Feather name="edit" size={18} color="#fff" />
            <Text style={styles.actionBtnText}>Override</Text>
          </TouchableOpacity>
        </View>
      )}

      {canOverride && item.status !== 'AI Predicted' && (
        <TouchableOpacity 
          style={styles.resetBtn} 
          onPress={() => onReset(item)}
        >
          <Feather name="refresh-cw" size={16} color="#718096" />
          <Text style={styles.resetBtnText}>Reset to AI Prediction</Text>
        </TouchableOpacity>
      )}
    </View>
  );
};

const styles = StyleSheet.create({
  card: {
    backgroundColor: '#fff',
    borderRadius: 20,
    padding: 20,
    marginBottom: 20,
    shadowColor: "#000",
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.05,
    shadowRadius: 10,
    elevation: 3,
  },
  cardHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 15,
  },
  dateContainer: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  dateText: {
    fontSize: 14,
    fontWeight: '600',
    color: '#718096',
    marginLeft: 6,
  },
  statusBadge: {
    paddingHorizontal: 10,
    paddingVertical: 4,
    borderRadius: 8,
  },
  statusBadgeAI: {
    backgroundColor: '#EBF8FF',
  },
  statusBadgeOverridden: {
    backgroundColor: '#FFF5F5',
  },
  statusBadgeAccepted: {
    backgroundColor: '#F0FFF4',
  },
  statusText: {
    fontSize: 10,
    fontWeight: '800',
  },
  statusTextAI: {
    color: '#3182CE',
  },
  statusTextOverridden: {
    color: '#E53E3E',
  },
  statusTextAccepted: {
    color: '#38A169',
  },
  predictionType: {
    fontSize: 18,
    fontWeight: '700',
    color: '#2D3748',
    marginBottom: 15,
  },
  valuesRow: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    backgroundColor: '#F8FAFC',
    padding: 15,
    borderRadius: 12,
  },
  valueItem: {
    flex: 1,
  },
  valueLabel: {
    fontSize: 11,
    color: '#A0AEC0',
    textTransform: 'uppercase',
    marginBottom: 4,
  },
  predictedValue: {
    fontSize: 15,
    fontWeight: '700',
    color: '#4A5568',
  },
  currentValue: {
    fontSize: 15,
    fontWeight: '700',
    color: '#2D3748',
  },
  overriddenText: {
    color: '#E53E3E',
  },
  acceptedText: {
    color: '#38A169',
  },
  arrowContainer: {
    paddingHorizontal: 10,
  },
  justificationContainer: {
    marginTop: 15,
    padding: 12,
    backgroundColor: '#F7FAFC',
    borderRadius: 10,
    borderLeftWidth: 3,
    borderLeftColor: '#CBD5E0',
  },
  justificationHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 5,
  },
  justificationTitle: {
    fontSize: 12,
    fontWeight: '700',
    color: '#718096',
    marginLeft: 5,
  },
  justificationText: {
    fontSize: 13,
    color: '#4A5568',
    fontStyle: 'italic',
  },
  overriddenInfo: {
    fontSize: 10,
    color: '#A0AEC0',
    marginTop: 8,
    textAlign: 'right',
  },
  acceptedInfoContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    marginTop: 15,
    padding: 10,
    backgroundColor: '#F0FFF4',
    borderRadius: 10,
  },
  acceptedInfoText: {
    fontSize: 12,
    color: '#38A169',
    fontWeight: '600',
    marginLeft: 8,
  },
  actionButtonsRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    marginTop: 20,
  },
  actionBtn: {
    flex: 1,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    paddingVertical: 12,
    borderRadius: 12,
    marginHorizontal: 5,
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.2,
    shadowRadius: 5,
    elevation: 4,
  },
  acceptBtn: {
    backgroundColor: '#38A169',
    shadowColor: '#38A169',
  },
  overrideBtn: {
    backgroundColor: '#00a3ff',
    shadowColor: '#00a3ff',
  },
  actionBtnText: {
    color: '#fff',
    fontWeight: '700',
    marginLeft: 8,
  },
  resetBtn: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    marginTop: 15,
    paddingVertical: 10,
  },
  resetBtnText: {
    fontSize: 13,
    color: '#718096',
    fontWeight: '600',
    marginLeft: 6,
  },
});

export default PredictionCard;
