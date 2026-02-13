import React, { useMemo, useState } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  TextInput,
  TouchableOpacity,
  Image,
  ActivityIndicator,
  Alert,
} from 'react-native';
import { Feather } from '@expo/vector-icons';
import { authService } from '../../../services/authService';
import { lightTheme } from '../../../constants/theme';

const EmployeeProfile = ({ route, navigation }) => {
  const initialUser = route?.params?.user || {};
  const [user, setUser] = useState(initialUser);
  const [isEditing, setIsEditing] = useState(false);
  const [isSaving, setIsSaving] = useState(false);
  const [formData, setFormData] = useState({
    user_name: initialUser?.user_name || '',
    email: initialUser?.email || '',
    telephone: initialUser?.telephone || '',
    adresse: initialUser?.adresse || '',
  });

  const avatarUri = useMemo(() => {
    const name = encodeURIComponent(user?.user_name || 'Employee');
    return `https://ui-avatars.com/api/?name=${name}&background=04324C&color=fff&size=128`;
  }, [user?.user_name]);

  const handleLogout = () => {
    Alert.alert('Déconnexion', 'Êtes-vous sûr de vouloir vous déconnecter ?', [
      { text: 'Annuler', style: 'cancel' },
      {
        text: 'Déconnexion',
        style: 'destructive',
        onPress: async () => {
          await authService.logout();
          navigation.replace('Login');
        },
      },
    ]);
  };

  const handleCancel = () => {
    setIsEditing(false);
    setFormData({
      user_name: user?.user_name || '',
      email: user?.email || '',
      telephone: user?.telephone || '',
      adresse: user?.adresse || '',
    });
  };

  const handleSave = async () => {
    if (!user?.id) {
      Alert.alert('Erreur', 'Utilisateur introuvable.');
      return;
    }

    setIsSaving(true);
    try {
      const response = await authService.updateProfile(user.id, formData);
      if (response?.user) {
        setUser(response.user);
        setIsEditing(false);
        Alert.alert('Succès', 'Profil mis à jour avec succès.');
      }
    } catch (error) {
      console.error(error);
      Alert.alert('Erreur', 'Impossible de mettre à jour le profil.');
    } finally {
      setIsSaving(false);
    }
  };

  const profileRows = [
    { key: 'email', label: 'Email', icon: 'mail', keyboardType: 'email-address' },
    { key: 'telephone', label: 'Téléphone', icon: 'phone', keyboardType: 'phone-pad' },
    { key: 'adresse', label: 'Adresse', icon: 'map-pin' },
  ];

  return (
    <View style={styles.screen}>
      <ScrollView contentContainerStyle={styles.content} showsVerticalScrollIndicator={false}>
        <View style={styles.headerCard}>
          <View>
            <Text style={styles.heading}>Mon profil</Text>
            <Text style={styles.subHeading}>Espace employé</Text>
          </View>
          <TouchableOpacity style={styles.logoutBtn} onPress={handleLogout} activeOpacity={0.8}>
            <Feather name="power" size={18} color={lightTheme.error} />
          </TouchableOpacity>
        </View>

        <View style={styles.identityCard}>
          {isEditing ? (
            <TextInput
              style={styles.nameInput}
              value={formData.user_name}
              onChangeText={(text) => setFormData((prev) => ({ ...prev, user_name: text }))}
              placeholder="Nom complet"
            />
          ) : (
            <Text style={styles.name}>{user?.user_name || 'Employé'}</Text>
          )}
          <View style={styles.rolePill}>
            <Feather name="briefcase" size={14} color={lightTheme.primary} />
            <Text style={styles.roleText}>Employé</Text>
          </View>
        </View>

        <View style={styles.infoCard}>
          <View style={styles.infoHeaderRow}>
            <Text style={styles.sectionTitle}>Informations personnelles</Text>
            {!isEditing && (
              <TouchableOpacity style={styles.editBtn} onPress={() => setIsEditing(true)}>
                <Feather name="edit-2" size={14} color={lightTheme.primary} />
                <Text style={styles.editBtnText}>Modifier</Text>
              </TouchableOpacity>
            )}
          </View>

          {profileRows.map((item) => (
            <View key={item.key} style={styles.infoRow}>
              <View style={styles.iconWrap}>
                <Feather name={item.icon} size={16} color={lightTheme.primary} />
              </View>
              <View style={styles.infoValueWrap}>
                <Text style={styles.infoLabel}>{item.label}</Text>
                {isEditing ? (
                  <TextInput
                    style={styles.infoInput}
                    value={formData[item.key] || ''}
                    onChangeText={(text) => setFormData((prev) => ({ ...prev, [item.key]: text }))}
                    keyboardType={item.keyboardType || 'default'}
                    placeholder={item.label}
                  />
                ) : (
                  <Text style={styles.infoValue}>{user?.[item.key] || 'Non renseigné'}</Text>
                )}
              </View>
            </View>
          ))}

          {isEditing && (
            <View style={styles.actionsRow}>
              <TouchableOpacity style={[styles.actionBtn, styles.cancelBtn]} onPress={handleCancel}>
                <Text style={styles.cancelBtnText}>Annuler</Text>
              </TouchableOpacity>
              <TouchableOpacity
                style={[styles.actionBtn, styles.saveBtn]}
                onPress={handleSave}
                disabled={isSaving}
              >
                {isSaving ? (
                  <ActivityIndicator size="small" color={lightTheme.white} />
                ) : (
                  <Text style={styles.saveBtnText}>Enregistrer</Text>
                )}
              </TouchableOpacity>
            </View>
          )}
        </View>
      </ScrollView>
    </View>
  );
};

const styles = StyleSheet.create({
  screen: {
    flex: 1,
    backgroundColor:"#FFFFFF",
    marginTop: 34,
  },
  content: {
    paddingHorizontal: 16,
    paddingTop: 18,
    paddingBottom: 24,
    gap: 14,
    
  },
  headerCard: {
    backgroundColor: lightTheme.white,
    borderRadius: 18,
    padding: 16,
    borderWidth: 1,
    borderColor: lightTheme.border,
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  heading: {
    fontSize: 22,
    fontWeight: '700',
    color: lightTheme.textPrimary,
  },
  subHeading: {
    marginTop: 2,
    color: lightTheme.textSecondary,
    fontSize: 13,
  },
  logoutBtn: {
    width: 38,
    height: 38,
    borderRadius: 12,
    borderWidth: 1,
    borderColor: lightTheme.border,
    alignItems: 'center',
    justifyContent: 'center',
    backgroundColor: lightTheme.white,
  },
  identityCard: {
    backgroundColor: lightTheme.white,
    borderRadius: 18,
    borderWidth: 1,
    borderColor: lightTheme.border,
    paddingVertical: 18,
    alignItems: 'center',
  },
  avatar: {
    width: 84,
    height: 84,
    borderRadius: 42,
    borderWidth: 2,
    borderColor: lightTheme.border,
  },
  name: {
    marginTop: 10,
    fontSize: 21,
    fontWeight: '700',
    color: lightTheme.textPrimary,
  },
  nameInput: {
    marginTop: 10,
    minWidth: 180,
    textAlign: 'center',
    borderBottomWidth: 1,
    borderBottomColor: lightTheme.border,
    fontSize: 20,
    fontWeight: '700',
    color: lightTheme.textPrimary,
    paddingVertical: 2,
  },
  rolePill: {
    marginTop: 10,
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
    backgroundColor: lightTheme.bgHighlight,
    borderWidth: 1,
    borderColor: lightTheme.borderHighlight,
    borderRadius: 999,
    paddingHorizontal: 12,
    paddingVertical: 5,
  },
  roleText: {
    color: lightTheme.primary,
    fontWeight: '600',
    fontSize: 13,
  },
  infoCard: {
    backgroundColor: lightTheme.white,
    borderRadius: 18,
    borderWidth: 1,
    borderColor: lightTheme.border,
    padding: 16,
  },
  infoHeaderRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 10,
  },
  sectionTitle: {
    fontSize: 16,
    color: lightTheme.textPrimary,
    fontWeight: '700',
  },
  editBtn: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 5,
    paddingHorizontal: 10,
    paddingVertical: 7,
    borderRadius: 10,
    backgroundColor: lightTheme.bgHighlight,
  },
  editBtnText: {
    fontSize: 13,
    color: lightTheme.primary,
    fontWeight: '600',
  },
  infoRow: {
    flexDirection: 'row',
    gap: 10,
    paddingVertical: 12,
    borderTopWidth: 1,
    borderTopColor: lightTheme.divider,
  },
  iconWrap: {
    width: 28,
    alignItems: 'center',
    paddingTop: 2,
  },
  infoValueWrap: {
    flex: 1,
  },
  infoLabel: {
    fontSize: 12,
    color: lightTheme.textSecondary,
  },
  infoValue: {
    fontSize: 15,
    marginTop: 2,
    color: lightTheme.textPrimary,
    fontWeight: '500',
  },
  infoInput: {
    fontSize: 15,
    color: lightTheme.textPrimary,
    borderBottomWidth: 1,
    borderBottomColor: lightTheme.border,
    paddingVertical: 2,
    marginTop: 2,
  },
  actionsRow: {
    flexDirection: 'row',
    gap: 10,
    marginTop: 16,
  },
  actionBtn: {
    flex: 1,
    borderRadius: 12,
    paddingVertical: 11,
    alignItems: 'center',
    justifyContent: 'center',
  },
  cancelBtn: {
    backgroundColor: lightTheme.inputBackground,
  },
  saveBtn: {
    backgroundColor: lightTheme.primary,
  },
  cancelBtnText: {
    color: lightTheme.textPrimary,
    fontWeight: '600',
  },
  saveBtnText: {
    color: lightTheme.white,
    fontWeight: '700',
  },
});

export default EmployeeProfile;
