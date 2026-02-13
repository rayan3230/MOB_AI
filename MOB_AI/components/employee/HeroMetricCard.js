import React from 'react';
import { View, Text, StyleSheet } from 'react-native';
import { Feather } from '@expo/vector-icons';
import { lightTheme } from '../../constants/theme';

const HeroMetricCard = ({ title, value }) => {
  return (
    <View style={styles.container}>
      <View>
        <Text style={styles.title}>{title}</Text>
        <Text style={styles.value}>{value}</Text>
      </View>
      <View style={styles.iconWrap}>
        <Feather name="box" size={22} color={lightTheme.white} />
      </View>
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    borderRadius: 18,
    backgroundColor: lightTheme.primary,
    padding: 16,
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  title: {
    color: lightTheme.white,
    fontSize: 16,
    fontWeight: '500',
    marginBottom: 6,
  },
  value: {
    color: lightTheme.white,
    fontSize: 38,
    fontWeight: '700',
  },
  iconWrap: {
    width: 42,
    height: 42,
    borderRadius: 14,
    backgroundColor: lightTheme.overlayLight,
    alignItems: 'center',
    justifyContent: 'center',
  },
});

export default HeroMetricCard;
