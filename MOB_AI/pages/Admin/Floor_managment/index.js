import React from 'react';
import { View, Text, StyleSheet } from 'react-native';

const FloorManagement = () => {
  return (
    <View style={styles.container}>
      <Text style={styles.text}>Floor Management Screen</Text>
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    backgroundColor: '#fff',
  },
  text: {
    fontSize: 18,
    fontWeight: '600',
  },
});

export default FloorManagement;
