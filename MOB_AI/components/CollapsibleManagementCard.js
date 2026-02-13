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

const CollapsibleManagementCard = ({ 
  title, 
  subtitle, 
  status, 
  details = [], 
  onEdit, 
  onDelete, 
  extraActions = [],
  icon = "box",
  iconColor = "#007AFF"
}) => {
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

  return (
    <View style={styles.cardWrapper}>
      <TouchableOpacity 
        style={[styles.container, expanded && styles.containerExpanded]} 
        onPress={toggleExpand}
        activeOpacity={0.9}
      >
        <View style={styles.mainContent}>
          <View style={[styles.iconContainer, { backgroundColor: `${iconColor}15` }]}>
            <Feather name={icon} size={22} color={iconColor} />
          </View>
          
          <View style={styles.infoContainer}>
            <View style={styles.nameRow}>
              <Text style={styles.title} numberOfLines={1}>
                {title || 'Unnamed'}
              </Text>
              {status && (
                <View style={[styles.statusBadge, { backgroundColor: status === 'Active' || status === 'ACTIF' ? '#E3FBE3' : '#FDE8E8' }]}>
                  <Text style={[styles.statusText, { color: status === 'Active' || status === 'ACTIF' ? '#1B811B' : '#C53030' }]}>{status}</Text>
                </View>
              )}
            </View>
            <Text style={styles.subtitle}>{subtitle || 'No details'}</Text>
          </View>

          <View style={styles.actionSection}>
            <Animated.View style={{ transform: [{ rotate: rotateInterpolate }] }}>
              <Feather name="chevron-down" size={20} color="#A0A0A0" />
            </Animated.View>
          </View>
        </View>

        {expanded && (
          <View style={styles.expandedWrapper}>
            <View style={styles.divider} />
            
            <View style={styles.detailsGrid}>
              {details.map((detail, index) => (
                <View key={index} style={styles.detailItem}>
                  <Text style={styles.detailLabel}>{detail.label}</Text>
                  <Text style={styles.detailValue}>{detail.value || 'N/A'}</Text>
                </View>
              ))}
            </View>

            <View style={styles.actionsFooter}>
              {onEdit && (
                <TouchableOpacity style={styles.actionButton} onPress={onEdit}>
                  <Feather name="edit-2" size={18} color="#007AFF" />
                  <Text style={[styles.actionButtonText, { color: '#007AFF' }]}>Update</Text>
                </TouchableOpacity>
              )}
              
              {extraActions.map((action, index) => (
                <TouchableOpacity key={index} style={styles.actionButton} onPress={action.onPress}>
                  <Feather name={action.icon} size={18} color={action.color || "#5856D6"} />
                  <Text style={[styles.actionButtonText, { color: action.color || "#5856D6" }]}>{action.label}</Text>
                </TouchableOpacity>
              ))}

              {onDelete && (
                <TouchableOpacity style={styles.actionButton} onPress={onDelete}>
                  <Feather name="trash-2" size={18} color="#FF3B30" />
                  <Text style={[styles.actionButtonText, { color: '#FF3B30' }]}>Delete</Text>
                </TouchableOpacity>
              )}
            </View>
          </View>
        )}
      </TouchableOpacity>
    </View>
  );
};

const styles = StyleSheet.create({
  cardWrapper: {
    marginHorizontal: 16,
    marginVertical: 8,
    borderRadius: 12,
    ...Platform.select({
      ios: {
        shadowColor: '#000',
        shadowOffset: { width: 0, height: 2 },
        shadowOpacity: 0.1,
        shadowRadius: 4,
      },
      android: {
        elevation: 3,
      },
    }),
  },
  container: {
    backgroundColor: '#FFFFFF',
    borderRadius: 12,
    overflow: 'hidden',
  },
  containerExpanded: {
    paddingBottom: 8,
  },
  mainContent: {
    flexDirection: 'row',
    alignItems: 'center',
    padding: 16,
  },
  iconContainer: {
    width: 44,
    height: 44,
    borderRadius: 22,
    justifyContent: 'center',
    alignItems: 'center',
    marginRight: 12,
  },
  infoContainer: {
    flex: 1,
  },
  nameRow: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 4,
  },
  title: {
    fontSize: 16,
    fontWeight: 'bold',
    color: '#1A1A1A',
    marginRight: 8,
  },
  subtitle: {
    fontSize: 14,
    color: '#666666',
  },
  statusBadge: {
    paddingHorizontal: 8,
    paddingVertical: 2,
    borderRadius: 12,
  },
  statusText: {
    fontSize: 10,
    fontWeight: 'bold',
  },
  actionSection: {
    marginLeft: 8,
  },
  expandedWrapper: {
    paddingHorizontal: 16,
    paddingBottom: 8,
  },
  divider: {
    height: 1,
    backgroundColor: '#F0F0F0',
    marginBottom: 12,
  },
  detailsGrid: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    marginBottom: 16,
  },
  detailItem: {
    width: '50%',
    marginBottom: 12,
  },
  detailLabel: {
    fontSize: 12,
    color: '#8E8E93',
    marginBottom: 2,
  },
  detailValue: {
    fontSize: 14,
    color: '#333333',
    fontWeight: '500',
  },
  actionsFooter: {
    flexDirection: 'row',
    justifyContent: 'space-around',
    borderTopWidth: 1,
    borderTopColor: '#F0F0F0',
    paddingTop: 12,
  },
  actionButton: {
    flexDirection: 'row',
    alignItems: 'center',
    padding: 8,
  },
  actionButtonText: {
    marginLeft: 6,
    fontSize: 14,
    fontWeight: '600',
  },
});

export default CollapsibleManagementCard;
