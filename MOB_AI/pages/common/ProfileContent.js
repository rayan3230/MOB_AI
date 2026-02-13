import React, { useState } from 'react';
import { View, Text, StyleSheet, Image, TouchableOpacity, ScrollView, TextInput, Alert, ActivityIndicator } from 'react-native';
import { Feather, FontAwesome, Ionicons } from '@expo/vector-icons';
import { authService } from '../../services/authService';

const ProfileContent = ({ user: initialUser, role, navigation, onOpenDrawer }) => {
  const [isEditing, setIsEditing] = useState(false);
  const [loading, setLoading] = useState(false);
  const [user, setUser] = useState(initialUser);
  
  // Form states
  const [formData, setFormData] = useState({
    user_name: initialUser?.user_name || '',
    email: initialUser?.email || '',
    telephone: initialUser?.telephone || '',
    adresse: initialUser?.adresse || '',
  });

  const handleLogout = () => {
    Alert.alert(
      "Déconnexion",
      "Êtes-vous sûr de vouloir vous déconnecter ?",
      [
        { text: "Annuler", style: "cancel" },
        { 
          text: "Déconnexion", 
          style: "destructive",
          onPress: async () => {
            await authService.logout();
            navigation.replace('Login');
          }
        }
      ]
    );
  };

  const handleUpdate = async () => {
    setLoading(true);
    try {
      const response = await authService.updateProfile(user.id, formData);
      if (response && response.user) {
        setUser(response.user);
        setIsEditing(false);
        Alert.alert("Succès", "Profil mis à jour avec succès");
      }
    } catch (error) {
      console.error(error);
      Alert.alert("Erreur", "Impossible de mettre à jour le profil");
    } finally {
      setLoading(false);
    }
  };

  const menuItems = [
    { id: 1, title: 'Paramètre du compte', icon: 'settings', action: () => setIsEditing(true) },
    { id: 2, title: 'Notifications', icon: 'bell' },
    { id: 3, title: 'Sécurité', icon: 'shield' },
    { id: 4, title: 'Aide & Support', icon: 'help-circle' },
  ];

  const bottomMenuItems = [
    { id: 5, title: 'À propos', icon: 'info' },
    { id: 6, title: 'Confidentialité', icon: 'lock' },
  ];

  return (
    <View style={styles.container}>
      <View style={styles.headerContainer}>
        <View style={styles.headerTop}>
          <View style={styles.leftHeader}>
            {onOpenDrawer && (
              <TouchableOpacity onPress={onOpenDrawer} style={styles.menuButton}>
                <Feather name="menu" size={24} color="#333" />
              </TouchableOpacity>
            )}
          </View>
          <TouchableOpacity style={styles.powerButton} onPress={handleLogout}>
            <Feather name="power" size={20} color="#FF3B30" />
          </TouchableOpacity>
        </View>
      </View>

      <ScrollView style={styles.content} showsVerticalScrollIndicator={false}>
        <View style={styles.profileCard}>
          
          {isEditing ? (
            <TextInput
              style={styles.userNameInput}
              value={formData.user_name}
              onChangeText={(text) => setFormData({...formData, user_name: text})}
              placeholder="Nom complet"
            />
          ) : (
            <Text style={styles.userName}>{user?.user_name || 'Utilisateur'}</Text>
          )}

          <View style={styles.roleContainer}>
            <FontAwesome name="drivers-license-o" size={12} color="#666" />
            <Text style={styles.userRole}>{role === 'employee' ? 'Employé' : role === 'admin' ? 'Administrateur' : 'Superviseur'}</Text>
          </View>
        </View>

        <View style={styles.infoSection}>
            <Text style={styles.sectionTitle}>Informations personnelles</Text>
            
            <View style={styles.infoItem}>
              <Feather name="mail" size={18} color="#666" style={styles.infoIcon} />
              <View style={styles.infoContent}>
                <Text style={styles.infoLabel}>Email</Text>
                {isEditing ? (
                  <TextInput
                    style={styles.infoInput}
                    value={formData.email}
                    onChangeText={(text) => setFormData({...formData, email: text})}
                    placeholder="E-mail"
                    keyboardType="email-address"
                  />
                ) : (
                  <Text style={styles.infoValue}>{user?.email || 'Non renseigné'}</Text>
                )}
              </View>
            </View>

            <View style={styles.infoItem}>
              <Feather name="phone" size={18} color="#666" style={styles.infoIcon} />
              <View style={styles.infoContent}>
                <Text style={styles.infoLabel}>Téléphone</Text>
                {isEditing ? (
                  <TextInput
                    style={styles.infoInput}
                    value={formData.telephone}
                    onChangeText={(text) => setFormData({...formData, telephone: text})}
                    placeholder="Téléphone"
                    keyboardType="phone-pad"
                  />
                ) : (
                  <Text style={styles.infoValue}>{user?.telephone || 'Non renseigné'}</Text>
                )}
              </View>
            </View>

            <View style={styles.infoItem}>
              <Feather name="map-pin" size={18} color="#666" style={styles.infoIcon} />
              <View style={styles.infoContent}>
                <Text style={styles.infoLabel}>Adresse</Text>
                {isEditing ? (
                  <TextInput
                    style={styles.infoInput}
                    value={formData.adresse}
                    onChangeText={(text) => setFormData({...formData, adresse: text})}
                    placeholder="Adresse"
                  />
                ) : (
                  <Text style={styles.infoValue}>{user?.adresse || 'Non renseignée'}</Text>
                )}
              </View>
            </View>
        </View>

        {isEditing ? (
          <View style={styles.actionButtons}>
            <TouchableOpacity 
              style={[styles.btn, styles.btnCancel]} 
              onPress={() => {
                setIsEditing(false);
                setFormData({
                    user_name: user?.user_name || '',
                    email: user?.email || '',
                    telephone: user?.telephone || '',
                    adresse: user?.adresse || '',
                });
              }}
            >
              <Text style={styles.btnCancelText}>Annuler</Text>
            </TouchableOpacity>
            <TouchableOpacity 
              style={[styles.btn, styles.btnSave]} 
              onPress={handleUpdate}
              disabled={loading}
            >
              {loading ? <ActivityIndicator color="#fff" /> : <Text style={styles.btnSaveText}>Enregistrer</Text>}
            </TouchableOpacity>
          </View>
        ) : (
          <>
            <View style={styles.menuSection}>
              {menuItems.map((item) => (
                <TouchableOpacity key={item.id} style={styles.menuItem} onPress={item.action}>
                  <View style={styles.menuLeft}>
                    <Feather name={item.icon} size={20} color="#555" style={styles.menuIcon} />
                    <Text style={styles.menuText}>{item.title}</Text>
                  </View>
                  <Feather name="chevron-right" size={20} color="#ccc" />
                </TouchableOpacity>
              ))}
            </View>

            <View style={styles.divider} />

            <View style={styles.menuSection}>
              {bottomMenuItems.map((item) => (
                <TouchableOpacity key={item.id} style={styles.menuItem}>
                  <View style={styles.menuLeft}>
                    <Feather name={item.icon} size={20} color="#555" style={styles.menuIcon} />
                    <Text style={styles.menuText}>{item.title}</Text>
                  </View>
                  <Feather name="chevron-right" size={20} color="#ccc" />
                </TouchableOpacity>
              ))}
            </View>
          </>
        )}
        <View style={{ height: 40 }} />
      </ScrollView>
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#04324C',
  },
  headerContainer: {
    paddingTop: 10,
  },
  headerTop: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingHorizontal: 25,
    paddingVertical: 20,
    backgroundColor: '#fff',
    borderTopLeftRadius: 40,
    borderTopRightRadius: 40,
    height: 90,
  },
  leftHeader: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  menuButton: {
    marginRight: 15,
  },
  headerTitle: {
    fontSize: 24,
    fontWeight: 'bold',
    color: '#000',
  },
  powerButton: {
    width: 40,
    height: 40,
    borderRadius: 20,
    borderWidth: 1,
    borderColor: '#FEE2E2',
    backgroundColor: '#FEF2F2',
    justifyContent: 'center',
    alignItems: 'center',
  },
  content: {
    flex: 1,
    paddingHorizontal: 25,
    backgroundColor: '#fff',
  },
  profileCard: {
    backgroundColor: '#fff',
    borderRadius: 20,
    padding: 20,
    alignItems: 'center',
    marginTop: 10,
    marginBottom: 20,
  },
  imageContainer: {
    position: 'relative',
    marginBottom: 15,
  },
  profileImage: {
    width: 100,
    height: 100,
    borderRadius: 50,
    borderWidth: 3,
    borderColor: '#f0f0f0',
  },
  editBadge: {
    position: 'absolute',
    bottom: 5,
    right: 5,
    backgroundColor: '#00a3ff',
    width: 28,
    height: 28,
    borderRadius: 14,
    justifyContent: 'center',
    alignItems: 'center',
    borderWidth: 2,
    borderColor: '#fff',
  },
  userName: {
    fontSize: 22,
    fontWeight: 'bold',
    color: '#000',
    marginBottom: 5,
  },
  userNameInput: {
    fontSize: 22,
    fontWeight: 'bold',
    color: '#000',
    marginBottom: 5,
    borderBottomWidth: 1,
    borderBottomColor: '#ccc',
    paddingHorizontal: 10,
    minWidth: 200,
    textAlign: 'center',
  },
  roleContainer: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  userRole: {
    fontSize: 14,
    color: '#666',
    marginLeft: 8,
  },
  infoSection: {
    marginBottom: 20,
    backgroundColor: '#f9f9f9',
    borderRadius: 15,
    padding: 15,
  },
  sectionTitle: {
    fontSize: 16,
    fontWeight: 'bold',
    color: '#333',
    marginBottom: 15,
  },
  infoItem: {
    flexDirection: 'row',
    alignItems: 'flex-start',
    marginBottom: 15,
  },
  infoIcon: {
    marginTop: 2,
    marginRight: 12,
  },
  infoContent: {
    flex: 1,
  },
  infoLabel: {
    fontSize: 12,
    color: '#888',
    marginBottom: 2,
  },
  infoValue: {
    fontSize: 15,
    color: '#333',
    fontWeight: '500',
  },
  infoInput: {
    fontSize: 15,
    color: '#333',
    borderBottomWidth: 1,
    borderBottomColor: '#ddd',
    paddingVertical: 2,
  },
  menuSection: {
    marginBottom: 10,
  },
  menuItem: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingVertical: 15,
  },
  menuLeft: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  menuIcon: {
    marginRight: 15,
  },
  menuText: {
    fontSize: 16,
    color: '#333',
    fontWeight: '500',
  },
  divider: {
    height: 1,
    backgroundColor: '#f5f5f5',
    marginVertical: 10,
  },
  actionButtons: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    marginTop: 10,
  },
  btn: {
    flex: 0.48,
    height: 50,
    borderRadius: 12,
    justifyContent: 'center',
    alignItems: 'center',
  },
  btnCancel: {
    backgroundColor: '#f0f0f0',
  },
  btnSave: {
    backgroundColor: '#04324C',
  },
  btnCancelText: {
    color: '#666',
    fontWeight: 'bold',
  },
  btnSaveText: {
    color: '#fff',
    fontWeight: 'bold',
  },
});

export default ProfileContent;

