import React from 'react';
import { View, Text, StyleSheet } from 'react-native';

const WarehouseManagement = () => {
  return (
    <View style={styles.container}>
      <Text style={styles.text}>Warehouse Management Screen</Text>
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

export default WarehouseManagement;
