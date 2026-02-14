import React from 'react';
import { View, StyleSheet, TouchableOpacity, Dimensions, Text } from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { lightTheme } from '../constants/theme';

const { width } = Dimensions.get('window');

const EmployeeNavbar = ({ state, navigation }) => {
  /**
   * Navigation Logic:
   * Maps through the current navigation state routes to generate tab buttons.
   * This ensures the navbar automatically syncs with React Navigation tabs.
   */
  return (
    <View style={styles.container}>
      <View style={styles.navbar}>
        {state.routes.map((route, index) => {
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
          let label;
          let iconSize = 22;
          
          if (route.name === 'Home') {
            iconName = isFocused ? 'home' : 'home-outline';
            label = 'Home';
          } else if (route.name === 'Tasks') {
            iconName = isFocused ? 'list' : 'list-outline';
            label = 'Tasks';
          } else if (route.name === 'Scan') {
            iconName = isFocused ? 'scan' : 'scan-outline';
            label = 'Scan';
            iconSize = 28; // Larger for emphasis
          } else if (route.name === 'Profile') {
            iconName = isFocused ? 'person' : 'person-outline';
            label = 'Profile';
          }

          // Special styling for Scan button
          const isScanButton = route.name === 'Scan';

          return (
            <TouchableOpacity
              key={index}
              onPress={onPress}
              style={styles.navItem}
              activeOpacity={0.6}
            >
              <View style={[
                styles.iconContainer,
                isFocused && styles.activeIconContainer,
                isScanButton && styles.scanButton,
                isScanButton && isFocused && styles.scanButtonActive
              ]}>
                <Ionicons 
                  name={iconName} 
                  size={iconSize}
                  color={
                    isScanButton && isFocused ? lightTheme.white :
                    isScanButton ? lightTheme.primary :
                    isFocused ? lightTheme.primary : 
                    lightTheme.textSecondary
                  }
                />
                {!isScanButton && (
                  <Text style={[styles.label, isFocused && styles.activeLabel]}>{label}</Text>
                )}
              </View>
              {isScanButton && (
                <Text style={[styles.scanLabel, isFocused && styles.scanLabelActive]}>
                  {label}
                </Text>
              )}
            </TouchableOpacity>
          );
        })}
      </View>
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    backgroundColor: lightTheme.white,
    width: width,
    paddingBottom: 16,
  },
  navbar: {
    flexDirection: 'row',
    backgroundColor: lightTheme.white,
    marginHorizontal: 16,
    marginTop: 8,
    borderRadius: 18,
    borderWidth: 1,
    borderColor: lightTheme.border,
    height: 64,
    alignItems: 'center',
    justifyContent: 'space-around',
    paddingHorizontal: 10,
    shadowColor: lightTheme.black,
    shadowOffset: { width: 0, height: 3 },
    shadowOpacity: 0.08,
    shadowRadius: 8,
    elevation: 5,
  },
  navItem: {
    alignItems: 'center',
    justifyContent: 'center',
    flex: 1,
    height: '100%',
  },
  iconContainer: {
    minWidth: 92,
    height: 44,
    borderRadius: 14,
    alignItems: 'center',
    justifyContent: 'center',
    flexDirection: 'row',
    gap: 8,
  },
  activeIconContainer: {
    backgroundColor: lightTheme.bgHighlight,
    borderWidth: 1,
    borderColor: lightTheme.borderHighlight,
  },
  label: {
    fontSize: 13,
    color: lightTheme.textSecondary,
    fontWeight: '500',
  },
  activeLabel: {
    color: lightTheme.primary,
    fontWeight: '700',
  },
  scanButton: {
    width: 56,
    height: 56,
    borderRadius: 28,
    backgroundColor: lightTheme.white,
    borderWidth: 3,
    borderColor: lightTheme.primary,
    marginTop: -20,
    shadowColor: lightTheme.primary,
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.3,
    shadowRadius: 8,
    elevation: 8,
  },
  scanButtonActive: {
    backgroundColor: lightTheme.primary,
  },
  scanLabel: {
    fontSize: 11,
    color: lightTheme.textSecondary,
    fontWeight: '600',
    marginTop: 4,
  },
  scanLabelActive: {
    color: lightTheme.primary,
    fontWeight: '700',
  },
});

export default EmployeeNavbar;
