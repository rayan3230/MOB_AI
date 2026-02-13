import React from 'react';
import { View, Text, StyleSheet, TouchableOpacity, ScrollView, Image, Alert } from 'react-native';
import { FontAwesome } from '@expo/vector-icons';
import Logo from './Logo';
import { authService } from '../services/authService';

const Sidebar = ({ role, user, activePage = 'User_managment', onNavigate, onClose }) => {
  const adminLinks = [
    { name: 'Dashboard', id: 'Dashboard', icon: 'dashboard' },
    { name: 'AI Action', id: 'AI_Actions', icon: 'magic' },
    { name: 'Users management', id: 'User_managment', icon: 'users' },
    { name: 'Warehouse management', id: 'Warhouse_management', icon: 'building' },
    { name: 'Location management', id: 'Location_managment', icon: 'map-marker' },
    { name: 'Floor management', id: 'Floor_managment', icon: 'th' },
    { name: 'Gestion des Produits', id: 'StockingUnit_management', icon: 'archive' },
    { name: 'Gestion Vrack', id: 'Vrack_management', icon: 'database' },
    { name: 'Chariot management', id: 'Chariot_management', icon: 'truck' },
    { name: 'Visual representation', id: 'Visual_Warhouse', icon: 'eye' },
  ];

  const supervisorLinks = [
    { name: 'Dashboard', id: 'Dashboard', icon: 'dashboard' },
    { name: 'Floor management', id: 'Floor_managment', icon: 'th' },
    { name: 'Visual representation', id: 'Visual_Warhouse', icon: 'eye' },
  ];

  const employeeLinks = [
    { name: 'Home', id: 'Dashboard', icon: 'home' },
    { name: 'Tasks', id: 'List_Actions', icon: 'tasks' },
  ];

  const handleLogout = () => {
    Alert.alert(
      'Logout',
      'Are you sure you want to log out?',
      [
        { text: 'Cancel', style: 'cancel' },
        { 
          text: 'Logout', 
          onPress: async () => {
             await authService.logout();
             onNavigate('Logout');
          }, 
          style: 'destructive' 
        },
      ],
      { cancelable: true }
    );
  };

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
            <FontAwesome 
              name={link.icon} 
              size={18} 
              color={activePage === link.id ? '#00a3ff' : '#666'} 
              style={styles.navIcon} 
            />
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
        <TouchableOpacity 
          style={styles.profileSection} 
          onPress={() => onNavigate('Profile')}
        >
          <Image 
            source={{ uri: `https://ui-avatars.com/api/?name=${user?.user_name || 'User'}&background=random` }} 
            style={styles.avatar} 
          />
          <View style={styles.profileInfo}>
            <Text style={[
              styles.userName,
              activePage === 'Profile' && styles.activeNavText
            ]}>
              {user?.user_name || 'User'}
            </Text>
            <Text style={styles.userRole}>{role === 'admin' ? 'Administrator' : role === 'supervisor' ? 'Supervisor' : 'Staff'}</Text>
          </View>
        </TouchableOpacity>
        
        <TouchableOpacity style={styles.logoutButton} onPress={handleLogout}>
          <FontAwesome name="sign-out" size={20} color="#ff4d4d" />
          <Text style={styles.logoutText}>Logout</Text>
        </TouchableOpacity>

        <Text style={styles.versionText}>Flow Logix version 1.0</Text>
      </View>
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#ffffff',
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
    flexDirection: 'row',
    alignItems: 'center',
    paddingVertical: 12,
    marginBottom: 5,
  },
  navIcon: {
    width: 25,
    marginRight: 12,
    textAlign: 'center',
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
  logoutButton: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingVertical: 12,
    borderTopWidth: 1,
    borderTopColor: '#f0f0f0',
    marginTop: 10,
  },
  logoutText: {
    color: '#ff4d4d',
    fontSize: 15,
    fontWeight: '600',
    marginLeft: 12,
  },
  versionText: {
    fontSize: 11,
    color: '#bbb',
    textAlign: 'center',
    marginTop: 10,
  }
});

export default Sidebar;
