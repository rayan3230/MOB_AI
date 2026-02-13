import React, { useMemo, useState, useEffect, useCallback } from 'react';
import { View, Text, StyleSheet, ScrollView, TouchableOpacity, ActivityIndicator, Alert } from 'react-native';
import { Feather } from '@expo/vector-icons';
import { lightTheme } from '../../../constants/theme';
import { warehouseService } from '../../../services/warehouseService';
import { taskService } from '../../../services/taskService';
import { apiCall } from '../../../services/api';
import HeroMetricCard from '../../../components/employee/HeroMetricCard';
import MetricCard from '../../../components/employee/MetricCard';
import TaskDonutCard from '../../../components/employee/TaskDonutCard';
import TaskItemCard from '../../../components/employee/TaskItemCard';
import NotificationBell from '../../../components/employee/NotificationBell';
import TaskNotificationPanel from '../../../components/employee/TaskNotificationPanel';

const EmployeeListActions = ({ route }) => {
  const employeeName = route?.params?.user?.user_name || route?.params?.user?.username;
  const [tasks, setTasks] = useState([]);
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(true);
  const [updatingTaskId, setUpdatingTaskId] = useState(null);
  const [showNotifications, setShowNotifications] = useState(false);
  const [error, setError] = useState(null);

  const loadData = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const [statsRes, taskRes] = await Promise.allSettled([
        warehouseService.getDashboardStats(),
        taskService.getTasks(),
      ]);

      if (statsRes.status === 'fulfilled') {
        setStats(statsRes.value);
      }

      // Hardcoded tasks with priority indicators
      const dueSoonDate = new Date();
      dueSoonDate.setMinutes(dueSoonDate.getMinutes() + 90); // 1.5 hours from now
      
      const hardcodedTasks = [
        {
          id: 'TASK-001',
          title: 'Urgent: Stock Replenishment Zone A',
          description: 'Immediate replenishment needed for high-demand products in Zone A. Critical stock level reached.',
          status: 'PENDING',
          priority: 'HIGH',
          createdAt: new Date(Date.now() - 2 * 60 * 60 * 1000).toISOString(), // 2 hours ago
          createdBy: 'Manager',
        },
        {
          id: 'TASK-002',
          title: 'Pick Order #12458',
          description: 'Customer order ready for picking. Contains 15 items from multiple zones.',
          status: 'CONFIRMED',
          dueDate: dueSoonDate.toISOString(),
          createdAt: new Date(Date.now() - 1 * 60 * 60 * 1000).toISOString(), // 1 hour ago
          createdBy: 'System',
        },
        {
          id: 'TASK-003',
          title: 'Move Items to Zone B',
          description: 'Transfer 50 units of SKU-2847 from Zone C to Zone B for better accessibility.',
          status: 'PENDING',
          priority: 'NORMAL',
          createdAt: new Date(Date.now() - 3 * 60 * 60 * 1000).toISOString(), // 3 hours ago
          createdBy: 'Supervisor',
        },
        {
          id: 'TASK-004',
          title: 'Quality Check - Incoming Shipment',
          description: 'Inspect and verify incoming shipment #SH-9832. Check for damages and count accuracy.',
          status: 'PENDING',
          priority: 'NORMAL',
          createdAt: new Date(Date.now() - 30 * 60 * 1000).toISOString(), // 30 minutes ago
          createdBy: 'Admin',
        },
        {
          id: 'TASK-005',
          title: 'Organize Storage Rack R-15',
          description: 'Reorganize items in Rack R-15 to optimize space utilization and improve picking efficiency.',
          status: 'PENDING',
          priority: 'LOW',
          createdAt: new Date(Date.now() - 5 * 60 * 60 * 1000).toISOString(), // 5 hours ago
          createdBy: 'Manager',
        },
      ];

      if (taskRes.status === 'fulfilled' && taskRes.value && taskRes.value.length > 0) {
        // If API returns tasks, enhance them with priority
        const tasksWithPriority = (taskRes.value || []).map((task, index) => {
          if (index === 0) {
            return { ...task, priority: 'HIGH' };
          }
          if (index === 1) {
            return { ...task, dueDate: dueSoonDate.toISOString() };
          }
          return task;
        });
        setTasks([...hardcodedTasks, ...tasksWithPriority]);
      } else {
        // Use only hardcoded tasks
        setTasks(hardcodedTasks);
      }
      
      // Check if both failed
      if (statsRes.status === 'rejected' && taskRes.status === 'rejected') {
        setError('Unable to connect to server. Please check your internet connection.');
      }
    } catch (error) {
      console.error(error);
      setError('An unexpected error occurred. Pull down to retry.');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadData();
  }, [loadData]);

  const activeWarehouseCount = useMemo(
    () => stats?.warehouse?.count || 0,
    [stats]
  );

  const donutStats = useMemo(() => {
    return tasks.reduce(
      (acc, task) => {
        const status = (task.status || '').toUpperCase();
        if (status === 'PENDING') acc.pending += 1;
        if (status === 'CONFIRMED') acc.confirmed += 1;
        if (status === 'COMPLETED') acc.completed += 1;
        return acc;
      },
      { pending: 0, confirmed: 0, completed: 0 }
    );
  }, [tasks]);

  const visibleTasks = useMemo(() => {
    if (!employeeName) return tasks;
    return tasks.filter((task) => {
      if (!task.createdBy) return true;
      return task.createdBy.toLowerCase() !== employeeName.toLowerCase();
    });
  }, [tasks, employeeName]);

  const sortedTasks = useMemo(() => {
    return [...visibleTasks].sort((a, b) => {
      const dateA = new Date(a.createdAt).getTime();
      const dateB = new Date(b.createdAt).getTime();
      return dateB - dateA;
    });
  }, [visibleTasks]);

  const notifications = useMemo(() => {
    return sortedTasks.slice(0, 6);
  }, [sortedTasks]);

  const pendingNotifications = useMemo(
    () => visibleTasks.filter((task) => task.status === 'PENDING' || task.status === 'CONFIRMED').length,
    [visibleTasks]
  );

  const handleMarkDone = async (taskId) => {
    setUpdatingTaskId(taskId);
    try {
      await taskService.markTaskDone(taskId);
      setTasks((prev) => prev.map((task) => (task.id === taskId ? { ...task, status: 'COMPLETED' } : task)));
      Alert.alert('✅ Success', 'Task completed successfully!', [{ text: 'OK' }]);
    } catch (error) {
      console.error(error);
      const errorMsg = error?.detail || error?.message || 'Unable to update this task. Please try again.';
      Alert.alert('❌ Error', errorMsg, [
        { text: 'Cancel', style: 'cancel' },
        { text: 'Retry', onPress: () => handleMarkDone(taskId) }
      ]);
    } finally {
      setUpdatingTaskId(null);
    }
  };

  const handleReceive = () => {
    Alert.alert(
      '📦 Receive Goods',
      'Start receiving incoming inventory?',
      [
        { text: 'Cancel', style: 'cancel' },
        {
          text: 'Start',
          onPress: () => {
            Alert.alert('✅ Success', 'Receive mode activated. Scan incoming goods to add to inventory.');
          }
        }
      ]
    );
  };

  const handlePick = () => {
    Alert.alert(
      '🛍️ Pick Orders',
      'Start picking products for orders?',
      [
        { text: 'Cancel', style: 'cancel' },
        {
          text: 'Start',
          onPress: () => {
            Alert.alert('✅ Success', 'Pick mode activated. Scan items to prepare orders.');
          }
        }
      ]
    );
  };

  const handleMove = () => {
    Alert.alert(
      '📍 Move Items',
      'Start transferring items between locations?',
      [
        { text: 'Cancel', style: 'cancel' },
        {
          text: 'Start',
          onPress: () => {
            Alert.alert('✅ Success', 'Move mode activated. Scan items to transfer locations.');
          }
        }
      ]
    );
  };

  if (loading) {
    return (
      <View style={styles.loadingContainer}>
        <ActivityIndicator size="large" color={lightTheme.primary} />
      </View>
    );
  }

  return (
    <View style={styles.screen}>
      <ScrollView contentContainerStyle={styles.content} showsVerticalScrollIndicator={false}>
        <View style={styles.topRow}>
          <Text style={styles.pageTitle}>Employee Tasks</Text>
          <NotificationBell
            count={pendingNotifications}
            onPress={() => setShowNotifications((prev) => !prev)}
          />
        </View>

        {/* Network Error Banner */}
        {error && (
          <View style={styles.errorBanner}>
            <Feather name="wifi-off" size={18} color={lightTheme.error} />
            <View style={styles.errorTextContainer}>
              <Text style={styles.errorTitle}>Connection Error</Text>
              <Text style={styles.errorMessage}>{error}</Text>
            </View>
            <TouchableOpacity onPress={loadData} style={styles.retryButton}>
              <Feather name="refresh-cw" size={16} color={lightTheme.white} />
            </TouchableOpacity>
          </View>
        )}

        {showNotifications && (
          <TaskNotificationPanel notifications={notifications} />
        )}

        {/* Quick Actions - Core Warehouse Operations */}
        <View style={styles.quickActionsContainer}>
          <View style={styles.sectionHeader}>
            <View>
              <Text style={styles.sectionTitle}>Quick Actions</Text>
              <Text style={styles.sectionSubtitle}>Choose your operation</Text>
            </View>
          </View>

          <View style={styles.actionsGrid}>
            {/* Row 1 */}
            <View style={styles.actionsRow}>
              <TouchableOpacity 
                style={[styles.actionCard, styles.receiveCard]} 
                activeOpacity={0.85}
                onPress={handleReceive}
              >
                <View style={styles.actionTop}>
                  <View style={[styles.actionIconCircle, styles.receiveIcon]}>
                    <Feather name="package" size={24} color="#0055FF" />
                  </View>
                  <View style={styles.actionBadge}>
                    <Feather name="arrow-down" size={12} color="#0055FF" />
                  </View>
                </View>
                <View style={styles.actionBottom}>
                  <Text style={styles.actionTitle}>Receive</Text>
                  <Text style={styles.actionSubtitle}>Incoming goods</Text>
                </View>
              </TouchableOpacity>

              <TouchableOpacity 
                style={[styles.actionCard, styles.pickCard]} 
                activeOpacity={0.85}
                onPress={handlePick}
              >
                <View style={styles.actionTop}>
                  <View style={[styles.actionIconCircle, styles.pickIcon]}>
                    <Feather name="shopping-bag" size={24} color="#5DB86D" />
                  </View>
                  <View style={[styles.actionBadge, styles.pickBadge]}>
                    <Feather name="arrow-up" size={12} color="#5DB86D" />
                  </View>
                </View>
                <View style={styles.actionBottom}>
                  <Text style={styles.actionTitle}>Pick</Text>
                  <Text style={styles.actionSubtitle}>Prepare orders</Text>
                </View>
              </TouchableOpacity>
            </View>

            {/* Row 2 */}
            <View style={styles.actionsRow}>
              <TouchableOpacity 
                style={[styles.actionCard, styles.moveCard]} 
                activeOpacity={0.85}
                onPress={handleMove}
              >
                <View style={styles.actionTop}>
                  <View style={[styles.actionIconCircle, styles.moveIcon]}>
                    <Feather name="move" size={24} color="#FFA500" />
                  </View>
                  <View style={[styles.actionBadge, styles.moveBadge]}>
                    <Feather name="arrow-right" size={12} color="#FFA500" />
                  </View>
                </View>
                <View style={styles.actionBottom}>
                  <Text style={styles.actionTitle}>Move</Text>
                  <Text style={styles.actionSubtitle}>Transfer items</Text>
                </View>
              </TouchableOpacity>

              <TouchableOpacity style={[styles.actionCard, styles.scanCard]} activeOpacity={0.85}>
                <View style={styles.actionTop}>
                  <View style={[styles.actionIconCircle, styles.scanIcon]}>
                    <Feather name="camera" size={24} color={lightTheme.white} />
                  </View>
                  <View style={[styles.actionBadge, styles.scanBadge]}>
                    <Feather name="zap" size={12} color={lightTheme.white} />
                  </View>
                </View>
                <View style={styles.actionBottom}>
                  <Text style={[styles.actionTitle, { color: lightTheme.white }]}>Scan</Text>
                  <Text style={[styles.actionSubtitle, { color: 'rgba(255,255,255,0.9)' }]}>Barcode reader</Text>
                </View>
              </TouchableOpacity>
            </View>
          </View>
        </View>

        <HeroMetricCard title="Total Warehouses" value={stats?.warehouse?.count || 0} />

        <View style={styles.metricsRow}>
          <MetricCard title="Active Locations" value={stats?.warehouse?.locations || 0} icon="home" />
          <MetricCard title="Products" value={stats?.inventory?.products || 0} icon="box" />
        </View>

        <TaskDonutCard stats={donutStats} />

        <View style={styles.tasksHeaderRow}>
          <Text style={styles.tasksHeader}>Assigned Tasks</Text>
          <TouchableOpacity onPress={loadData} style={styles.refreshButton}>
            <Feather name="refresh-cw" size={14} color={lightTheme.primary} />
            <Text style={styles.refreshText}>Refresh</Text>
          </TouchableOpacity>
        </View>

        {sortedTasks.length === 0 ? (
          <View style={styles.emptyState}>
            <Feather name="check-circle" size={48} color={lightTheme.success} />
            <Text style={styles.emptyStateTitle}>All caught up!</Text>
            <Text style={styles.emptyStateText}>No pending tasks at the moment.</Text>
            <Text style={styles.emptyStateHint}>New tasks will appear here when assigned.</Text>
          </View>
        ) : (
          sortedTasks.map((task) => (
            <TaskItemCard
              key={task.id}
              task={task}
              onDone={handleMarkDone}
              loading={updatingTaskId === task.id}
            />
          ))
        )}
      </ScrollView>
    </View>
  );
};

const styles = StyleSheet.create({
  screen: {
    flex: 1,
    backgroundColor: lightTheme.background,
    marginTop: 34,
  },
  content: {
    paddingHorizontal: 16,
    paddingVertical: 16,
    gap: 14,
    paddingBottom: 28,
  },
  loadingContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    backgroundColor: lightTheme.background,
  },
  topRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  pageTitle: {
    fontSize: 24,
    fontWeight: '700',
    color: lightTheme.textPrimary,
  },
  metricsRow: {
    flexDirection: 'row',
    gap: 10,
  },
  tasksHeaderRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginTop: 2,
  },
  tasksHeader: {
    fontSize: 18,
    fontWeight: '700',
    color: lightTheme.textPrimary,
  },
  refreshButton: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
    paddingVertical: 6,
    paddingHorizontal: 10,
    backgroundColor: lightTheme.bgHighlight,
    borderRadius: 10,
    borderWidth: 1,
    borderColor: lightTheme.borderHighlight,
  },
  refreshText: {
    color: lightTheme.primary,
    fontSize: 12,
    fontWeight: '600',
  },
  emptyState: {
    borderWidth: 1,
    borderColor: lightTheme.border,
    borderRadius: 12,
    paddingVertical: 40,
    paddingHorizontal: 20,
    alignItems: 'center',
    backgroundColor: lightTheme.white,
    gap: 12,
  },
  emptyStateTitle: {
    fontSize: 18,
    fontWeight: '700',
    color: lightTheme.textPrimary,
    marginTop: 8,
  },
  emptyStateText: {
    color: lightTheme.textSecondary,
    fontSize: 14,
    textAlign: 'center',
  },
  emptyStateHint: {
    color: lightTheme.textLight,
    fontSize: 12,
    textAlign: 'center',
    fontStyle: 'italic',
  },
  errorBanner: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#FEE2E2',
    borderRadius: 12,
    padding: 14,
    gap: 12,
    borderLeftWidth: 4,
    borderLeftColor: lightTheme.error,
  },
  errorTextContainer: {
    flex: 1,
    gap: 2,
  },
  errorTitle: {
    fontSize: 13,
    fontWeight: '700',
    color: '#991B1B',
  },
  errorMessage: {
    fontSize: 12,
    color: '#7F1D1D',
  },
  retryButton: {
    backgroundColor: lightTheme.error,
    borderRadius: 8,
    padding: 8,
  },
  quickActionsContainer: {
    marginBottom: 6,
  },
  sectionHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'flex-start',
    marginBottom: 16,
  },
  sectionTitle: {
    fontSize: 22,
    fontWeight: '800',
    color: lightTheme.textPrimary,
    letterSpacing: -0.5,
  },
  sectionSubtitle: {
    fontSize: 13,
    fontWeight: '500',
    color: lightTheme.textSecondary,
    marginTop: 2,
  },
  actionsGrid: {
    gap: 14,
  },
  actionsRow: {
    flexDirection: 'row',
    gap: 14,
  },
  actionCard: {
    flex: 1,
    aspectRatio: 1.15,
    borderRadius: 20,
    padding: 18,
    justifyContent: 'space-between',
    shadowColor: lightTheme.black,
    shadowOffset: { width: 0, height: 6 },
    shadowOpacity: 0.15,
    shadowRadius: 12,
    elevation: 8,
    borderWidth: 1,
    borderColor: 'rgba(255, 255, 255, 0.8)',
  },
  receiveCard: {
    backgroundColor: '#E3F2FD',
  },
  pickCard: {
    backgroundColor: '#E8F5E9',
  },
  moveCard: {
    backgroundColor: '#FFF8E1',
  },
  scanCard: {
    backgroundColor: lightTheme.primary,
    borderColor: 'rgba(255, 255, 255, 0.3)',
  },
  actionTop: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'flex-start',
  },
  actionIconCircle: {
    width: 56,
    height: 56,
    borderRadius: 28,
    backgroundColor: lightTheme.white,
    justifyContent: 'center',
    alignItems: 'center',
    shadowColor: lightTheme.black,
    shadowOffset: { width: 0, height: 3 },
    shadowOpacity: 0.12,
    shadowRadius: 6,
    elevation: 4,
  },
  receiveIcon: {
    backgroundColor: '#FFFFFF',
  },
  pickIcon: {
    backgroundColor: '#FFFFFF',
  },
  moveIcon: {
    backgroundColor: '#FFFFFF',
  },
  scanIcon: {
    backgroundColor: 'rgba(255, 255, 255, 0.25)',
  },
  actionBadge: {
    width: 28,
    height: 28,
    borderRadius: 14,
    backgroundColor: 'rgba(0, 85, 255, 0.12)',
    justifyContent: 'center',
    alignItems: 'center',
  },
  pickBadge: {
    backgroundColor: 'rgba(93, 184, 109, 0.12)',
  },
  moveBadge: {
    backgroundColor: 'rgba(255, 165, 0, 0.12)',
  },
  scanBadge: {
    backgroundColor: 'rgba(255, 255, 255, 0.25)',
  },
  actionBottom: {
    gap: 2,
  },
  actionTitle: {
    fontSize: 17,
    fontWeight: '800',
    color: lightTheme.textPrimary,
    letterSpacing: -0.3,
  },
  actionSubtitle: {
    fontSize: 11,
    fontWeight: '600',
    color: lightTheme.textSecondary,
    textTransform: 'uppercase',
    letterSpacing: 0.5,
  },
});

export default EmployeeListActions;
