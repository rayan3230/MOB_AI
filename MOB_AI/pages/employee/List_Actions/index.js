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
  const [warehouses, setWarehouses] = useState([]);
  const [products, setProducts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [updatingTaskId, setUpdatingTaskId] = useState(null);
  const [showNotifications, setShowNotifications] = useState(false);

  const loadData = useCallback(async () => {
    setLoading(true);
    try {
      const [warehouseRes, productRes, taskRes] = await Promise.allSettled([
        warehouseService.getWarehouses(),
        apiCall('/api/produit/produits/', 'GET'),
        taskService.getTasks(),
      ]);

      if (warehouseRes.status === 'fulfilled' && Array.isArray(warehouseRes.value)) {
        setWarehouses(warehouseRes.value);
      }

      if (productRes.status === 'fulfilled' && Array.isArray(productRes.value)) {
        setProducts(productRes.value);
      }

      if (taskRes.status === 'fulfilled') {
        setTasks(taskRes.value || []);
      }
    } catch (error) {
      console.error(error);
      Alert.alert('Error', 'Failed to load employee dashboard data.');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadData();
  }, [loadData]);

  const activeWarehouseCount = useMemo(
    () => warehouses.filter((item) => item.actif !== false).length,
    [warehouses]
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
      Alert.alert('Success', 'Task marked as done.');
    } catch (error) {
      console.error(error);
      Alert.alert('Error', 'Unable to update this task.');
    } finally {
      setUpdatingTaskId(null);
    }
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

        {showNotifications && (
          <TaskNotificationPanel notifications={notifications} />
        )}

        <HeroMetricCard title="Number of warehouse" value={warehouses.length} />

        <View style={styles.metricsRow}>
          <MetricCard title="Active Warehouse" value={activeWarehouseCount} icon="home" />
          <MetricCard title="Products" value={products.length} icon="box" />
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
            <Text style={styles.emptyStateText}>No tasks assigned.</Text>
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
    paddingVertical: 20,
    alignItems: 'center',
    backgroundColor: lightTheme.white,
  },
  emptyStateText: {
    color: lightTheme.textSecondary,
    fontSize: 14,
  },
});

export default EmployeeListActions;
