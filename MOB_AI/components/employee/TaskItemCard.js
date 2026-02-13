import React from 'react';
import { View, Text, TouchableOpacity, StyleSheet } from 'react-native';
import { Feather } from '@expo/vector-icons';
import { lightTheme } from '../../constants/theme';

const statusColorMap = {
  PENDING: lightTheme.warning,
  CONFIRMED: lightTheme.primary,
  COMPLETED: lightTheme.success,
  CANCELLED: lightTheme.error,
};

const formatDateTime = (value) => {
  if (!value) return 'Unknown time';
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return 'Unknown time';
  return date.toLocaleString();
};

const TaskItemCard = ({ task, onDone, loading }) => {
  const statusColor = statusColorMap[task.status] || lightTheme.textSecondary;
  const canBeCompleted = task.status !== 'COMPLETED' && task.status !== 'CANCELLED';

  return (
    <View style={styles.card}>
      <View style={styles.headerRow}>
        <Text style={styles.title}>{task.title}</Text>
        <View style={[styles.statusChip, { backgroundColor: statusColor }]}>
          <Text style={styles.statusText}>{task.status}</Text>
        </View>
      </View>

      <Text style={styles.description}>{task.description}</Text>

      <View style={styles.metaRow}>
        <View style={styles.metaItem}>
          <Feather name="calendar" size={13} color={lightTheme.textSecondary} />
          <Text style={styles.metaText}>{formatDateTime(task.createdAt)}</Text>
        </View>
        <View style={styles.metaItem}>
          <Feather name="user" size={13} color={lightTheme.textSecondary} />
          <Text style={styles.metaText}>{task.createdBy || 'Admin'}</Text>
        </View>
      </View>

      {canBeCompleted && (
        <TouchableOpacity
          style={[styles.doneButton, loading && styles.disabledButton]}
          onPress={() => onDone(task.id)}
          disabled={loading}
          activeOpacity={0.8}
        >
          <Feather name="check-circle" size={15} color={lightTheme.white} />
          <Text style={styles.doneButtonText}>{loading ? 'Saving...' : 'Mark as done'}</Text>
        </TouchableOpacity>
      )}
    </View>
  );
};

const styles = StyleSheet.create({
  card: {
    borderRadius: 14,
    borderWidth: 1,
    borderColor: lightTheme.border,
    backgroundColor: lightTheme.white,
    padding: 14,
    marginBottom: 10,
  },
  headerRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    gap: 10,
  },
  title: {
    flex: 1,
    fontSize: 16,
    fontWeight: '700',
    color: lightTheme.textPrimary,
  },
  statusChip: {
    borderRadius: 999,
    paddingHorizontal: 10,
    paddingVertical: 4,
  },
  statusText: {
    color: lightTheme.white,
    fontSize: 11,
    fontWeight: '700',
  },
  description: {
    marginTop: 8,
    color: lightTheme.textMuted,
    fontSize: 14,
    lineHeight: 20,
  },
  metaRow: {
    marginTop: 10,
    gap: 8,
  },
  metaItem: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
  },
  metaText: {
    fontSize: 12,
    color: lightTheme.textSecondary,
  },
  doneButton: {
    marginTop: 12,
    borderRadius: 10,
    backgroundColor: lightTheme.primary,
    paddingVertical: 10,
    alignItems: 'center',
    justifyContent: 'center',
    flexDirection: 'row',
    gap: 8,
  },
  disabledButton: {
    backgroundColor: lightTheme.textSecondary,
  },
  doneButtonText: {
    color: lightTheme.white,
    fontWeight: '700',
    fontSize: 14,
  },
});

export default TaskItemCard;
