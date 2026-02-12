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
      <Tab.Screen name="Dashboard" component={() => <PlaceholderScreen title="Employee Dashboard" />} />
      <Tab.Screen name="Tasks" component={() => <PlaceholderScreen title="Task List" />} />
      <Tab.Screen name="Profile" component={() => <PlaceholderScreen title="My Profile" />} />
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
                <Stack.Screen name="Login" component={Login} />
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
