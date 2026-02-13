import React, { useState } from 'react';
import {
  View,
  Text,
  StyleSheet,
  TouchableOpacity,
  Modal,
  FlatList,
  TextInput,
  SafeAreaView,
  TouchableWithoutFeedback,
} from 'react-native';
import { Feather } from '@expo/vector-icons';

const OptionSelector = ({
  options = [],
  selectedValue,
  onValueChange,
  label,
  placeholder = 'Select an option',
  labelKey = 'label',
  valueKey = 'value',
  icon = 'list',
}) => {
  const [modalVisible, setModalVisible] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');

  const selectedLabel =
    options.find((opt) => opt[valueKey] === selectedValue)?.[labelKey] || placeholder;

  const filteredOptions = options.filter((opt) =>
    opt[labelKey].toLowerCase().includes(searchQuery.toLowerCase())
  );

  const renderItem = ({ item }) => (
    <TouchableOpacity
      style={styles.optionItem}
      onPress={() => {
        onValueChange(item[valueKey]);
        setModalVisible(false);
        setSearchQuery('');
      }}
    >
      <Text style={styles.optionText}>{item[labelKey]}</Text>
      {selectedValue === item[valueKey] && (
        <Feather name="check" size={20} color="#2196F3" />
      )}
    </TouchableOpacity>
  );

  return (
    <>
      {label && <Text style={styles.label}>{label}</Text>}
      <TouchableOpacity
        style={styles.selectorButton}
        onPress={() => setModalVisible(true)}
      >
        <Feather name={icon} size={18} color="#94A3B8" style={styles.inputIcon} />
        <Text style={styles.selectorButtonText} numberOfLines={1}>
          {selectedLabel}
        </Text>
        <Feather name="chevron-down" size={20} color="#94A3B8" />
      </TouchableOpacity>

      <Modal
        animationType="slide"
        transparent={true}
        visible={modalVisible}
        onRequestClose={() => setModalVisible(false)}
      >
        <TouchableWithoutFeedback onPress={() => setModalVisible(false)}>
          <SafeAreaView style={styles.modalOverlay}>
            <TouchableWithoutFeedback>
              <View style={styles.modalContent}>
                <View style={styles.handle} />
                <View style={styles.searchContainer}>
                  <Feather name="search" size={20} color="#94A3B8" />
                  <TextInput
                    style={styles.searchInput}
                    placeholder="Search..."
                    placeholderTextColor="#94A3B8"
                    value={searchQuery}
                    onChangeText={setSearchQuery}
                  />
                </View>
                <FlatList
                  data={filteredOptions}
                  renderItem={renderItem}
                  keyExtractor={(item) => item[valueKey]?.toString()}
                  showsVerticalScrollIndicator={false}
                  contentContainerStyle={styles.listContent}
                  ListEmptyComponent={
                    <View style={styles.emptyContainer}>
                      <Text style={styles.emptyText}>No options found</Text>
                    </View>
                  }
                />
              </View>
            </TouchableWithoutFeedback>
          </SafeAreaView>
        </TouchableWithoutFeedback>
      </Modal>
    </>
  );
};

const styles = StyleSheet.create({
  label: {
    fontSize: 14,
    fontWeight: '700',
    marginBottom: 8,
    color: '#475569',
  },
  selectorButton: {
    backgroundColor: '#F8FAFC',
    borderRadius: 12,
    borderWidth: 1,
    borderColor: '#E2E8F0',
    flexDirection: 'row',
    alignItems: 'center',
    height: 54,
    paddingHorizontal: 12,
  },
  inputIcon: {
    marginRight: 10,
  },
  selectorButtonText: {
    flex: 1,
    fontSize: 16,
    color: '#1E293B',
  },
  modalOverlay: {
    flex: 1,
    backgroundColor: 'rgba(0, 0, 0, 0.5)',
    justifyContent: 'flex-end',
  },
  modalContent: {
    backgroundColor: '#FFF',
    borderTopLeftRadius: 25,
    borderTopRightRadius: 25,
    paddingHorizontal: 20,
    paddingBottom: 20,
    maxHeight: '70%',
  },
  handle: {
    width: 40,
    height: 5,
    backgroundColor: '#E0E0E0',
    borderRadius: 3,
    alignSelf: 'center',
    marginTop: 12,
    marginBottom: 15,
  },
  searchContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#F1F5F9',
    borderRadius: 12,
    paddingHorizontal: 12,
    marginBottom: 15,
  },
  searchInput: {
    flex: 1,
    height: 48,
    fontSize: 16,
    marginLeft: 8,
    color: '#1E293B',
  },
  listContent: {
    paddingBottom: 20,
  },
  optionItem: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingVertical: 16,
    borderBottomWidth: 1,
    borderBottomColor: '#F1F5F9',
  },
  optionText: {
    fontSize: 16,
    color: '#334155',
    fontWeight: '500',
  },
  emptyContainer: {
    alignItems: 'center',
    padding: 20,
  },
  emptyText: {
    fontSize: 16,
    color: '#94A3B8',
  },
});

export default OptionSelector;
