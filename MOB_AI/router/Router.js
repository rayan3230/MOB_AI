import React, { useState, useRef } from 'react';
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
  StyleSheet
} from 'react-native';
import { Feather } from '@expo/vector-icons';

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

// Supervisor Pages
import SupervisorDashboard from '../pages/Supervisor/Dashboard';
import SupervisorAIActions from '../pages/Supervisor/AI_Actions';
import SupervisorListActions from '../pages/Supervisor/List_Actions';
import SupervisorProfile from '../pages/Supervisor/Profile';

// Employee Pages
import EmployeeDashboard from '../pages/employee/Dashboard';
import EmployeeListActions from '../pages/employee/List_Actions';
import EmployeeProfile from '../pages/employee/Profile';

// Common Pages
import ForgetPassword from '../pages/common/Forget_Password';
import SignUp from '../pages/common/SignUp';
import WelcomePage from '../pages/common/welcome_Page';

const Stack = createStackNavigator();
const Tab = createBottomTabNavigator();
const { width } = Dimensions.get('window');
const DRAWER_WIDTH = width * 0.75;

// --- EMPLOYEE VIEW (Bottom Tabs) ---
const EmployeeTabs = () => {
  return (
    <Tab.Navigator
      screenOptions={({ route }) => ({
        headerShown: false,
        tabBarIcon: ({ color, size }) => {
          let iconName;
          if (route.name === 'Dashboard') iconName = 'grid';
          else if (route.name === 'Tasks') iconName = 'list';
          else if (route.name === 'Profile') iconName = 'user';
          return <Feather name={iconName} size={size} color={color} />;
        },
        tabBarActiveTintColor: '#00a3ff',
        tabBarInactiveTintColor: 'gray',
        tabBarStyle: { height: 60, paddingBottom: 10 },
      })}
    >
      <Tab.Screen name="Dashboard" component={EmployeeDashboard} />
      <Tab.Screen name="Tasks" component={EmployeeListActions} />
      <Tab.Screen name="Profile" component={EmployeeProfile} />
    </Tab.Navigator>
  );
};

// --- ADMIN / SUPERVISOR LAYOUT (Sidebar) ---
const RoleDashboardLayout = ({ role, navigation }) => {
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
        case 'Dashboard': return <AdminDashboard />;
        case 'AI_Actions': return <AIActions />;
        case 'User_managment': return <UserManagement />;
        case 'Warhouse_management': return <WarehouseManagement />;
        case 'Location_managment': return <LocationManagement />;
        case 'Floor_managment': return <FloorManagement />;
        case 'StockingUnit_management': return <StockingUnitManagement />;
        case 'Chariot_management': return <ChariotManagement />;
        case 'Visual_Warhouse': return <VisualWarehouse />;
        case 'Profile': return <AdminProfile />;
        case 'List_Actions': return <ListActions />;
        default: return <PlaceholderScreen title={`Admin - ${activePage}`} />;
      }
    } else if (role === 'supervisor') {
      switch (activePage) {
        case 'Dashboard': return <SupervisorDashboard />;
        case 'AI_Actions': return <SupervisorAIActions />;
        case 'List_Actions': return <SupervisorListActions />;
        case 'Profile': return <SupervisorProfile />;
        case 'Floor_managment': return <FloorManagement />;
        case 'Visual_Warhouse': return <VisualWarehouse />;
        default: return <PlaceholderScreen title={`Supervisor - ${activePage}`} />;
      }
    }
    return <PlaceholderScreen title={`${role.toUpperCase()} - ${activePage}`} />;
  };

  return (
    <View style={styles.container}>
      <StatusBar barStyle="light-content" />
      
      <View style={styles.mainContent}>
        <SafeAreaView style={styles.topSection}>
            <View style={{ paddingHorizontal: 25, paddingVertical: 10 }}>
                <Text style={styles.roleLabel}>{role?.toUpperCase()}</Text>
                <Text style={styles.dashboardTitle}>{activePage}</Text>
            </View>
        </SafeAreaView>

        <TopHeader 
            onMenuPress={() => toggleDrawer(true)}
            onSettingsPress={() => console.log('Settings')}
            onNotificationPress={() => console.log('Notifications')}
        />

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
    return (
        <NavigationContainer>
            <Stack.Navigator 
                initialRouteName="Login"
                screenOptions={{
                    headerShown: false,
                    gestureEnabled: false
                }}
            >
                <Stack.Screen name="Welcome" component={WelcomePage} />
                <Stack.Screen name="Login" component={Login} />
                <Stack.Screen name="SignUp" component={SignUp} />
                <Stack.Screen name="ForgetPassword" component={ForgetPassword} />
                <Stack.Screen name="AdminHome">
                  {(props) => <RoleDashboardLayout {...props} role="admin" />}
                </Stack.Screen>
                <Stack.Screen name="SupervisorHome">
                  {(props) => <RoleDashboardLayout {...props} role="supervisor" />}
                </Stack.Screen>
                <Stack.Screen name="EmployeeHome" component={EmployeeTabs} />
            </Stack.Navigator>
        </NavigationContainer>
    );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#4d4d4d',
  },
  mainContent: {
    flex: 1,
  },
  topSection: {
    backgroundColor: '#4d4d4d',
  },
  roleLabel: {
    color: '#aaa',
    fontSize: 14,
    letterSpacing: 1,
  },
  dashboardTitle: {
    color: '#fff',
    fontSize: 26,
    fontWeight: '700',
  },
  whiteSheet: {
    flex: 1,
    backgroundColor: '#fff',
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
    backgroundColor: '#fff',
    zIndex: 100,
  }
});

export default Router;
