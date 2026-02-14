import React from 'react';
import { TouchableOpacity, Text, StyleSheet, ActivityIndicator } from 'react-native';
import { Feather } from '@expo/vector-icons';
import { lightTheme } from '../../constants/theme';

const Button = ({ 
  children, 
  variant = 'primary', 
  size = 'medium',
  onPress, 
  disabled = false, 
  loading = false,
  icon = null,
  fullWidth = false,
  style,
  textStyle
}) => {
  const getVariantStyle = () => {
    switch (variant) {
      case 'primary':
        return styles.primaryButton;
      case 'secondary':
        return styles.secondaryButton;
      case 'danger':
        return styles.dangerButton;
      case 'success':
        return styles.successButton;
      case 'outline':
        return styles.outlineButton;
      case 'ghost':
        return styles.ghostButton;
      default:
        return styles.primaryButton;
    }
  };

  const getTextVariantStyle = () => {
    switch (variant) {
      case 'outline':
      case 'ghost':
        return styles.outlineText;
      default:
        return styles.buttonText;
    }
  };

  const getSizeStyle = () => {
    switch (size) {
      case 'small':
        return styles.smallButton;
      case 'large':
        return styles.largeButton;
      default:
        return styles.mediumButton;
    }
  };

  return (
    <TouchableOpacity
      style={[
        styles.button,
        getVariantStyle(),
        getSizeStyle(),
        fullWidth && styles.fullWidth,
        (disabled || loading) && styles.disabled,
        style
      ]}
      onPress={onPress}
      disabled={disabled || loading}
      activeOpacity={0.7}
    >
      {loading ? (
        <ActivityIndicator color={variant === 'outline' || variant === 'ghost' ? lightTheme.primary : lightTheme.white} />
      ) : (
        <>
          {icon && <Feather name={icon} size={size === 'small' ? 14 : size === 'large' ? 20 : 16} color={variant === 'outline' || variant === 'ghost' ? lightTheme.primary : lightTheme.white} style={styles.icon} />}
          <Text style={[getTextVariantStyle(), textStyle]}>{children}</Text>
        </>
      )}
    </TouchableOpacity>
  );
};

const styles = StyleSheet.create({
  button: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    borderRadius: 12,
    gap: 6,
  },
  fullWidth: {
    width: '100%',
  },
  smallButton: {
    paddingVertical: 8,
    paddingHorizontal: 12,
  },
  mediumButton: {
    paddingVertical: 12,
    paddingHorizontal: 16,
  },
  largeButton: {
    paddingVertical: 16,
    paddingHorizontal: 24,
  },
  primaryButton: {
    backgroundColor: lightTheme.primary,
  },
  secondaryButton: {
    backgroundColor: lightTheme.secondary,
  },
  dangerButton: {
    backgroundColor: lightTheme.error,
  },
  successButton: {
    backgroundColor: lightTheme.success,
  },
  outlineButton: {
    backgroundColor: 'transparent',
    borderWidth: 2,
    borderColor: lightTheme.primary,
  },
  ghostButton: {
    backgroundColor: 'transparent',
  },
  disabled: {
    opacity: 0.5,
  },
  buttonText: {
    color: lightTheme.white,
    fontSize: 14,
    fontWeight: '700',
  },
  outlineText: {
    color: lightTheme.primary,
    fontSize: 14,
    fontWeight: '700',
  },
  icon: {
    marginRight: 4,
  },
});

export default Button;
