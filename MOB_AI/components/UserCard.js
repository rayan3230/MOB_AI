import React, { useState, useRef } from 'react';
import { 
  View, 
  Text, 
  StyleSheet, 
  TouchableOpacity, 
  LayoutAnimation, 
  Platform, 
  UIManager,
  Animated,
  Dimensions
} from 'react-native';
import { Feather } from '@expo/vector-icons';
import { lightTheme } from '../constants/theme';

const { width } = Dimensions.get('window');

if (Platform.OS === 'android' && UIManager.setLayoutAnimationEnabledExperimental) {
  UIManager.setLayoutAnimationEnabledExperimental(true);
}

const UserCard = ({ user, currentUserRole, onToggleStatus, onEdit, onDelete }) => {
  const [expanded, setExpanded] = useState(false);
  const animation = useRef(new Animated.Value(0)).current;

  const toggleExpand = () => {
    LayoutAnimation.configureNext(LayoutAnimation.Presets.easeInEaseOut);
    setExpanded(!expanded);
    Animated.timing(animation, {
      toValue: expanded ? 0 : 1,
      duration: 300,
      useNativeDriver: true,
    }).start();
  };

  const rotateInterpolate = animation.interpolate({
    inputRange: [0, 1],
    outputRange: ['0deg', '180deg'],
  });

  const getInitials = (name) => {
    if (!name) return 'U';
    return name.split(' ').map(n => n[0]).join('').toUpperCase().slice(0, 2);
  };

  const getRoleColor = (role) => {
    switch (role?.toUpperCase()) {
      case 'ADMIN': return '#FF9500';
      case 'SUPERVISOR': return '#5856D6';
      default: return '#007AFF';
    }
  };

  const canBan = () => {
    const role = currentUserRole?.toLowerCase();
    const targetRole = user.role?.toLowerCase();

    if (role === 'admin' || role === 'administrator') {
      return targetRole === 'supervisor' || targetRole === 'employee';
    }
    if (role === 'supervisor' || role === 'manager') {
      return targetRole === 'employee';
    }
    return false;
  };

  return (
    <View style={styles.cardWrapper}>
      <TouchableOpacity 
        style={[styles.container, expanded && styles.containerExpanded]} 
        onPress={toggleExpand}
        activeOpacity={0.9}
      >
        {/* Header Section */}
        <View style={styles.mainContent}>
          <View style={styles.infoContainer}>
            <View style={styles.nameRow}>
              <Text style={styles.userName} numberOfLines={1}>
                {user.nom_complet || 'Unnamed User'}
              </Text>
              {user.is_banned && (
                <View style={styles.bannedBadge}>
                  <Text style={styles.bannedBadgeText}>BANNED</Text>
                </View>
              )}
            </View>
            <Text style={styles.userRole}>{user.role || 'No Role'}</Text>
          </View>

          <View style={styles.actionSection}>
            <Animated.View style={{ transform: [{ rotate: rotateInterpolate }] }}>
              <Feather name="chevron-down" size={22} color="#A0A0A0" />
            </Animated.View>
          </View>
        </View>

        {/* Expanded Content */}
        {expanded && (
          <View style={styles.expandedWrapper}>
            <View style={styles.divider} />
            
            <View style={styles.detailsGrid}>
              <View style={styles.detailItem}>
                <View style={styles.detailIconContainer}>
                  <Feather name="mail" size={14} color={lightTheme.primary} />
                </View>
                <View>
                  <Text style={styles.detailLabel}>Email Address</Text>
                  <Text style={styles.detailValue}>{user.email || '—'}</Text>
                </View>
              </View>

              <View style={styles.detailItem}>
                <View style={styles.detailIconContainer}>
                  <Feather name="phone" size={14} color={lightTheme.primary} />
                </View>
                <View>
                  <Text style={styles.detailLabel}>Phone Number</Text>
                  <Text style={styles.detailValue}>{user.telephone || '—'}</Text>
                </View>
              </View>

              <View style={styles.detailItem}>
                <View style={styles.detailIconContainer}>
                  <Feather name="map-pin" size={14} color={lightTheme.primary} />
                </View>
                <View>
                  <Text style={styles.detailLabel}>Address</Text>
                  <Text style={styles.detailValue}>{user.adresse || '—'}</Text>
                </View>
              </View>

              <View style={styles.detailItem}>
                <View style={styles.detailIconContainer}>
                  <Feather name="hash" size={14} color={lightTheme.primary} />
                </View>
                <View>
                  <Text style={styles.detailLabel}>User ID</Text>
                  <Text style={styles.detailValue}>{user.id_utilisateur}</Text>
                </View>
              </View>
            </View>

            <View style={styles.footerActions}>
              <TouchableOpacity 
                style={styles.editButton} 
                onPress={() => onEdit(user)}
              >
                <Feather name="edit-2" size={16} color={lightTheme.primary} />
                <Text style={styles.editButtonText}>Edit</Text>
              </TouchableOpacity>

              {canBan() && (
                <TouchableOpacity 
                  style={[styles.banButton, user.is_banned && styles.unbanButton]} 
                  onPress={() => onToggleStatus(user)}
                >
                  <Feather 
                    name={user.is_banned ? "user-check" : "user-x"} 
                    size={16} 
                    color="#FFF" 
                  />
                </TouchableOpacity>
              )}

              <TouchableOpacity 
                style={styles.deleteButton} 
                onPress={() => onDelete(user)}
              >
                <Feather name="trash-2" size={16} color="#FF3B30" />
              </TouchableOpacity>
            </View>
          </View>
        )}
      </TouchableOpacity>
    </View>
  );
};

const styles = StyleSheet.create({
  cardWrapper: {
    paddingHorizontal: 0,
    backgroundColor: lightTheme.primary,
    paddingVertical: 8,
  },
  container: {
    backgroundColor: lightTheme.primary,
    borderRadius: 20,
    padding: 16,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.05,
    shadowRadius: 10,
    elevation: 4,
    borderWidth: 1,
    borderColor: lightTheme.border,
  },
  containerExpanded: {
    borderColor: lightTheme.border,
    shadowOpacity: 0.1,
    shadowRadius: 15,
  },
  mainContent: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  avatarContainer: {
    position: 'relative',
  },
  avatar: {
    width: 50,
    height: 50,
    borderRadius: 15,
    justifyContent: 'center',
    alignItems: 'center',
  },
  avatarText: {
    color: '#FFF',
    fontSize: 18,
    fontWeight: '800',
  },
  statusDot: {
    position: 'absolute',
    bottom: -2,
    right: -2,
    width: 14,
    height: 14,
    borderRadius: 7,
    borderWidth: 2,
    borderColor: '#FFF',
  },
  infoContainer: {
    flex: 1,
    marginLeft: 15,
  },
  nameRow: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 4,
  },
  userName: {
    fontSize: 17,
    fontWeight: '700',
    color: '#1A1A1A',
    marginRight: 8,
  },
  bannedBadge: {
    backgroundColor: '#FFE5E5',
    paddingHorizontal: 6,
    paddingVertical: 2,
    borderRadius: 6,
  },
  bannedBadgeText: {
    fontSize: 9,
    fontWeight: '900',
    color: '#FF3B30',
  },
  userRole: {
    fontSize: 13,
    color: '#7D7D7D',
    fontWeight: '500',
  },
  actionSection: {
    paddingLeft: 10,
  },
  expandedWrapper: {
    marginTop: 15,
  },
  divider: {
    height: 1,
    backgroundColor: '#F0F0F0',
    marginBottom: 15,
  },
  detailsGrid: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    justifyContent: 'space-between',
  },
  detailItem: {
    width: '48%',
    flexDirection: 'row',
    alignItems: 'flex-start',
    marginBottom: 15,
  },
  detailIconContainer: {
    width: 28,
    height: 28,
    borderRadius: 8,
    backgroundColor: '#F0F9FF',
    justifyContent: 'center',
    alignItems: 'center',
    marginRight: 10,
    marginTop: 2,
  },
  detailLabel: {
    fontSize: 11,
    color: '#999',
    fontWeight: '600',
    textTransform: 'uppercase',
    letterSpacing: 0.5,
  },
  detailValue: {
    fontSize: 13,
    color: '#333',
    fontWeight: '500',
  },
  footerActions: {
    flexDirection: 'row',
    marginTop: 10,
    justifyContent: 'space-between',
    gap: 12,
  },
  editButton: {
    flex: 1,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    backgroundColor: lightTheme.bgHighlight,
    paddingVertical: 12,
    borderRadius: 12,
    borderWidth: 1,
    borderColor: lightTheme.primary + '20',
  },
  editButtonText: {
    marginLeft: 8,
    color: lightTheme.primary,
    fontSize: 14,
    fontWeight: '700',
  },
  banButton: {
    width: 50,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    backgroundColor: '#FF3B30',
    paddingVertical: 12,
    borderRadius: 12,
  },
  deleteButton: {
    width: 50,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    backgroundColor: '#FFE5E5',
    paddingVertical: 12,
    borderRadius: 12,
  },
  unbanButton: {
    backgroundColor: '#34C759',
  },
  banButtonText: {
    marginLeft: 8,
    color: '#FFF',
    fontSize: 14,
    fontWeight: '700',
  },
});

export default UserCard;

