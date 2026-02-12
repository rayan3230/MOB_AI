import React from 'react';
import { View, Text, StyleSheet, TouchableOpacity, ScrollView, Image } from 'react-native';
import { FontAwesome } from '@expo/vector-icons';
import Logo from './Logo';

const Sidebar = ({ role, activePage = 'User_managment', onNavigate, onClose }) => {
  const adminLinks = [
    { name: 'Dashboard', id: 'Dashboard' },
    { name: 'AI Action', id: 'AI_Actions' },
    { name: 'Users management', id: 'User_managment' },
    { name: 'Warehouse management', id: 'Warhouse_management' },
    { name: 'Location management', id: 'Location_managment' },
    { name: 'Floor management', id: 'Floor_managment' },
    { name: 'Stocking units management', id: 'StockingUnit_management' },
    { name: 'Chariot management', id: 'Chariot_management' },
    { name: 'Visual representation of warehousre', id: 'Visual_Warhouse' },
  ];

  const supervisorLinks = [
    { name: 'Dashboard', id: 'Dashboard' },
    { name: 'Floor management', id: 'Floor_managment' },
    { name: 'Visual representation', id: 'Visual_Warhouse' },
  ];

  const employeeLinks = [
    { name: 'Home', id: 'Dashboard' },
    { name: 'Tasks', id: 'List_Actions' },
  ];

  const getLinks = () => {
    if (role === 'admin') return adminLinks;
    if (role === 'supervisor') return supervisorLinks;
    return employeeLinks;
  };

  return (
    <View style={styles.container}>
      <View style={styles.header}>
        <View style={styles.logoRow}>
          <Logo width={30} height={30} color="#000" />
          <Text style={styles.logoText}>FLOWLOGIX</Text>
        </View>
        <TouchableOpacity onPress={onClose} style={styles.closeButton}>
            <View style={styles.divider} />
        </TouchableOpacity>
      </View>
      
      <ScrollView style={styles.content} showsVerticalScrollIndicator={false}>
        {getLinks().map((link) => (
          <TouchableOpacity
            key={link.id}
            style={styles.navLink}
            onPress={() => onNavigate(link.id)}
          >
            <Text style={[
              styles.navText,
              activePage === link.id && styles.activeNavText
            ]}>
              {link.name}
            </Text>
          </TouchableOpacity>
        ))}
      </ScrollView>

      <View style={styles.footer}>
        <View style={styles.profileSection}>
          <Image 
            source={{ uri: 'https://i.pravatar.cc/150?u=wassim' }} // Placeholder for the avatar
            style={styles.avatar} 
          />
          <View style={styles.profileInfo}>
            <Text style={styles.userName}>Wassim Mouhouce</Text>
            <Text style={styles.userRole}>{role === 'admin' ? 'Admin' : 'Staff'}</Text>
          </View>
        </View>
        <Text style={styles.versionText}>Flow Logix version 1.0</Text>
      </View>
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#fff',
    paddingTop: 60,
    borderRightWidth: 1,
    borderRightColor: '#f0f0f0',
  },
  header: {
    paddingHorizontal: 25,
    marginBottom: 40,
  },
  logoRow: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  logoText: {
    fontSize: 18,
    fontWeight: '800',
    color: '#000',
    marginLeft: 12,
    letterSpacing: 1,
  },
  divider: {
    height: 1,
    backgroundColor: '#eee',
    marginTop: 25,
    width: '100%',
  },
  content: {
    paddingHorizontal: 25,
  },
  navLink: {
    paddingVertical: 12,
    marginBottom: 5,
  },
  navText: {
    color: '#333',
    fontSize: 15,
    fontWeight: '500',
  },
  activeNavText: {
    color: '#00a3ff', // Bright blue from the image
    fontWeight: '600',
  },
  footer: {
    paddingHorizontal: 25,
    paddingBottom: 30,
    borderTopWidth: 1,
    borderTopColor: '#f8f9fa',
    paddingTop: 20,
  },
  profileSection: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 20,
  },
  avatar: {
    width: 45,
    height: 45,
    borderRadius: 22.5,
    backgroundColor: '#eee',
  },
  profileInfo: {
    marginLeft: 12,
  },
  userName: {
    fontSize: 14,
    fontWeight: '700',
    color: '#1a1a1a',
  },
  userRole: {
    fontSize: 12,
    color: '#888',
    marginTop: 2,
  },
  versionText: {
    fontSize: 11,
    color: '#bbb',
    textAlign: 'center',
    marginTop: 10,
  }
});

export default Sidebar;
