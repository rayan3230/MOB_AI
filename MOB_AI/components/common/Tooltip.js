import React, { useState } from 'react';
import { View, Text, StyleSheet, TouchableOpacity, Modal, ScrollView } from 'react-native';
import { Feather } from '@expo/vector-icons';
import { lightTheme } from '../../constants/theme';

const Tooltip = ({ children, content, title, position = 'top' }) => {
  const [visible, setVisible] = useState(false);

  return (
    <View>
      <TouchableOpacity onPress={() => setVisible(true)} activeOpacity={0.7}>
        {children}
      </TouchableOpacity>

      <Modal
        visible={visible}
        transparent
        animationType="fade"
        onRequestClose={() => setVisible(false)}
      >
        <TouchableOpacity 
          style={styles.overlay} 
          activeOpacity={1} 
          onPress={() => setVisible(false)}
        >
          <View style={styles.tooltipContainer}>
            <View style={styles.tooltipHeader}>
              {title && <Text style={styles.tooltipTitle}>{title}</Text>}
              <TouchableOpacity onPress={() => setVisible(false)} style={styles.closeButton}>
                <Feather name="x" size={20} color={lightTheme.textSecondary} />
              </TouchableOpacity>
            </View>
            <ScrollView style={styles.tooltipContent}>
              <Text style={styles.tooltipText}>{content}</Text>
            </ScrollView>
          </View>
        </TouchableOpacity>
      </Modal>
    </View>
  );
};

const styles = StyleSheet.create({
  overlay: {
    flex: 1,
    backgroundColor: 'rgba(0, 0, 0, 0.5)',
    justifyContent: 'center',
    alignItems: 'center',
    padding: 24,
  },
  tooltipContainer: {
    backgroundColor: lightTheme.white,
    borderRadius: 16,
    padding: 20,
    maxWidth: 340,
    maxHeight: '70%',
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.3,
    shadowRadius: 12,
    elevation: 8,
  },
  tooltipHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 12,
  },
  tooltipTitle: {
    fontSize: 16,
    fontWeight: '700',
    color: lightTheme.textPrimary,
    flex: 1,
  },
  closeButton: {
    padding: 4,
  },
  tooltipContent: {
    maxHeight: 300,
  },
  tooltipText: {
    fontSize: 14,
    color: lightTheme.textSecondary,
    lineHeight: 20,
  },
});

export default Tooltip;
