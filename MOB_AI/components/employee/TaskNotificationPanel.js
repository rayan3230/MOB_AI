import React from 'react';
import { View, Text, StyleSheet } from 'react-native';
import { lightTheme } from '../../constants/theme';

const TaskNotificationPanel = ({ notifications }) => {
  return (
    <View style={styles.panel}>
      <Text style={styles.title}>Notifications</Text>
      {notifications.length === 0 ? (
        <Text style={styles.empty}>No notifications yet.</Text>
      ) : (
        notifications.map((item) => (
          <View key={`notification-${item.id}`} style={styles.item}>
            <View style={styles.headingRow}>
              <Text style={styles.itemTitle} numberOfLines={1}>{item.title}</Text>
              <Text style={styles.time}>{new Date(item.createdAt).toLocaleTimeString()}</Text>
            </View>
            <Text style={styles.desc} numberOfLines={2}>{item.description}</Text>
          </View>
        ))
      )}
    </View>
  );
};

const styles = StyleSheet.create({
  panel: {
    borderRadius: 14,
    borderWidth: 1,
    borderColor: lightTheme.border,
    backgroundColor: lightTheme.white,
    padding: 12,
  },
  title: {
    color: lightTheme.textPrimary,
    fontSize: 15,
    fontWeight: '700',
    marginBottom: 8,
  },
  empty: {
    color: lightTheme.textSecondary,
    fontSize: 13,
  },
  item: {
    borderTopWidth: 1,
    borderTopColor: lightTheme.divider,
    paddingVertical: 8,
  },
  headingRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    gap: 10,
  },
  itemTitle: {
    flex: 1,
    color: lightTheme.textPrimary,
    fontWeight: '600',
    fontSize: 13,
  },
  time: {
    color: lightTheme.textSecondary,
    fontSize: 12,
  },
  desc: {
    marginTop: 3,
    color: lightTheme.textMuted,
    fontSize: 12,
  },
});

export default TaskNotificationPanel;
