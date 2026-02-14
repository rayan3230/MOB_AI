import React from 'react';
import { View, StyleSheet, TouchableOpacity } from 'react-native';
import { Feather } from '@expo/vector-icons';
import { lightTheme } from '../constants/theme';
const TopHeader = ({ onMenuPress, onSettingsPress, onNotificationPress }) => {
  return (
    <View style={styles.outerContainer}>
      <View style={styles.innerContainer}>
        <TouchableOpacity onPress={onMenuPress}>
          <Feather name="menu" size={24} color={lightTheme.primary} />
        </TouchableOpacity>
        
        <View style={styles.rightIcons}>
          <TouchableOpacity onPress={onNotificationPress} style={styles.iconButton}>
            <Feather name="bell" size={24} color={lightTheme.primary} />
          </TouchableOpacity>
          <TouchableOpacity onPress={onSettingsPress}>
            <Feather name="settings" size={24} color={lightTheme.primary} />
          </TouchableOpacity>
        </View>
      </View>
    </View>
  );
};

const styles = StyleSheet.create({
  outerContainer: {
    backgroundColor: lightTheme.primary, // Original dark background
    paddingTop: 10,
  },
  innerContainer: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingHorizontal: 25,
    paddingVertical: 20,
    backgroundColor: '#fff',
    borderTopLeftRadius: 40,
    borderTopRightRadius: 40,
    height: 90,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: -5 },
    shadowOpacity: 0.05,
    shadowRadius: 10,
    elevation: 8,
  },
  rightIcons: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  iconButton: {
    marginRight: 20,
  }
});

export default TopHeader;
