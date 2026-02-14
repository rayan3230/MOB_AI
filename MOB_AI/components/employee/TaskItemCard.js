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

const TaskItemCard = ({ task, onDone, onStart, loading }) => {
  const statusColor = statusColorMap[task.status] || lightTheme.textSecondary;
  const canBeCompleted = task.status === 'CONFIRMED' || task.status === 'PENDING';
  const canBeStarted = task.status === 'PENDING';
  
  // Priority logic (can be from backend or calculated)
  const priority = task.priority || 'NORMAL'; // HIGH, NORMAL, LOW
  const isUrgent = priority === 'HIGH' || priority === 'URGENT';
  
  // Calculate if task is due soon (within 2 hours)
  const isDueSoon = task.dueDate && (new Date(task.dueDate).getTime() - Date.now()) < 2 * 60 * 60 * 1000;

  return (
    <View style={[
      styles.card,
      isUrgent && styles.urgentCard,
      isDueSoon && styles.dueSoonCard
    ]}>
      {(isUrgent || isDueSoon) && (
        <View style={[styles.priorityBanner, isUrgent ? styles.urgentBanner : styles.dueSoonBanner]}>
          <Feather name="alert-circle" size={12} color={lightTheme.white} />
          <Text style={styles.priorityText}>
            {isUrgent ? 'URGENT' : 'DUE SOON'}
          </Text>
        </View>
      )}
      
      <View style={styles.headerRow}>
        <Text style={styles.title}>{task.title}</Text>
        <View style={[styles.statusChip, { backgroundColor: statusColor }]}>
          <Text style={styles.statusText}>{task.status === 'CONFIRMED' ? 'IN PROGRESS' : task.status}</Text>
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

      <View style={styles.actionContainer}>
        {canBeStarted && (
          <TouchableOpacity
            style={[styles.startButton, loading && styles.disabledButton]}
            onPress={() => onStart(task.id)}
            disabled={loading}
            activeOpacity={0.8}
          >
            <Feather name="play-circle" size={15} color={lightTheme.white} />
            <Text style={styles.doneButtonText}>{loading ? '...' : 'Start'}</Text>
          </TouchableOpacity>
        )}

        {canBeCompleted && (
          <TouchableOpacity
            style={[
              styles.doneButton, 
              loading && styles.disabledButton,
              task.status === 'PENDING' && { flex: 2, backgroundColor: lightTheme.secondary }
            ]}
            onPress={() => onDone(task.id)}
            disabled={loading}
            activeOpacity={0.8}
          >
            <Feather name="check-circle" size={15} color={lightTheme.white} />
            <Text style={styles.doneButtonText}>{loading ? 'Saving...' : 'Complete'}</Text>
          </TouchableOpacity>
        )}
      </View>
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
    overflow: 'hidden',
  },
  actionContainer: {
    flexDirection: 'row',
    gap: 10,
    marginTop: 10,
  },
  startButton: {
    flex: 1,
    backgroundColor: lightTheme.primary,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    paddingVertical: 10,
    borderRadius: 10,
    gap: 6,
  },
  doneButton: {
    flex: 1,
    backgroundColor: lightTheme.success,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    paddingVertical: 10,
    borderRadius: 10,
    gap: 6,
  },
  disabledButton: {
    opacity: 0.6,
  },
  doneButtonText: {
    color: lightTheme.white,
    fontWeight: '600',
    fontSize: 14,
  },
  urgentCard: {
    borderColor: '#DC2626',
    borderWidth: 2,
  },
  dueSoonCard: {
    borderColor: '#F59E0B',
    borderWidth: 2,
  },
  priorityBanner: {
    position: 'absolute',
    top: 0,
    left: 0,
    right: 0,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    paddingVertical: 4,
    gap: 4,
    zIndex: 10,
  },
  urgentBanner: {
    backgroundColor: '#DC2626',
  },
  dueSoonBanner: {
    backgroundColor: '#F59E0B',
  },
  priorityText: {
    color: lightTheme.white,
    fontSize: 10,
    fontWeight: '800',
    letterSpacing: 0.5,
  },
  headerRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    gap: 10,
    marginTop: 20,
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
