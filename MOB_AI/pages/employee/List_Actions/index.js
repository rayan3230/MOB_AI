import React, { useMemo, useState, useEffect, useCallback } from 'react';
import { View, Text, StyleSheet, ScrollView, TouchableOpacity, ActivityIndicator, Alert, Modal, TextInput, FlatList } from 'react-native';
import { Feather } from '@expo/vector-icons';
import { lightTheme } from '../../../constants/theme';
import { warehouseService } from '../../../services/warehouseService';
import { taskService } from '../../../services/taskService';
import { offlineService } from '../../../services/offlineService';
import { productService } from '../../../services/productService';
import { aiService } from '../../../services/aiService';
import { apiCall } from '../../../services/api';
import HeroMetricCard from '../../../components/employee/HeroMetricCard';
import MetricCard from '../../../components/employee/MetricCard';
import TaskDonutCard from '../../../components/employee/TaskDonutCard';
import TaskItemCard from '../../../components/employee/TaskItemCard';
import NotificationBell from '../../../components/employee/NotificationBell';
import TaskNotificationPanel from '../../../components/employee/TaskNotificationPanel';
import WarehouseMap from '../../../components/WarehouseMap';

const EmployeeListActions = ({ route, navigation }) => {
  const employeeName = route?.params?.user?.user_name || route?.params?.user?.username;
  const [tasks, setTasks] = useState([]);
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(true);
  const [updatingTaskId, setUpdatingTaskId] = useState(null);
  const [showNotifications, setShowNotifications] = useState(false);
  const [error, setError] = useState(null);
  const [isOptimized, setIsOptimized] = useState(false);
  const [page, setPage] = useState(1);
  const [hasMore, setHasMore] = useState(true);
  const [isMoreLoading, setIsMoreLoading] = useState(false);

  // Route Optimization State
  const [routeVisible, setRouteVisible] = useState(false);
  const [optimizedRoute, setOptimizedRoute] = useState(null);
  const [loadingRoute, setLoadingRoute] = useState(false);
  const [mapData, setMapData] = useState(null);

  // Product Locator State
  const [locatorVisible, setLocatorVisible] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');
  const [searchResults, setSearchResults] = useState([]);
  const [searching, setSearching] = useState(false);

  const loadData = useCallback(async (forcedOptimized = null, loadMore = false) => {
    const useOptimization = forcedOptimized !== null ? forcedOptimized : isOptimized;
    
    if (loadMore) {
      if (!hasMore || isMoreLoading) return;
      setIsMoreLoading(true);
    } else {
      setLoading(true);
      setPage(1);
      setHasMore(true);
    }
    
    setError(null);

    // Try to sync any offline actions first
    await offlineService.syncQueue();

    const currentPage = loadMore ? page + 1 : 1;
    
    try {
      const requests = [
        useOptimization ? aiService.getOptimizedTasks() : taskService.getTasks(currentPage)
      ];
      
      if (!loadMore) {
        requests.push(warehouseService.getDashboardStats());
      }

      const results = await Promise.allSettled(requests);
      const taskRes = results[0];
      const statsRes = !loadMore ? (results.length > 1 ? results[1] : null) : null;

      if (statsRes && statsRes.status === 'fulfilled') {
        const statsData = statsRes.value;
        setStats(statsData);
        await offlineService.cacheData('employee_dashboard_stats', statsData);
      }

      if (taskRes.status === 'fulfilled') {
        const fetchedTasks = taskRes.value || [];
        
        if (fetchedTasks.length < 10 || useOptimization) {
          setHasMore(false);
        } else {
          setHasMore(true);
        }

        const processedTasks = fetchedTasks.map((task, index) => ({
          ...task,
          priority: index < 2 && useOptimization ? 'HIGH' : (task.priority || 'NORMAL'),
        }));

        if (loadMore) {
          setTasks(prev => [...prev, ...processedTasks]);
          setPage(currentPage);
        } else {
          setTasks(processedTasks);
          const cacheKey = useOptimization ? 'ai_optimized_tasks' : 'employee_dashboard_tasks';
          await offlineService.cacheData(cacheKey, processedTasks);
        }
      } 
    } catch (error) {
      console.error('Data loading error:', error);
      setError('Failed to load tasks.');
    } finally {
      setLoading(false);
      setIsMoreLoading(false);
    }
  }, [isOptimized, page, hasMore, isMoreLoading]);

  useEffect(() => {
    loadData();
    
    // Set up a background sync interval every 60 seconds (Optimized Interval)
    const syncInterval = setInterval(() => {
      offlineService.syncQueue();
    }, 60000);

    return () => clearInterval(syncInterval);
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
        if (status === 'CONFIRMED' || status === 'STARTED') acc.confirmed += 1;
        if (status === 'COMPLETED' || status === 'DONE') acc.completed += 1;
        return acc;
      },
      { pending: 0, confirmed: 0, completed: 0 }
    );
  }, [tasks]);

  const visibleTasks = useMemo(() => {
    // Show all real tasks from backend
    return tasks;
  }, [tasks]);

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

  const toggleOptimization = async () => {
    const newVal = !isOptimized;
    setIsOptimized(newVal);
    await loadData(newVal);
  };

  const handleMarkDone = async (taskId) => {
    setUpdatingTaskId(taskId);
    try {
      const response = await taskService.markTaskDone(taskId);
      
      setTasks((prev) => prev.map((task) => (task.id === taskId ? { ...task, status: 'COMPLETED' } : task)));
      
      if (response?._queued) {
        Alert.alert('📡 Offline Mode', 'You are currently offline. This task status will be updated on the server once you reconnect.', [{ text: 'OK' }]);
      } else {
        Alert.alert('✅ Success', 'Task marked as completed!', [{ text: 'OK' }]);
      }
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

  const handleStartTask = async (taskId) => {
    setUpdatingTaskId(taskId);
    try {
      const response = await taskService.startTask(taskId);
      
      setTasks((prev) => prev.map((task) => (task.id === taskId ? { ...task, status: 'CONFIRMED' } : task)));
      
      if (response?._queued) {
        Alert.alert('📡 Offline Mode', 'You are currently offline. Task started locally and will sync later.', [{ text: 'OK' }]);
      }
    } catch (error) {
      console.error(error);
      const errorMsg = error?.detail || error?.message || 'Unable to start this task.';
      Alert.alert('❌ Error', errorMsg);
    } finally {
      setUpdatingTaskId(null);
    }
  };

  const handleSearch = async (text) => {
    setSearchQuery(text);
    if (text.length < 2) {
      setSearchResults([]);
      return;
    }
    
    setSearching(true);
    try {
      const results = await productService.locateProduct(text);
      setSearchResults(results);
    } catch (err) {
      console.error('Search error:', err);
    } finally {
      setSearching(false);
    }
  };

  const handleScanQR = () => {
    navigation.navigate('ScanQR');
  };

  const handlePick = async () => {
    setLoadingRoute(true);
    setRouteVisible(true);
    
    try {
      // 1. Fetch Digital Twin map data (Floor 0)
      const mapInfo = await aiService.getDigitalTwinMap(0);
      setMapData(mapInfo);

      // 2. Mock some pick locations for the demo
      // In a real app, these would come from the task's order details
      const picks = [
        { x: 3, y: 12 },
        { x: 18, y: 5 },
        { x: 12, y: 15 },
        { x: 5, y: 2 }
      ];

      // 3. Get AI optimized route
      const result = await aiService.getAIPathOptimization(0, { x: 0, y: 0 }, picks);
      if (result.status === 'success') {
        setOptimizedRoute(result.data);
      } else {
        Alert.alert('AI Error', result.message || 'Failed to optimize route');
      }
    } catch (err) {
      console.error('Pick session error:', err);
      Alert.alert('Error', 'Unable to start optimized pick session. Please check your connection.');
    } finally {
      setLoadingRoute(false);
    }
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

  const renderHeader = () => (
    <View style={styles.headerContainer}>
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
          <TouchableOpacity onPress={() => loadData()} style={styles.retryButton}>
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
              style={[styles.actionCard, styles.scannerCard]} 
              activeOpacity={0.85}
              onPress={handleScanQR}
            >
              <View style={styles.actionTop}>
                <View style={[styles.actionIconCircle, styles.scannerIcon]}>
                  <Feather name="maximize" size={24} color="#6366F1" />
                </View>
                <View style={[styles.actionBadge, styles.scannerBadge]}>
                  <Feather name="qr-code" size={12} color="#6366F1" />
                </View>
              </View>
              <View style={styles.actionBottom}>
                <Text style={styles.actionTitle}>Scan QR</Text>
                <Text style={styles.actionSubtitle}>Barcode Scanner</Text>
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

            <TouchableOpacity 
              style={[styles.actionCard, styles.scanCard]} 
              activeOpacity={0.85}
              onPress={() => setLocatorVisible(true)}
            >
              <View style={styles.actionTop}>
                <View style={[styles.actionIconCircle, styles.scanIcon]}>
                  <Feather name="search" size={24} color={lightTheme.white} />
                </View>
                <View style={[styles.actionBadge, styles.scanBadge]}>
                  <Feather name="map-pin" size={12} color={lightTheme.white} />
                </View>
              </View>
              <View style={styles.actionBottom}>
                <Text style={[styles.actionTitle, { color: lightTheme.white }]}>Locate</Text>
                <Text style={[styles.actionSubtitle, { color: 'rgba(255,255,255,0.9)' }]}>Find items</Text>
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
        <View style={styles.headerActions}>
          <TouchableOpacity 
            onPress={toggleOptimization} 
            style={[
              styles.optimizeToggle, 
              isOptimized && styles.activeOptimize
            ]}
          >
            <Feather name="zap" size={12} color={isOptimized ? '#FFF' : lightTheme.primary} />
            <Text style={[styles.optimizeText, isOptimized && styles.activeOptimizeText]}>
              {isOptimized ? 'AI Optimized' : 'Optimize'}
            </Text>
          </TouchableOpacity>

          <TouchableOpacity onPress={() => loadData()} style={styles.refreshButton}>
            <Feather name="refresh-cw" size={14} color={lightTheme.primary} />
            <Text style={styles.refreshText}>Refresh</Text>
          </TouchableOpacity>
        </View>
      </View>
    </View>
  );

  if (loading && page === 1) {
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
                style={[styles.actionCard, styles.scannerCard]} 
                activeOpacity={0.85}
                onPress={handleScanQR}
              >
                <View style={styles.actionTop}>
                  <View style={[styles.actionIconCircle, styles.scannerIcon]}>
                    <Feather name="maximize" size={24} color="#6366F1" />
                  </View>
                  <View style={[styles.actionBadge, styles.scannerBadge]}>
                    <Feather name="qr-code" size={12} color="#6366F1" />
                  </View>
                </View>
                <View style={styles.actionBottom}>
                  <Text style={styles.actionTitle}>Scan QR</Text>
                  <Text style={styles.actionSubtitle}>Barcode Scanner</Text>
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

              <TouchableOpacity 
                style={[styles.actionCard, styles.scanCard]} 
                activeOpacity={0.85}
                onPress={() => setLocatorVisible(true)}
              >
                <View style={styles.actionTop}>
                  <View style={[styles.actionIconCircle, styles.scanIcon]}>
                    <Feather name="search" size={24} color={lightTheme.white} />
                  </View>
                  <View style={[styles.actionBadge, styles.scanBadge]}>
                    <Feather name="map-pin" size={12} color={lightTheme.white} />
                  </View>
                </View>
                <View style={styles.actionBottom}>
                  <Text style={[styles.actionTitle, { color: lightTheme.white }]}>Locate</Text>
                  <Text style={[styles.actionSubtitle, { color: 'rgba(255,255,255,0.9)' }]}>Find items</Text>
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
          <View style={styles.headerActions}>
            <TouchableOpacity 
              onPress={toggleOptimization} 
              style={[
                styles.optimizeToggle, 
                isOptimized && styles.activeOptimize
              ]}
            >
              <Feather name="zap" size={12} color={isOptimized ? '#FFF' : lightTheme.primary} />
              <Text style={[styles.optimizeText, isOptimized && styles.activeOptimizeText]}>
                {isOptimized ? 'AI Optimized' : 'Optimize'}
              </Text>
            </TouchableOpacity>

            <TouchableOpacity onPress={() => loadData()} style={styles.refreshButton}>
              <Feather name="refresh-cw" size={14} color={lightTheme.primary} />
              <Text style={styles.refreshText}>Refresh</Text>
            </TouchableOpacity>
          </View>
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
              onStart={handleStartTask}
              onViewMap={() => handlePick(task)}
              loading={updatingTaskId === task.id}
            />
          ))
        )}
      </ScrollView>

      {/* Route Optimization Modal */}
      <Modal
        visible={routeVisible}
        animationType="slide"
        transparent={true}
        onRequestClose={() => setRouteVisible(false)}
      >
        <View style={styles.modalOverlay}>
          <View style={[styles.modalContent, { height: '85%' }]}>
            <View style={styles.modalHeader}>
              <View>
                <Text style={styles.modalTitle}>AI Optimized Route</Text>
                <Text style={styles.modalSubtitle}>Picking Sequence & Path</Text>
              </View>
              <TouchableOpacity onPress={() => setRouteVisible(false)}>
                <Feather name="x" size={24} color={lightTheme.textPrimary} />
              </TouchableOpacity>
            </View>

            <View style={styles.mapContainer}>
              {loadingRoute ? (
                <View style={styles.centerFixed}>
                  <ActivityIndicator size="large" color={lightTheme.primary} />
                  <Text style={styles.loadingText}>Calculating optimal path...</Text>
                </View>
              ) : optimizedRoute && mapData ? (
                <>
                  <WarehouseMap 
                    mapData={mapData}
                    pathData={optimizedRoute}
                    width={350}
                    height={400}
                  />
                  <View style={styles.routeLegend}>
                    <View style={styles.legendItem}>
                      <View style={[styles.legendDot, { backgroundColor: '#3B82F6' }]} />
                      <Text style={styles.legendText}>Picking Point</Text>
                    </View>
                    <View style={styles.legendItem}>
                      <View style={[styles.legendLine, { backgroundColor: '#10B981' }]} />
                      <Text style={styles.legendText}>Optimized Path</Text>
                    </View>
                  </View>
                  
                  <View style={styles.statsSummary}>
                    <View style={styles.statBox}>
                      <Text style={styles.statVal}>{optimizedRoute.total_distance?.toFixed(1)}m</Text>
                      <Text style={styles.statLab}>Distance</Text>
                    </View>
                    <View style={styles.statBox}>
                      <Text style={styles.statVal}>{optimizedRoute.route_sequence?.length - 1}</Text>
                      <Text style={styles.statLab}>Picks</Text>
                    </View>
                    <View style={styles.statBox}>
                      <Text style={[styles.statVal, { color: lightTheme.success }]}>~{Math.ceil(optimizedRoute.total_distance * 0.1)}m</Text>
                      <Text style={styles.statLab}>Time Est.</Text>
                    </View>
                  </View>
                </>
              ) : (
                <View style={styles.centerFixed}>
                  <Feather name="alert-triangle" size={40} color={lightTheme.warning} />
                  <Text style={styles.errorText}>Unavailable to load route map</Text>
                </View>
              )}
            </View>

            <TouchableOpacity 
              style={styles.confirmPickButton}
              onPress={() => setRouteVisible(false)}
            >
              <Text style={styles.confirmPickText}>Start Picking Session</Text>
              <Feather name="arrow-right" size={18} color={lightTheme.white} />
            </TouchableOpacity>
          </View>
        </View>
      </Modal>

      {/* Product Locator Modal */}
      <Modal
        visible={locatorVisible}
        animationType="slide"
        transparent={true}
        onRequestClose={() => setLocatorVisible(false)}
      >
        <View style={styles.modalOverlay}>
          <View style={styles.modalContent}>
            <View style={styles.modalHeader}>
              <Text style={styles.modalTitle}>Product Locator</Text>
              <TouchableOpacity onPress={() => setLocatorVisible(false)}>
                <Feather name="x" size={24} color={lightTheme.textPrimary} />
              </TouchableOpacity>
            </View>

            <View style={styles.searchBarContainer}>
              <Feather name="search" size={20} color={lightTheme.textSecondary} style={styles.searchIcon} />
              <TextInput
                style={styles.searchInput}
                placeholder="Search by SKU or Name..."
                value={searchQuery}
                onChangeText={handleSearch}
                autoFocus
              />
            </View>

            {searching ? (
              <ActivityIndicator style={{ marginTop: 20 }} color={lightTheme.primary} />
            ) : (
              <FlatList
                data={searchResults}
                keyExtractor={(item) => item.id}
                contentContainerStyle={{ paddingBottom: 20 }}
                ListEmptyComponent={
                  <View style={styles.emptySearch}>
                    <Text style={styles.emptySearchText}>
                      {searchQuery.length < 2 ? 'Type at least 2 characters' : 'No products found'}
                    </Text>
                    {searchQuery.length >= 2 && <Text style={styles.offlineNote}>Showing results from local cache if offline</Text>}
                  </View>
                }
                renderItem={({ item }) => (
                  <View style={styles.resultItem}>
                    <View style={styles.resultInfo}>
                      <Text style={styles.resultName}>{item.name}</Text>
                      <Text style={styles.resultSku}>{item.sku} • {item.category}</Text>
                    </View>
                    <View style={styles.resultLocation}>
                      <Feather name="map-pin" size={14} color={lightTheme.primary} />
                      <Text style={styles.locationText}>{item.location}</Text>
                      <Text style={styles.warehouseText}>{item.warehouse}</Text>
                    </View>
                  </View>
                )}
              />
            )}
          </View>
        </View>
      </Modal>
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
  // Modal & Search Styles
  modalOverlay: {
    flex: 1,
    backgroundColor: 'rgba(0,0,0,0.5)',
    justifyContent: 'flex-end',
  },
  modalContent: {
    backgroundColor: lightTheme.white,
    borderTopLeftRadius: 24,
    borderTopRightRadius: 24,
    height: '80%',
    padding: 20,
  },
  modalHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 20,
  },
  modalTitle: {
    fontSize: 20,
    fontWeight: '700',
    color: lightTheme.textPrimary,
  },
  searchBarContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#F3F4F6',
    borderRadius: 12,
    paddingHorizontal: 12,
    marginBottom: 16,
  },
  searchIcon: {
    marginRight: 8,
  },
  searchInput: {
    flex: 1,
    height: 44,
    fontSize: 16,
    color: lightTheme.textPrimary,
  },
  resultItem: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    paddingVertical: 12,
    borderBottomWidth: 1,
    borderBottomColor: lightTheme.border,
  },
  resultInfo: {
    flex: 1,
    marginRight: 8,
  },
  resultName: {
    fontSize: 16,
    fontWeight: '600',
    color: lightTheme.textPrimary,
  },
  resultSku: {
    fontSize: 13,
    color: lightTheme.textSecondary,
    marginTop: 2,
  },
  resultLocation: {
    alignItems: 'flex-end',
  },
  locationText: {
    fontSize: 16,
    fontWeight: '700',
    color: lightTheme.primary,
  },
  warehouseText: {
    fontSize: 11,
    color: lightTheme.textSecondary,
    marginTop: 2,
  },
  emptySearch: {
    alignItems: 'center',
    marginTop: 40,
  },
  emptySearchText: {
    color: lightTheme.textSecondary,
    fontSize: 16,
  },
  offlineNote: {
    color: lightTheme.primary,
    fontSize: 12,
    marginTop: 8,
    fontStyle: 'italic',
  },
  headerActions: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
  },
  optimizeToggle: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#EBF5FF',
    paddingHorizontal: 8,
    paddingVertical: 4,
    borderRadius: 8,
    borderWidth: 1,
    borderColor: '#BFDBFE',
    gap: 4,
  },
  activeOptimize: {
    backgroundColor: lightTheme.primary,
    borderColor: lightTheme.primary,
  },
  optimizeText: {
    fontSize: 12,
    fontWeight: '600',
    color: lightTheme.primary,
  },
  activeOptimizeText: {
    color: '#FFF',
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
  scannerCard: {
    backgroundColor: '#EEF2FF',
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
  scannerIcon: {
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
  scannerBadge: {
    backgroundColor: 'rgba(99, 102, 241, 0.12)',
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
  modalSubtitle: {
    fontSize: 12,
    color: lightTheme.textSecondary,
    marginTop: 2,
  },
  mapContainer: {
    flex: 1,
    backgroundColor: '#F9FAFB',
    borderRadius: 16,
    overflow: 'hidden',
    borderWidth: 1,
    borderColor: lightTheme.border,
    justifyContent: 'center',
    alignItems: 'center',
    marginVertical: 10,
    minHeight: 420,
  },
  centerFixed: {
    justifyContent: 'center',
    alignItems: 'center',
    gap: 12,
  },
  loadingText: {
    color: lightTheme.textSecondary,
    fontSize: 14,
    fontWeight: '500',
  },
  errorText: {
    color: lightTheme.textSecondary,
    fontSize: 14,
    marginTop: 8,
  },
  routeLegend: {
    flexDirection: 'row',
    justifyContent: 'center',
    gap: 20,
    marginTop: 10,
    paddingVertical: 10,
    borderTopWidth: 1,
    borderTopColor: '#F3F4F6',
    width: '100%',
  },
  legendItem: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
  },
  legendDot: {
    width: 8,
    height: 8,
    borderRadius: 4,
  },
  legendLine: {
    width: 20,
    height: 3,
    borderRadius: 2,
  },
  legendText: {
    fontSize: 11,
    color: lightTheme.textSecondary,
    fontWeight: '600',
  },
  statsSummary: {
    flexDirection: 'row',
    justifyContent: 'space-around',
    width: '100%',
    paddingVertical: 15,
    backgroundColor: '#F8FAFC',
    borderBottomLeftRadius: 16,
    borderBottomRightRadius: 16,
  },
  statBox: {
    alignItems: 'center',
  },
  statVal: {
    fontSize: 16,
    fontWeight: '800',
    color: lightTheme.textPrimary,
  },
  statLab: {
    fontSize: 11,
    color: lightTheme.textSecondary,
    textTransform: 'uppercase',
    marginTop: 2,
  },
  confirmPickButton: {
    backgroundColor: lightTheme.primary,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    paddingVertical: 14,
    borderRadius: 12,
    gap: 10,
    marginTop: 5,
  },
  confirmPickText: {
    color: lightTheme.white,
    fontSize: 16,
    fontWeight: '700',
  },
});

export default EmployeeListActions;
