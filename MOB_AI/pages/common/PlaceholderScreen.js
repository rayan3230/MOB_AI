import React from 'react';
import { View, Text, StyleSheet } from 'react-native';
import { lightTheme } from '../../constants/theme';
const PlaceholderScreen = ({ title }) => (
  <View style={styles.container}>
    <Text style={styles.text}>{title}</Text>
  </View>
);

const styles = StyleSheet.create({
  container: { flex: 1, justifyContent: 'center', alignItems: 'center', backgroundColor: lightTheme.primary },
  text: { fontSize: 20, fontWeight: 'bold', color: '#333' }
});

export default PlaceholderScreen;
