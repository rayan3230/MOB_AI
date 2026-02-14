import React from 'react';
import { TouchableOpacity, Text, StyleSheet, View } from 'react-native';
import { Feather } from '@expo/vector-icons';
import { lightTheme } from '../../constants/theme';
import * as Haptics from 'expo-haptics';

const QuickActionButton = ({ 
  icon, 
  label, 
  onPress, 
  variant = 'primary',
  badge = null,
  disabled = false
}) => {
  const handlePress = () => {
    Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Medium);
    onPress();
  };

  const getVariantColors = () => {
    switch (variant) {
      case 'primary':
        return { bg: lightTheme.primary, icon: lightTheme.white };
      case 'success':
        return { bg: lightTheme.success, icon: lightTheme.white };
      case 'warning':
        return { bg: lightTheme.warning, icon: lightTheme.white };
      case 'secondary':
        return { bg: lightTheme.secondary, icon: lightTheme.textPrimary };
      default:
        return { bg: lightTheme.primary, icon: lightTheme.white };
    }
  };

  const colors = getVariantColors();

  return (
    <TouchableOpacity
      style={[styles.container, disabled && styles.disabled]}
      onPress={handlePress}
      disabled={disabled}
      activeOpacity={0.8}
    >
      <View style={[styles.iconContainer, { backgroundColor: colors.bg }]}>
        <Feather name={icon} size={28} color={colors.icon} />
        {badge && (
          <View style={styles.badge}>
            <Text style={styles.badgeText}>{badge}</Text>
          </View>
        )}
      </View>
      <Text style={styles.label}>{label}</Text>
    </TouchableOpacity>
  );
};

const styles = StyleSheet.create({
  container: {
    alignItems: 'center',
    gap: 8,
    flex: 1,
    maxWidth: 100,
  },
  iconContainer: {
    width: 64,
    height: 64,
    borderRadius: 20,
    alignItems: 'center',
    justifyContent: 'center',
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.15,
    shadowRadius: 8,
    elevation: 4,
    position: 'relative',
  },
  disabled: {
    opacity: 0.5,
  },
  label: {
    fontSize: 12,
    fontWeight: '600',
    color: lightTheme.textPrimary,
    textAlign: 'center',
  },
  badge: {
    position: 'absolute',
    top: -4,
    right: -4,
    backgroundColor: lightTheme.error,
    borderRadius: 10,
    minWidth: 20,
    height: 20,
    alignItems: 'center',
    justifyContent: 'center',
    paddingHorizontal: 4,
    borderWidth: 2,
    borderColor: lightTheme.white,
  },
  badgeText: {
    color: lightTheme.white,
    fontSize: 10,
    fontWeight: '800',
  },
});

export default QuickActionButton;
