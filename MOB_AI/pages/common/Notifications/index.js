import React from 'react';
import { View, Text, StyleSheet } from 'react-native';
import { Feather } from '@expo/vector-icons';
import { lightTheme } from '../../../constants/theme';

const Notifications = () => {
  return (
    <View style={styles.container}>
      <View style={styles.iconWrapper}>
        <Feather name="bell" size={28} color={lightTheme.primary} />
      </View>
      <Text style={styles.title}>Notifications</Text>
      <Text style={styles.subtitle}>No new notifications right now.</Text>
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: lightTheme.white,
    justifyContent: 'center',
    alignItems: 'center',
    paddingHorizontal: 24,
  },
  iconWrapper: {
    width: 64,
    height: 64,
    borderRadius: 32,
    alignItems: 'center',
    justifyContent: 'center',
    backgroundColor: lightTheme.bgHighlight,
    borderWidth: 1,
    borderColor: lightTheme.borderHighlight,
    marginBottom: 14,
  },
  title: {
    fontSize: 24,
    fontWeight: '700',
    color: lightTheme.textPrimary,
  },
  subtitle: {
    marginTop: 8,
    fontSize: 14,
    color: lightTheme.textSecondary,
    textAlign: 'center',
  },
});

export default Notifications;
