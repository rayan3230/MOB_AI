import React from 'react';
import { View, StyleSheet, TouchableOpacity, Dimensions, Animated } from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { lightTheme } from '../constants/theme';

const { width } = Dimensions.get('window');

const EmployeeNavbar = ({ state, descriptors, navigation }) => {
  /**
   * Navigation Logic:
   * Maps through the current navigation state routes to generate tab buttons.
   * This ensures the navbar automatically syncs with React Navigation tabs.
   */
  return (
    <View style={styles.container}>
      <View style={styles.navbar}>
        {state.routes.map((route, index) => {
          const { options } = descriptors[route.key];
          const isFocused = state.index === index;

          /**
           * onPress Handler:
           * Triggers the navigation event. If the tab isn't focused, it navigates
           * to that screen. If it is already focused, it can trigger a scroll-to-top (standard UX).
           */
          const onPress = () => {
            const event = navigation.emit({
              type: 'tabPress',
              target: route.key,
              canPreventDefault: true,
            });

            if (!isFocused && !event.defaultPrevented) {
              navigation.navigate(route.name);
            }
          };

          /**
           * Dynamic Icon Logic:
           * Swaps between filled and outlined icons based on 'isFocused'.
           * This provides immediate visual feedback to the user on where they are.
           */
          let iconName;
          if (route.name === 'Dashboard') {
            iconName = isFocused ? 'grid' : 'grid-outline';
          } else if (route.name === 'Tasks') {
            iconName = isFocused ? 'flash' : 'flash-outline';
          } else if (route.name === 'Profile') {
            iconName = isFocused ? 'person' : 'person-outline';
          }

          return (
            <TouchableOpacity
              key={index}
              onPress={onPress}
              style={styles.navItem}
              activeOpacity={0.6}
            >
              <View style={[
                styles.iconContainer,
                isFocused && styles.activeIconContainer
              ]}>
                <Ionicons 
                  name={iconName} 
                  size={26} 
                  color={isFocused ? '#000000' : '#8E8E93'} 
                />
              </View>
              {/* Simple Dot Indicator: Minimalist UI design as per template */}
              {isFocused && <View style={styles.indicator} />}
            </TouchableOpacity>
          );
        })}
      </View>
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    backgroundColor: '#FFFFFF',
    width: width,
    borderTopWidth: 1,
    borderTopColor: '#F0F0F0',
    paddingBottom: 25, // For iPhone home indicator
  },
  navbar: {
    flexDirection: 'row',
    backgroundColor: '#FFFFFF',
    width: width,
    height: 65,
    alignItems: 'center',
    justifyContent: 'space-around',
    paddingHorizontal: 20,
  },
  navItem: {
    alignItems: 'center',
    justifyContent: 'center',
    flex: 1,
  },
  iconContainer: {
    width: 44,
    height: 44,
    borderRadius: 22,
    alignItems: 'center',
    justifyContent: 'center',
  },
  activeIconContainer: {
    backgroundColor: '#F8F9FA', // Very subtle background for active
  },
  indicator: {
    marginTop: 2,
    width: 3,
    height: 3,
    borderRadius: 1.5,
    backgroundColor: '#000', // Small simple dot
  }
});

export default EmployeeNavbar;
