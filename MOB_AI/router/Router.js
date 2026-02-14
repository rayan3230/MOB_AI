import React, { useState, useRef, useEffect } from 'react';
import { createStackNavigator } from '@react-navigation/stack';
import { createBottomTabNavigator } from '@react-navigation/bottom-tabs';
import { NavigationContainer } from '@react-navigation/native';
import { 
  View, 
  Text, 
  SafeAreaView, 
  StatusBar, 
  Dimensions, 
  Animated, 
  TouchableOpacity,
  TouchableWithoutFeedback,
  StyleSheet,
  ActivityIndicator
} from 'react-native';
import { lightTheme } from '../constants/theme.js';
import { authService } from '../services/authService';

// Import Components
import Sidebar from '../components/Sidebar';
import TopHeader from '../components/AdminHeader';
import Login from '../pages/common/Login/login';
import PlaceholderScreen from '../pages/common/PlaceholderScreen';

// Admin Pages
import AdminDashboard from '../pages/Admin/Dashboard';
import AIActions from '../pages/Admin/AI_Actions';
import ChariotManagement from '../pages/Admin/Chariot_management';
import FloorManagement from '../pages/Admin/Floor_managment';
import ListActions from '../pages/Admin/List_Actions';
import LocationManagement from '../pages/Admin/Location_managment';
import AdminProfile from '../pages/Admin/Profile';
import StockingUnitManagement from '../pages/Admin/StockingUnit_management';
import UserManagement from '../pages/Admin/User_managment';
import VisualWarehouse from '../pages/Admin/Visual_Warhouse';
import WarehouseManagement from '../pages/Admin/Warhouse_management';
import VrackManagement from '../pages/Admin/Vrack_management';

// Supervisor Pages
import SupervisorDashboard from '../pages/Supervisor/Dashboard';
import SupervisorAIActions from '../pages/Supervisor/AI_Actions';
import SupervisorListActions from '../pages/Supervisor/List_Actions';
import SupervisorProfile from '../pages/Supervisor/Profile';

// Employee Pages
import EmployeeListActions from '../pages/employee/List_Actions';
import EmployeeProfile from '../pages/employee/Profile';
import EmployeeNavbar from '../components/EmployeeNavbar';

// Common Pages
import Intro from '../pages/common/Intro/Intro';
import ForgetPassword from '../pages/common/Forget_Password';
import WelcomePage from '../pages/common/welcome_Page';
import Notifications from '../pages/common/Notifications';
import Settings from '../pages/common/Settings';

const Stack = createStackNavigator();
const Tab = createBottomTabNavigator();
const { width } = Dimensions.get('window');
const DRAWER_WIDTH = width * 0.75;

// --- EMPLOYEE VIEW (Bottom Tabs) ---
const EmployeeTabs = ({ route }) => {
  const user = route.params?.user;
  return (
    <Tab.Navigator
      tabBar={(props) => <EmployeeNavbar {...props} />}
      screenOptions={{
        headerShown: false,
      }}
    >
      <Tab.Screen name="Tasks" component={EmployeeListActions} initialParams={{ user }} />
      <Tab.Screen name="Profile" component={EmployeeProfile} initialParams={{ user }} />
    </Tab.Navigator>
  );
};

// --- ADMIN / SUPERVISOR LAYOUT (Sidebar) ---
const RoleDashboardLayout = ({ role, navigation, route }) => {
  const user = route.params?.user;
  const [isOpen, setIsOpen] = useState(false);
  const [activePage, setActivePage] = useState('Dashboard');
  const slideAnim = useRef(new Animated.Value(-DRAWER_WIDTH)).current;
  const overlayOpacity = useRef(new Animated.Value(0)).current;

  const toggleDrawer = (open) => {
    if (open) {
      setIsOpen(true);
      Animated.parallel([
        Animated.timing(slideAnim, {
          toValue: 0,
          duration: 300,
          useNativeDriver: true,
        }),
        Animated.timing(overlayOpacity, {
          toValue: 1,
          duration: 300,
          useNativeDriver: true,
        })
      ]).start();
    } else {
      Animated.parallel([
        Animated.timing(slideAnim, {
          toValue: -DRAWER_WIDTH,
          duration: 250,
          useNativeDriver: true,
        }),
        Animated.timing(overlayOpacity, {
          toValue: 0,
          duration: 250,
          useNativeDriver: true,
        })
      ]).start(() => setIsOpen(false));
    }
  };

  const renderContent = () => {
    if (role === 'admin') {
      switch (activePage) {
        case 'Dashboard': return <AdminDashboard user={user} onOpenDrawer={() => toggleDrawer(true)} onNavigate={(page) => setActivePage(page)} />;
        case 'AI_Actions': return <AIActions user={user} onOpenDrawer={() => toggleDrawer(true)} />;
        case 'User_managment': return <UserManagement user={user} onOpenDrawer={() => toggleDrawer(true)} />;
        case 'Warhouse_management': return <WarehouseManagement user={user} onOpenDrawer={() => toggleDrawer(true)} />;
        case 'Location_managment': return <LocationManagement user={user} onOpenDrawer={() => toggleDrawer(true)} />;
        case 'Floor_managment': return <FloorManagement user={user} onOpenDrawer={() => toggleDrawer(true)} />;
        case 'StockingUnit_management': return <StockingUnitManagement user={user} onOpenDrawer={() => toggleDrawer(true)} />;
        case 'Vrack_management': return <VrackManagement user={user} onOpenDrawer={() => toggleDrawer(true)} />;
        case 'Chariot_management': return <ChariotManagement user={user} onOpenDrawer={() => toggleDrawer(true)} />;
        case 'Visual_Warhouse': return <VisualWarehouse user={user} onOpenDrawer={() => toggleDrawer(true)} />;
        case 'Profile': return <AdminProfile user={user} onOpenDrawer={() => toggleDrawer(true)} />;
        case 'List_Actions': return <ListActions user={user} onOpenDrawer={() => toggleDrawer(true)} />;
        case 'Notifications': return <Notifications />;
        case 'Settings': return <Settings />;
        default: return <PlaceholderScreen title={`Admin - ${activePage}`} />;
      }
    } else if (role === 'supervisor') {
      switch (activePage) {
        case 'Dashboard': return <SupervisorDashboard user={user} onOpenDrawer={() => toggleDrawer(true)} onNavigate={(page) => setActivePage(page)} />;
        case 'AI_Actions': return <SupervisorAIActions user={user} onOpenDrawer={() => toggleDrawer(true)} />;
        case 'List_Actions': return <SupervisorListActions user={user} onOpenDrawer={() => toggleDrawer(true)} />;
        case 'Profile': return <SupervisorProfile user={user} onOpenDrawer={() => toggleDrawer(true)} />;
        case 'Floor_managment': return <FloorManagement user={user} onOpenDrawer={() => toggleDrawer(true)} />;
        case 'Visual_Warhouse': return <VisualWarehouse user={user} onOpenDrawer={() => toggleDrawer(true)} />;
        case 'Notifications': return <Notifications />;
        case 'Settings': return <Settings />;
        default: return <PlaceholderScreen title={`Supervisor - ${activePage}`} />;
      }
    }
    return <PlaceholderScreen title={`${role.toUpperCase()} - ${activePage}`} />;
  };

  return (
    <View style={styles.container}>
      <StatusBar barStyle="light-content" backgroundColor={lightTheme.primary} />
      
      <View style={styles.mainContent}>
        <SafeAreaView style={styles.topSection}>
            <View style={{ paddingHorizontal: 25, paddingVertical: 10 }}>
                <Text style={styles.roleLabel}>{role?.toUpperCase()}</Text>
                <Text style={styles.dashboardTitle}>{activePage.replace(/_/g, ' ')}</Text>
            </View>
        </SafeAreaView>

        {activePage !== 'Profile' && (
          <TopHeader 
              onMenuPress={() => toggleDrawer(true)}
              onSettingsPress={() => setActivePage('Settings')}
              onNotificationPress={() => setActivePage('Notifications')}
          />
        )}

        <View style={styles.whiteSheet}>
            {renderContent()}
        </View>
      </View>

      {isOpen && (
        <TouchableWithoutFeedback onPress={() => toggleDrawer(false)}>
          <Animated.View style={[styles.overlay, { opacity: overlayOpacity }]} />
        </TouchableWithoutFeedback>
      )}

      <Animated.View style={[
        styles.drawer, 
        { transform: [{ translateX: slideAnim }] }
      ]}>
        <Sidebar 
          role={role} 
          user={user}
          activePage={activePage}
          onClose={() => toggleDrawer(false)}
          onNavigate={(page) => {
            if (page === 'Logout') {
              navigation.replace('Login');
            } else {
              setActivePage(page);
              toggleDrawer(false);
            }
          }}
        />
      </Animated.View>
    </View>
  );
};

const Router = () => {
    const [isLoading, setIsLoading] = useState(true);
    const [initialRoute, setInitialRoute] = useState('Intro');
    const [user, setUser] = useState(null);

    useEffect(() => {
        const checkUser = async () => {
            try {
                const storedUser = await authService.getUser();
                if (storedUser) {
                    setUser(storedUser);
                    const role = (storedUser.user_role || '').toLowerCase();
                    if (role === 'admin' || role === 'administrator') {
                        setInitialRoute('AdminHome');
                    } else if (role === 'manager' || role === 'supervisor') {
                        setInitialRoute('SupervisorHome');
                    } else if (role === 'employee') {
                        setInitialRoute('EmployeeHome');
                    }
                }
            } catch (e) {
                console.error(e);
            } finally {
                setIsLoading(false);
            }
        };
        checkUser();
    }, []);

    if (isLoading) {
        return (
            <View style={{ flex: 1, justifyContent: 'center', alignItems: 'center', backgroundColor: lightTheme.primary }}>
                <ActivityIndicator size="large" color={lightTheme.secondary} />
            </View>
        );
    }

    return (
        <NavigationContainer>
            <Stack.Navigator 
                initialRouteName={initialRoute}
                screenOptions={{
                    headerShown: false,
                    gestureEnabled: false
                }}
            >
                <Stack.Screen name="Intro" component={Intro} />
                <Stack.Screen name="Welcome" component={WelcomePage} />
                <Stack.Screen name="Login" component={Login} />
                <Stack.Screen name="ForgetPassword" component={ForgetPassword} />
                <Stack.Screen name="AdminHome" initialParams={user && initialRoute === 'AdminHome' ? { user } : undefined}>
                  {(props) => <RoleDashboardLayout {...props} role="admin" />}
                </Stack.Screen>
                <Stack.Screen name="SupervisorHome" initialParams={user && initialRoute === 'SupervisorHome' ? { user } : undefined}>
                  {(props) => <RoleDashboardLayout {...props} role="supervisor" />}
                </Stack.Screen>
                <Stack.Screen name="EmployeeHome" component={EmployeeTabs} initialParams={user && initialRoute === 'EmployeeHome' ? { user } : undefined} />
            </Stack.Navigator>
        </NavigationContainer>
    );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: lightTheme.primary,
  },
  mainContent: {
    flex: 1,
    backgroundColor: lightTheme.primary,
  },
  topSection: {
    backgroundColor: "#007A8C",
  },
  roleLabel: {
    color: "#fff",
    fontSize: 14,
    letterSpacing: 1,
  },
  dashboardTitle: {
    color: "#fff",
    fontSize: 26,
    fontWeight: '700',
  },
  whiteSheet: {
    flex: 1,
    backgroundColor: lightTheme.primary,
    paddingTop: 0,
  },
  overlay: {
    ...StyleSheet.absoluteFillObject,
    backgroundColor: 'rgba(0,0,0,0.6)',
    zIndex: 99,
  },
  drawer: {
    position: 'absolute',
    left: 0,
    top: 0,
    bottom: 0,
    width: DRAWER_WIDTH,
    backgroundColor: lightTheme.primary,
    zIndex: 100,
  }
});

export default Router;
