import React from 'react';
import { View, StyleSheet } from 'react-native';
import { lightTheme } from '../../constants/theme';

export const SkeletonCard = ({ height = 100 }) => (
  <View style={[styles.card, { height }]}>
    <View style={[styles.skeleton, styles.shimmer, { width: '60%', height: 16 }]} />
    <View style={[styles.skeleton, styles.shimmer, { width: '90%', height: 12, marginTop: 8 }]} />
    <View style={[styles.skeleton, styles.shimmer, { width: '70%', height: 12, marginTop: 4 }]} />
  </View>
);

export const SkeletonList = ({ count = 3 }) => (
  <View style={styles.container}>
    {Array.from({ length: count }).map((_, index) => (
      <SkeletonCard key={index} />
    ))}
  </View>
);

const styles = StyleSheet.create({
  container: {
    padding: 16,
    gap: 12,
  },
  card: {
    backgroundColor: lightTheme.white,
    borderRadius: 12,
    padding: 16,
    justifyContent: 'center',
  },
  skeleton: {
    backgroundColor: lightTheme.inputBackground,
    borderRadius: 6,
  },
  shimmer: {
    opacity: 0.6,
  },
});

export default SkeletonList;
