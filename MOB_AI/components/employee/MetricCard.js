import React from 'react';
import { View, Text, StyleSheet } from 'react-native';
import { Feather } from '@expo/vector-icons';
import { lightTheme } from '../../constants/theme';

const MetricCard = ({ title, value, icon = 'activity' }) => {
  return (
    <View style={styles.card}>
      <View style={styles.topRow}>
        <Feather name={icon} size={14} color={lightTheme.textSecondary} />
        <Text style={styles.title}>{title}</Text>
      </View>
      <Text style={styles.value}>{value}</Text>
    </View>
  );
};

const styles = StyleSheet.create({
  card: {
    flex: 1,
    borderRadius: 14,
    borderWidth: 1,
    borderColor: lightTheme.border,
    backgroundColor: lightTheme.white,
    padding: 12,
  },
  topRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
  },
  title: {
    color: lightTheme.textSecondary,
    fontSize: 13,
    fontWeight: '500',
  },
  value: {
    marginTop: 10,
    color: lightTheme.textPrimary,
    fontSize: 30,
    fontWeight: '700',
  },
});

export default MetricCard;
