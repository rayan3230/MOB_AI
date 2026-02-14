import React, { useState } from 'react';
import { View, TextInput, Text, StyleSheet, TouchableOpacity } from 'react-native';
import { Feather } from '@expo/vector-icons';
import { lightTheme } from '../../constants/theme';

const Input = ({
  label,
  value,
  onChangeText,
  placeholder,
  error,
  icon,
  secureTextEntry = false,
  keyboardType = 'default',
  multiline = false,
  numberOfLines = 1,
  editable = true,
  disabled = false,
  style,
  inputStyle
}) => {
  const [isFocused, setIsFocused] = useState(false);
  const [showPassword, setShowPassword] = useState(false);

  return (
    <View style={[styles.container, style]}>
      {label && <Text style={styles.label}>{label}</Text>}
      <View style={[
        styles.inputContainer,
        isFocused && styles.focused,
        error && styles.error,
        disabled && styles.disabled
      ]}>
        {icon && (
          <Feather name={icon} size={18} color={error ? lightTheme.error : lightTheme.textSecondary} style={styles.icon} />
        )}
        <TextInput
          style={[styles.input, multiline && styles.multiline, inputStyle]}
          value={value}
          onChangeText={onChangeText}
          placeholder={placeholder}
          placeholderTextColor={lightTheme.placeholder}
          secureTextEntry={secureTextEntry && !showPassword}
          keyboardType={keyboardType}
          multiline={multiline}
          numberOfLines={numberOfLines}
          editable={editable && !disabled}
          onFocus={() => setIsFocused(true)}
          onBlur={() => setIsFocused(false)}
        />
        {secureTextEntry && (
          <TouchableOpacity onPress={() => setShowPassword(!showPassword)} style={styles.eyeIcon}>
            <Feather name={showPassword ? 'eye' : 'eye-off'} size={18} color={lightTheme.textSecondary} />
          </TouchableOpacity>
        )}
      </View>
      {error && <Text style={styles.errorText}>{error}</Text>}
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    marginBottom: 16,
  },
  label: {
    fontSize: 14,
    fontWeight: '600',
    color: lightTheme.textPrimary,
    marginBottom: 8,
  },
  inputContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: lightTheme.inputBackground,
    borderRadius: 12,
    borderWidth: 2,
    borderColor: 'transparent',
    paddingHorizontal: 12,
  },
  focused: {
    borderColor: lightTheme.primary,
    backgroundColor: lightTheme.white,
  },
  error: {
    borderColor: lightTheme.error,
  },
  disabled: {
    opacity: 0.6,
    backgroundColor: lightTheme.divider,
  },
  input: {
    flex: 1,
    paddingVertical: 12,
    fontSize: 14,
    color: lightTheme.textPrimary,
  },
  multiline: {
    paddingVertical: 12,
    minHeight: 80,
    textAlignVertical: 'top',
  },
  icon: {
    marginRight: 8,
  },
  eyeIcon: {
    padding: 4,
  },
  errorText: {
    marginTop: 4,
    fontSize: 12,
    color: lightTheme.error,
  },
});

export default Input;
